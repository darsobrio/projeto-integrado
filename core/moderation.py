"""Moderação e segurança do Oportunet.

Concentra as regras de denúncia de anúncios, verificação de empresas e os
limites de publicação por conta. Os registros vivem no Firestore nas
coleções ``denuncias`` e ``verificacoes``.
"""

from types import SimpleNamespace

from google.cloud import firestore

from core import db
from core.notificacoes import criar_notificacao
from core.utils import chave_data, formatar_data


# Limites de anúncios ativos por conta.
LIMITE_VAGAS_POR_EMPRESA = 10
LIMITE_IMOVEIS_POR_PROPRIETARIO = 10

MOTIVOS_DENUNCIA = [
    ("falsa", "Anúncio falso ou enganoso"),
    ("golpe", "Suspeita de golpe ou pedido de dinheiro"),
    ("ofensivo", "Conteúdo ofensivo ou inadequado"),
    ("duplicado", "Anúncio duplicado"),
    ("outro", "Outro motivo"),
]

MOTIVOS_DENUNCIA_LABELS = dict(MOTIVOS_DENUNCIA)

# Coleção de destino de cada tipo de anúncio denunciável.
COLECOES_ALVO = {
    "vaga": "vagas",
    "imovel": "imoveis",
}

NOMES_ALVO = {
    "vaga": "Vaga",
    "imovel": "Imóvel",
}


def registrar_denuncia(request, tipo, alvo_id, motivo, detalhes):
    """Grava uma denúncia de anúncio. Devolve True em caso de sucesso."""
    colecao = COLECOES_ALVO.get(tipo)

    if colecao is None or motivo not in MOTIVOS_DENUNCIA_LABELS:
        return False

    db.collection("denuncias").document().set({
        "tipo": tipo,
        "alvo_id": str(alvo_id),
        "motivo": motivo,
        "detalhes": detalhes.strip(),
        "denunciante_id": request.user.pk,
        "denunciante_uid": getattr(request.user, "firebase_uid", None),
        "denunciante_email": request.user.email,
        "status": "aberta",
        "criado_em": firestore.SERVER_TIMESTAMP,
    })

    return True


def converter_denuncia(documento):
    dados = documento.to_dict() or {}
    dados["pk"] = documento.id
    dados["motivo_display"] = MOTIVOS_DENUNCIA_LABELS.get(
        dados.get("motivo"), dados.get("motivo") or "—"
    )
    dados["tipo_display"] = NOMES_ALVO.get(dados.get("tipo"), "Anúncio")
    dados["criado_display"] = formatar_data(dados.get("criado_em"))
    dados["url_alvo"] = _url_alvo(dados.get("tipo"), dados.get("alvo_id"))
    return SimpleNamespace(**dados)


def _url_alvo(tipo, alvo_id):
    if tipo == "vaga":
        return f"/vagas/{alvo_id}/"
    if tipo == "imovel":
        return f"/imoveis/{alvo_id}/"
    return "#"


def listar_denuncias(status="aberta"):
    """Lista denúncias, mais recentes primeiro."""
    denuncias = []

    for documento in db.collection("denuncias").stream():
        item = converter_denuncia(documento)
        if status and getattr(item, "status", "aberta") != status:
            continue
        denuncias.append(item)

    denuncias.sort(key=lambda d: chave_data(d.criado_em), reverse=True)
    return denuncias


def definir_status_denuncia(pk, status):
    documento = db.collection("denuncias").document(str(pk)).get()

    if not documento.exists:
        return False

    documento.reference.update({"status": status})
    return True


def ja_denunciou(uid, tipo, alvo_id):
    """Evita que o mesmo usuário denuncie o mesmo anúncio várias vezes."""
    if not uid:
        return False

    for documento in (
        db.collection("denuncias")
        .where("denunciante_uid", "==", str(uid))
        .stream()
    ):
        dados = documento.to_dict() or {}
        if (
            dados.get("tipo") == tipo
            and str(dados.get("alvo_id")) == str(alvo_id)
            and dados.get("status") != "descartada"
        ):
            return True

    return False


# ---------------------------------------------------------------------------
# Verificação de empresas
# ---------------------------------------------------------------------------

def registrar_solicitacao_verificacao(
    request, documento_url=None, cnpj=None, mensagem=None
):
    """Cria (ou reaproveita) um pedido de verificação da empresa logada."""
    uid = getattr(request.user, "firebase_uid", None)

    if not uid:
        return False

    if solicitacao_pendente(uid):
        return False

    db.collection("verificacoes").document().set({
        "usuario_id": request.user.pk,
        "usuario_uid": uid,
        "email": request.user.email,
        "nome": request.user.nome_completo or request.user.email,
        "tipo_usuario": request.user.tipo_usuario,
        "cnpj": cnpj or getattr(request.user, "cpf", None),
        "mensagem": (mensagem or "").strip(),
        "documento_url": documento_url,
        "status": "pendente",
        "criado_em": firestore.SERVER_TIMESTAMP,
    })

    return True


def solicitacao_pendente(uid):
    for documento in (
        db.collection("verificacoes")
        .where("usuario_uid", "==", str(uid))
        .stream()
    ):
        if (documento.to_dict() or {}).get("status") == "pendente":
            return True

    return False


def converter_solicitacao(documento):
    dados = documento.to_dict() or {}
    dados["pk"] = documento.id
    dados["criado_display"] = formatar_data(dados.get("criado_em"))
    return SimpleNamespace(**dados)


def listar_solicitacoes(status="pendente"):
    solicitacoes = []

    for documento in db.collection("verificacoes").stream():
        item = converter_solicitacao(documento)
        if status and getattr(item, "status", "pendente") != status:
            continue
        solicitacoes.append(item)

    solicitacoes.sort(key=lambda s: chave_data(s.criado_em), reverse=True)
    return solicitacoes


def definir_status_verificacao(pk, aprovada):
    """Aprova ou recusa um pedido de verificação."""
    documento = db.collection("verificacoes").document(str(pk)).get()

    if not documento.exists:
        return False

    dados = documento.to_dict() or {}
    novo_status = "aprovada" if aprovada else "recusada"
    documento.reference.update({"status": novo_status})

    if aprovada:
        usuario_id = dados.get("usuario_id")
        if usuario_id:
            from users.models import CustomUser

            CustomUser.objects.filter(pk=usuario_id).update(verificado=True)

    criar_notificacao(
        dados.get("usuario_uid"),
        "Verificação aprovada" if aprovada else "Verificação recusada",
        (
            "Sua empresa agora está verificada no Oportunet."
            if aprovada
            else (
                "Seu pedido de verificação foi recusado. "
                "Você pode enviar novos documentos pelo seu perfil."
            )
        ),
        "/usuarios/perfil/?aba=conta",
    )

    return True
