"""Notificações in-app do Oportunet.

As notificações ficam na coleção ``notificacoes`` do Firestore, sempre
endereçadas a um usuário pelo seu ``firebase_uid`` (mesmo padrão usado em
``usuarios`` e ``candidaturas``).
"""

from google.cloud import firestore

from core import db


def _aceita_notificacoes(uid):
    """Respeita a preferência ``notificar_site`` do usuário (padrão: ligada)."""
    try:
        documento = db.collection("usuarios").document(str(uid)).get()
    except Exception:
        return True

    if not documento.exists:
        return True

    return (documento.to_dict() or {}).get("notificar_site", True) is not False


def criar_notificacao(uid, titulo, mensagem, link=None):
    """Cria uma notificação in-app para o usuário dono do ``uid``."""
    if not uid:
        return

    if not _aceita_notificacoes(uid):
        return

    db.collection("notificacoes").document().set({
        "usuario_uid": str(uid),
        "titulo": titulo,
        "mensagem": mensagem,
        "link": link or "",
        "lida": False,
        "criado_em": firestore.SERVER_TIMESTAMP,
    })


def notificacoes_do_usuario(uid, limite=None):
    """Notificações do usuário, mais recentes primeiro."""
    if not uid:
        return []

    itens = []

    for documento in (
        db.collection("notificacoes")
        .where("usuario_uid", "==", str(uid))
        .stream()
    ):
        dados = documento.to_dict() or {}
        dados["pk"] = documento.id
        itens.append(dados)

    itens.sort(key=lambda item: str(item.get("criado_em") or ""), reverse=True)

    return itens[:limite] if limite else itens


def contar_nao_lidas(uid):
    """Quantidade de notificações ainda não lidas."""
    if not uid:
        return 0

    return sum(
        1
        for documento in (
            db.collection("notificacoes")
            .where("usuario_uid", "==", str(uid))
            .stream()
        )
        if not (documento.to_dict() or {}).get("lida")
    )


def marcar_lida(uid, notificacao_id):
    """Marca uma notificação como lida (apenas se for do usuário)."""
    if not uid:
        return

    referencia = db.collection("notificacoes").document(str(notificacao_id))
    documento = referencia.get()

    if not documento.exists:
        return

    if str((documento.to_dict() or {}).get("usuario_uid", "")) != str(uid):
        return

    referencia.update({"lida": True})


def marcar_todas_lidas(uid):
    """Marca todas as notificações do usuário como lidas."""
    if not uid:
        return

    for documento in (
        db.collection("notificacoes")
        .where("usuario_uid", "==", str(uid))
        .stream()
    ):
        if not (documento.to_dict() or {}).get("lida"):
            documento.reference.update({"lida": True})
