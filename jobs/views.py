from datetime import date, datetime
from types import SimpleNamespace

from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from google.cloud import firestore

from core import db
from core.auth import login_required
from core.emails import enviar_email
from core.moderation import LIMITE_VAGAS_POR_EMPRESA
from core.notificacoes import criar_notificacao
from core.pagination import paginar
from core.user import (
    obter_perfil,
    obter_perfis,
    obter_usuario,
    obter_usuario_por_identificador,
    obter_usuarios,
)
from core.utils import (
    MODALIDADE_CHOICES,
    MODALIDADE_LABELS,
    STATUS_CANDIDATURA_LABELS,
    STATUS_VAGA_LABELS,
    TIPO_CONTRATO_CHOICES,
    TIPO_CONTRATO_LABELS,
    chave_data,
    formatar_data,
    formatar_moeda,
    numero_decimal,
    numero_inteiro,
    rotulo,
)

STATUS_CANDIDATURA_VALIDOS = {
    "enviada",
    "em_analise",
    "entrevista",
    "aprovado",
    "recusado",
}


def prazo_da_vaga(valor):
    """Converte o campo ``prazo`` (string ISO, date ou datetime) em date."""
    if not valor:
        return None

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    texto = str(valor).strip()
    if not texto:
        return None

    try:
        return datetime.strptime(texto[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def vaga_vencida(dados):
    """Diz se a vaga passou do prazo (data limite anterior a hoje)."""
    prazo = prazo_da_vaga(dados.get("prazo"))
    return prazo is not None and prazo < timezone.localdate()


def converter_vaga(documento):
    dados = documento.to_dict() or {}
    dados["pk"] = documento.id
    dados["id"] = documento.id
    dados["tipo_contrato_display"] = rotulo(
        TIPO_CONTRATO_LABELS, dados.get("tipo_contrato")
    )
    dados["modalidade_display"] = rotulo(
        MODALIDADE_LABELS, dados.get("modalidade")
    )
    dados["status_display"] = rotulo(
        STATUS_VAGA_LABELS, dados.get("status"), "Aberta"
    )
    dados["salario_display"] = formatar_moeda(dados.get("salario"))
    dados["data_publicacao_display"] = formatar_data(
        dados.get("data_publicacao")
    )
    dados["prazo_display"] = formatar_data(dados.get("prazo"))

    dados["vencida"] = vaga_vencida(dados)
    dados["aberta"] = (
        dados.get("status", "aberta") == "aberta" and not dados["vencida"]
    )

    if dados["vencida"]:
        dados["status_display"] = "Encerrada"

    return SimpleNamespace(**dados)


def buscar_candidatura(vaga_id, uid):
    """Verifica se o candidato já se inscreveu na vaga.

    O id do documento é determinístico (vaga_uid), então basta um get
    direto em vez de varrer toda a coleção.
    """
    if not uid:
        return False

    documento = db.collection("candidaturas").document(
        f"{vaga_id}_{uid}"
    ).get()

    return documento.exists


def id_favorito(vaga_id, uid):
    """Id determinístico de um favorito (mesmo padrão das candidaturas)."""
    return f"{vaga_id}_{uid}"


def ids_favoritos(uid):
    """Conjunto com os ids das vagas favoritadas por um candidato."""
    if not uid:
        return set()

    return {
        str((documento.to_dict() or {}).get("vaga_id"))
        for documento in db.collection("favoritos")
        .where("candidato_uid", "==", str(uid))
        .stream()
    }


def e_favorita(vaga_id, uid):
    """Diz se a vaga está entre os favoritos do candidato."""
    if not uid:
        return False

    return (
        db.collection("favoritos")
        .document(id_favorito(vaga_id, uid))
        .get()
        .exists
    )


def destino_seguro(request, padrao):
    """Devolve o parâmetro ``next`` apenas se apontar para o próprio site."""
    destino = request.POST.get("next") or ""
    if destino and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}
    ):
        return destino
    return padrao


def vaga_do_usuario(request, pk):
    """Devolve o documento da vaga se ela pertencer ao usuário logado."""
    documento = db.collection("vagas").document(str(pk)).get()

    if not documento.exists:
        return None

    dados = documento.to_dict() or {}

    if str(dados.get("empresa_id", "")) != str(request.user.pk):
        return None

    return documento


ORDENACOES_VAGAS = {
    "recentes": ("data_publicacao", True),
    "maior_salario": ("salario", True),
    "menor_salario": ("salario", False),
}

ORDENACAO_VAGAS_CHOICES = [
    ("recentes", "Mais recentes"),
    ("maior_salario", "Maior salário"),
    ("menor_salario", "Menor salário"),
]


def jobs_list(request):
    q = request.GET.get("q", "").strip()
    local = request.GET.get("local", "").strip()
    tipo_contrato = request.GET.get("tipo_contrato", "").strip().lower()
    modalidade = request.GET.get("modalidade", "").strip().lower()
    salario_min = numero_decimal(request.GET.get("salario_min"))
    salario_max = numero_decimal(request.GET.get("salario_max"))
    ordem = request.GET.get("ordem", "recentes").strip().lower()

    if ordem not in ORDENACOES_VAGAS:
        ordem = "recentes"

    q_busca = q.lower()
    local_busca = local.lower()

    # Filtros de igualdade direto no Firestore (não precisam de índice composto).
    consulta = db.collection("vagas").where("status", "==", "aberta")

    if tipo_contrato:
        consulta = consulta.where("tipo_contrato", "==", tipo_contrato)

    if modalidade:
        consulta = consulta.where("modalidade", "==", modalidade)

    vagas = []

    for documento in consulta.stream():
        dados = documento.to_dict() or {}

        if vaga_vencida(dados):
            continue

        texto_busca = " ".join([
            str(dados.get("funcao", "")),
            str(dados.get("nome_empresa", "")),
            str(dados.get("descricao", "")),
            str(dados.get("requisitos", "")),
        ]).lower()

        texto_local = " ".join([
            str(dados.get("endereco", "")),
            str(dados.get("funcao", "")),
            str(dados.get("nome_empresa", "")),
        ]).lower()

        if q_busca and q_busca not in texto_busca:
            continue

        if local_busca and local_busca not in texto_local:
            continue

        salario = numero_decimal(dados.get("salario"))

        if salario_min is not None and (
            salario is None or salario < salario_min
        ):
            continue

        if salario_max is not None and (
            salario is None or salario > salario_max
        ):
            continue

        vagas.append(converter_vaga(documento))

    campo, decrescente = ORDENACOES_VAGAS[ordem]

    if campo == "salario":
        vagas.sort(
            key=lambda vaga: numero_decimal(getattr(vaga, "salario", None)) or 0.0,
            reverse=decrescente,
        )
    else:
        vagas.sort(
            key=lambda vaga: chave_data(getattr(vaga, "data_publicacao", None)),
            reverse=decrescente,
        )

    paginacao = paginar(vagas, request, por_pagina=9)

    uid = getattr(request.user, "firebase_uid", None)
    favoritos = ids_favoritos(uid) if request.user.is_authenticated else set()

    return render(request, "jobs_list.html", {
        "vagas": paginacao.itens,
        "paginacao": paginacao,
        "favoritos": favoritos,
        "filtro_q": q,
        "filtro_local": local,
        "filtro_tipo_contrato": tipo_contrato,
        "filtro_modalidade": modalidade,
        "filtro_salario_min": request.GET.get("salario_min", "").strip(),
        "filtro_salario_max": request.GET.get("salario_max", "").strip(),
        "filtro_ordem": ordem,
        "ordenacao_choices": ORDENACAO_VAGAS_CHOICES,
        "tipo_contrato_choices": TIPO_CONTRATO_CHOICES,
        "modalidade_choices": MODALIDADE_CHOICES,
    })


def job_detail(request, pk):
    documento = db.collection("vagas").document(str(pk)).get()

    if not documento.exists:
        messages.error(request, "Essa vaga não foi encontrada.")
        return redirect("jobs:list")

    vaga = converter_vaga(documento)
    tipo_usuario = getattr(request.user, "tipo_usuario", None)
    uid = getattr(request.user, "firebase_uid", None)
    ja_candidatou = False
    sou_dono = False
    favoritado = False
    empresa_verificada = False
    empresa = None

    empresa = obter_usuario_por_identificador(getattr(vaga, "empresa_id", None))

    if empresa is not None:
        empresa_verificada = bool(empresa.verificado)

    if request.user.is_authenticated:
        sou_dono = str(getattr(vaga, "empresa_id", "")) == str(
            request.user.pk
        )

    if tipo_usuario == "candidato":
        ja_candidatou = buscar_candidatura(vaga.pk, uid)
        favoritado = e_favorita(vaga.pk, uid)

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.info(request, "Entre na sua conta para se candidatar.")
            destino = reverse("jobs:detail", kwargs={"pk": vaga.pk})
            return redirect(f"{reverse('core:login')}?next={destino}")

        if tipo_usuario != "candidato" or ja_candidatou:
            return redirect("jobs:detail", pk=vaga.pk)

        if not uid:
            messages.error(
                request,
                "Sua conta não está vinculada ao Firebase. "
                "Entre novamente na sua conta.",
            )
            return redirect("jobs:detail", pk=vaga.pk)

        db.collection("candidaturas").document(f"{vaga.pk}_{uid}").set({
            "vaga_id": vaga.pk,
            "candidato_id": request.user.pk,
            "candidato_uid": uid,
            "data_envio": firestore.SERVER_TIMESTAMP,
            "status_candidatura": "enviada",
            "observacoes": "",
        })

        empresa_dona = obter_usuario_por_identificador(
            getattr(vaga, "empresa_id", None)
        )

        if empresa_dona is not None and empresa_dona.firebase_uid:
            criar_notificacao(
                empresa_dona.firebase_uid,
                "Nova candidatura recebida",
                (
                    f"{request.user.nome_completo or 'Um candidato'} se "
                    f"candidatou para a vaga de {vaga.funcao}."
                ),
                reverse("jobs:candidaturas"),
            )

        messages.success(request, "Candidatura enviada com sucesso! Boa sorte 🤞")
        return redirect("jobs:detail", pk=vaga.pk)

    # Vagas semelhantes: mesma modalidade/tipo de contrato ganham prioridade.
    candidatas = []

    for documento_similar in (
        db.collection("vagas").where("status", "==", "aberta").limit(40).stream()
    ):
        if documento_similar.id == vaga.pk:
            continue

        similar = converter_vaga(documento_similar)

        if similar.vencida:
            continue

        pontuacao = 0

        if getattr(similar, "tipo_contrato", None) == getattr(vaga, "tipo_contrato", None):
            pontuacao += 2

        if getattr(similar, "modalidade", None) == getattr(vaga, "modalidade", None):
            pontuacao += 1

        candidatas.append((pontuacao, similar))

    candidatas.sort(key=lambda item: item[0], reverse=True)
    vagas_similares = [item[1] for item in candidatas[:3]]

    return render(request, "job_detail.html", {
        "vaga": vaga,
        "ja_candidatou": ja_candidatou,
        "sou_dono": sou_dono,
        "favoritado": favoritado,
        "empresa_verificada": empresa_verificada,
        "empresa": empresa,
        "vagas_similares": vagas_similares,
    })


@login_required
def job_create(request):
    """Publica uma nova vaga no Firestore (apenas empresas)."""
    if request.user.tipo_usuario != "empresa":
        messages.error(request, "Apenas contas de empresa podem publicar vagas.")
        return redirect("core:dashboard")

    publicadas = db.collection("vagas").where(
        "empresa_id", "==", str(request.user.pk)
    ).stream()
    total_publicadas = sum(1 for _ in publicadas)

    if total_publicadas >= LIMITE_VAGAS_POR_EMPRESA:
        messages.error(
            request,
            f"Você atingiu o limite de {LIMITE_VAGAS_POR_EMPRESA} vagas "
            "publicadas por conta. Exclua ou feche uma vaga para publicar outra.",
        )
        return redirect("core:dashboard")

    if request.method == "POST":
        funcao = request.POST.get("funcao", "").strip()
        descricao = request.POST.get("descricao", "").strip()
        requisitos = request.POST.get("requisitos", "").strip()

        if not (funcao and descricao and requisitos):
            messages.error(
                request,
                "Preencha os campos obrigatórios: função, descrição e requisitos.",
            )
        else:
            referencia = db.collection("vagas").document()
            dados_vaga = {
                "empresa_id": str(request.user.pk),
                "empresa_uid": getattr(request.user, "firebase_uid", None),
                "nome_empresa": (
                    request.POST.get("nome_empresa", "").strip()
                    or request.user.nome_completo
                    or request.user.email
                ),
                "cnpj": request.POST.get("cnpj", "").strip(),
                "endereco": request.POST.get("endereco", "").strip(),
                "funcao": funcao,
                "descricao": descricao,
                "requisitos": requisitos,
                "beneficios": request.POST.get("beneficios", "").strip(),
                "horario": request.POST.get("horario", "").strip(),
                "salario": numero_decimal(request.POST.get("salario")),
                "tipo_contrato": request.POST.get("tipo_contrato", "clt"),
                "modalidade": request.POST.get("modalidade", "presencial"),
                "qtd_vagas": numero_inteiro(request.POST.get("qtd_vagas"), 1),
                "prazo": request.POST.get("prazo", "").strip(),
                "status": "aberta",
                "data_publicacao": firestore.SERVER_TIMESTAMP,
            }
            referencia.set(dados_vaga)
            notificar_alertas(dados_vaga)
            messages.success(request, "Vaga publicada com sucesso!")
            return redirect("jobs:detail", pk=referencia.id)

    return render(request, "job_form.html", {
        "tipo_contrato_choices": TIPO_CONTRATO_CHOICES,
        "modalidade_choices": MODALIDADE_CHOICES,
    })


@login_required
def job_edit(request, pk):
    """Edita uma vaga existente (apenas a empresa responsável)."""
    if request.user.tipo_usuario != "empresa":
        messages.error(request, "Apenas contas de empresa podem editar vagas.")
        return redirect("core:dashboard")

    documento = vaga_do_usuario(request, pk)

    if documento is None:
        messages.error(request, "Vaga não encontrada ou sem permissão de acesso.")
        return redirect("core:dashboard")

    if request.method == "POST":
        funcao = request.POST.get("funcao", "").strip()
        descricao = request.POST.get("descricao", "").strip()
        requisitos = request.POST.get("requisitos", "").strip()

        if not (funcao and descricao and requisitos):
            messages.error(
                request,
                "Preencha os campos obrigatórios: função, descrição e requisitos.",
            )
        else:
            documento.reference.update({
                "nome_empresa": (
                    request.POST.get("nome_empresa", "").strip()
                    or request.user.nome_completo
                    or request.user.email
                ),
                "cnpj": request.POST.get("cnpj", "").strip(),
                "endereco": request.POST.get("endereco", "").strip(),
                "funcao": funcao,
                "descricao": descricao,
                "requisitos": requisitos,
                "beneficios": request.POST.get("beneficios", "").strip(),
                "horario": request.POST.get("horario", "").strip(),
                "salario": numero_decimal(request.POST.get("salario")),
                "tipo_contrato": request.POST.get("tipo_contrato", "clt"),
                "modalidade": request.POST.get("modalidade", "presencial"),
                "qtd_vagas": numero_inteiro(request.POST.get("qtd_vagas"), 1),
                "prazo": request.POST.get("prazo", "").strip(),
            })
            messages.success(request, "Vaga atualizada com sucesso!")
            return redirect("jobs:detail", pk=pk)

    vaga = converter_vaga(documento)

    return render(request, "job_form.html", {
        "vaga": vaga,
        "modo_edicao": True,
        "tipo_contrato_choices": TIPO_CONTRATO_CHOICES,
        "modalidade_choices": MODALIDADE_CHOICES,
    })


@login_required
def job_toggle_status(request, pk):
    """Abre ou fecha uma vaga (apenas a empresa responsável)."""
    if request.method != "POST":
        return redirect("core:dashboard")

    documento = vaga_do_usuario(request, pk)

    if documento is None:
        messages.error(request, "Vaga não encontrada ou sem permissão de acesso.")
        return redirect("core:dashboard")

    atual = (documento.to_dict() or {}).get("status", "aberta")
    novo = "fechada" if atual == "aberta" else "aberta"
    documento.reference.update({"status": novo})

    messages.success(
        request,
        "Vaga fechada. Ela deixará de aparecer nas buscas."
        if novo == "fechada"
        else "Vaga reaberta com sucesso!",
    )
    return redirect("core:dashboard")


@login_required
def job_delete(request, pk):
    """Exclui uma vaga e suas candidaturas (apenas a empresa responsável)."""
    if request.method != "POST":
        return redirect("core:dashboard")

    documento = vaga_do_usuario(request, pk)

    if documento is None:
        messages.error(request, "Vaga não encontrada ou sem permissão de acesso.")
        return redirect("core:dashboard")

    for candidatura in (
        db.collection("candidaturas")
        .where("vaga_id", "==", str(pk))
        .stream()
    ):
        candidatura.reference.delete()

    documento.reference.delete()
    messages.success(request, "Vaga excluída com sucesso.")
    return redirect("core:dashboard")


def buscar_email_candidato(candidatura):
    """Descobre o e-mail do candidato a partir da candidatura.

    Tenta o banco local (SQLite) primeiro e, se não achar, consulta o
    documento espelho no Firestore.
    """
    uid = str(candidatura.get("candidato_uid") or "")
    candidato_id = candidatura.get("candidato_id")

    usuario = None

    if uid:
        usuario = obter_usuario(uid)

    if usuario is None and candidato_id:
        usuario = obter_usuario_por_identificador(candidato_id)

    if usuario is not None and usuario.email:
        return usuario.email

    if uid:
        documento = db.collection("usuarios").document(uid).get()
        if documento.exists:
            return (documento.to_dict() or {}).get("email")

    return None


def notificar_mudanca_status(candidatura, vaga, novo_status):
    """Avisa o candidato, por e-mail, que o status da candidatura mudou."""
    destinatario = buscar_email_candidato(candidatura)

    if not destinatario:
        return

    funcao = vaga.get("funcao") or "a vaga"
    empresa = vaga.get("nome_empresa") or "A empresa"
    rotulo_status = rotulo(STATUS_CANDIDATURA_LABELS, novo_status, novo_status)

    enviar_email(
        destinatario,
        f"Oportunet — sua candidatura para {funcao} foi atualizada",
        (
            f"Olá!\n\n"
            f"Sua candidatura para a vaga de {funcao} em {empresa} "
            f"teve o status atualizado para: {rotulo_status}.\n\n"
            "Acesse o seu painel no Oportunet para ver os detalhes.\n\n"
            "Boa sorte!\n"
            "Equipe Oportunet"
        ),
    )


@login_required
def candidatura_status(request, pk):
    """Atualiza o status de uma candidatura recebida (apenas a empresa)."""
    destino = destino_seguro(request, reverse("core:dashboard"))

    if request.user.tipo_usuario != "empresa":
        messages.error(
            request, "Apenas contas de empresa podem gerenciar candidaturas."
        )
        return redirect(destino)

    if request.method != "POST":
        return redirect(destino)

    novo_status = request.POST.get("status", "").strip()

    if novo_status not in STATUS_CANDIDATURA_VALIDOS:
        messages.error(request, "Status de candidatura inválido.")
        return redirect(destino)

    documento = db.collection("candidaturas").document(str(pk)).get()

    if not documento.exists:
        messages.error(request, "Candidatura não encontrada.")
        return redirect(destino)

    dados = documento.to_dict() or {}
    vaga = db.collection("vagas").document(
        str(dados.get("vaga_id", ""))
    ).get()

    if not vaga.exists or str(
        (vaga.to_dict() or {}).get("empresa_id", "")
    ) != str(request.user.pk):
        messages.error(
            request, "Você não tem permissão para alterar esta candidatura."
        )
        return redirect(destino)

    status_atual = dados.get("status_candidatura", "")

    documento.reference.update({"status_candidatura": novo_status})

    if status_atual != novo_status:
        dados_vaga = vaga.to_dict() or {}
        notificar_mudanca_status(dados, dados_vaga, novo_status)
        criar_notificacao(
            dados.get("candidato_uid"),
            "Status da candidatura atualizado",
            (
                f"Sua candidatura para "
                f"{dados_vaga.get('funcao') or 'a vaga'} agora está como "
                f"{rotulo(STATUS_CANDIDATURA_LABELS, novo_status, novo_status)}."
            ),
            reverse("jobs:minhas_candidaturas"),
        )

    messages.success(request, "Status da candidatura atualizado.")
    return redirect(destino)


# ---------------------------------------------------------------------------
# Recrutamento — pipeline e histórico de candidaturas
# ---------------------------------------------------------------------------

PIPELINE_STATUS = ["enviada", "em_analise", "entrevista", "aprovado", "recusado"]


def mapa_candidatos(uids):
    """Reúne dados de exibição dos candidatos (nome, foto, currículo).

    Faz duas leituras no total (usuários e perfis), evitando uma consulta por
    candidatura.
    """
    uids = {str(uid) for uid in uids if uid}

    if not uids:
        return {}

    usuarios = obter_usuarios(uids)
    perfis = obter_perfis(uids)

    resultado = {}

    for uid in uids:
        usuario = usuarios.get(uid)
        perfil = perfis.get(uid)

        resultado[uid] = SimpleNamespace(
            uid=uid,
            nome=(
                (usuario.nome_completo if usuario else None)
                or (usuario.email if usuario else None)
                or "Candidato"
            ),
            cidade=(usuario.cidade if usuario else "") or "",
            foto_url=(
                usuario.foto_perfil.url
                if usuario and usuario.foto_perfil
                else None
            ),
            curriculo_url=(
                perfil.curriculo_pdf.url
                if perfil and perfil.curriculo_pdf
                else None
            ),
            perfil_url=reverse("users:candidato_detalhe", kwargs={"uid": uid}),
        )

    return resultado


def candidaturas_das_vagas(vagas):
    """Carrega as candidaturas referentes a um conjunto de vagas."""
    candidaturas = []

    for documento in db.collection("candidaturas").stream():
        dados = documento.to_dict() or {}
        vaga_id = str(dados.get("vaga_id", ""))

        if vaga_id not in vagas:
            continue

        candidaturas.append(
            SimpleNamespace(
                pk=documento.id,
                vaga_id=vaga_id,
                candidato_uid=str(dados.get("candidato_uid") or ""),
                status_candidatura=dados.get("status_candidatura") or "enviada",
                status_display=rotulo(
                    STATUS_CANDIDATURA_LABELS,
                    dados.get("status_candidatura") or "enviada",
                    "Enviada",
                ),
                data_envio=dados.get("data_envio"),
                data_display=formatar_data(dados.get("data_envio")),
                mensagem=dados.get("mensagem") or "",
                vaga=vagas[vaga_id],
            )
        )

    candidaturas.sort(
        key=lambda item: chave_data(item.data_envio), reverse=True
    )
    return candidaturas


@login_required
def candidaturas_recebidas(request):
    """Pipeline (kanban) das candidaturas recebidas pela empresa."""
    if request.user.tipo_usuario != "empresa":
        messages.error(
            request, "Apenas contas de empresa podem ver candidaturas recebidas."
        )
        return redirect("core:dashboard")

    minhas_vagas = {}

    for documento in db.collection("vagas").stream():
        dados = documento.to_dict() or {}

        if str(dados.get("empresa_id", "")) != str(request.user.pk):
            continue

        minhas_vagas[documento.id] = converter_vaga(documento)

    vaga_filtro = request.GET.get("vaga", "").strip()

    candidaturas = candidaturas_das_vagas(minhas_vagas)

    if vaga_filtro:
        candidaturas = [
            item for item in candidaturas if item.vaga_id == vaga_filtro
        ]

    candidatos = mapa_candidatos(
        {candidatura.candidato_uid for candidatura in candidaturas}
    )

    for candidatura in candidaturas:
        candidatura.candidato = candidatos.get(candidatura.candidato_uid)

    colunas = [
        {
            "status": status,
            "rotulo": STATUS_CANDIDATURA_LABELS.get(status, status),
            "itens": [
                item for item in candidaturas
                if item.status_candidatura == status
            ],
        }
        for status in PIPELINE_STATUS
    ]

    return render(request, "jobs_candidaturas.html", {
        "colunas": colunas,
        "vagas": sorted(
            minhas_vagas.values(), key=lambda vaga: str(vaga.funcao or "")
        ),
        "vaga_filtro": vaga_filtro,
        "total": len(candidaturas),
        "status_opcoes": list(STATUS_CANDIDATURA_LABELS.items()),
    })


@login_required
def minhas_candidaturas(request):
    """Histórico das candidaturas enviadas pelo candidato."""
    if request.user.tipo_usuario != "candidato":
        messages.error(
            request, "Apenas candidatos possuem candidaturas enviadas."
        )
        return redirect("core:dashboard")

    uid = getattr(request.user, "firebase_uid", None)
    status_filtro = request.GET.get("status", "").strip()

    todas = []

    for documento in db.collection("candidaturas").stream():
        dados = documento.to_dict() or {}
        candidato_uid = str(dados.get("candidato_uid") or "")
        candidato_id = str(dados.get("candidato_id") or "")

        pertence = (
            (uid and candidato_uid == str(uid))
            or candidato_id == str(request.user.pk)
        )

        if not pertence:
            continue

        vaga_documento = db.collection("vagas").document(
            str(dados.get("vaga_id", ""))
        ).get()
        vaga = (
            converter_vaga(vaga_documento)
            if vaga_documento.exists
            else None
        )

        status = dados.get("status_candidatura") or "enviada"

        todas.append(
            SimpleNamespace(
                pk=documento.id,
                vaga_id=str(dados.get("vaga_id", "")),
                vaga=vaga,
                status_candidatura=status,
                status_display=rotulo(
                    STATUS_CANDIDATURA_LABELS, status, "Enviada"
                ),
                data_envio=dados.get("data_envio"),
                data_display=formatar_data(dados.get("data_envio")),
            )
        )

    todas.sort(key=lambda item: chave_data(item.data_envio), reverse=True)

    candidaturas = [
        item for item in todas
        if not status_filtro or item.status_candidatura == status_filtro
    ]

    contagens = {
        status: sum(
            1 for item in todas if item.status_candidatura == status
        )
        for status in PIPELINE_STATUS
    }

    return render(request, "jobs_minhas_candidaturas.html", {
        "candidaturas": candidaturas,
        "status_opcoes": list(STATUS_CANDIDATURA_LABELS.items()),
        "status_filtro": status_filtro,
        "contagens": contagens,
        "total": len(todas),
    })


# ---------------------------------------------------------------------------
# Favoritos
# ---------------------------------------------------------------------------

@login_required
def favoritar(request, pk):
    """Adiciona ou remove uma vaga dos favoritos do candidato (POST)."""
    destino = destino_seguro(request, reverse("jobs:detail", kwargs={"pk": pk}))

    if request.method != "POST":
        return redirect(destino)

    if request.user.tipo_usuario != "candidato":
        messages.error(request, "Apenas candidatos podem favoritar vagas.")
        return redirect(destino)

    uid = getattr(request.user, "firebase_uid", None)

    if not uid:
        messages.error(
            request,
            "Sua conta não está vinculada ao Firebase. Entre novamente.",
        )
        return redirect(destino)

    documento = db.collection("favoritos").document(id_favorito(pk, uid))

    if documento.get().exists:
        documento.delete()
        messages.info(request, "Vaga removida dos favoritos.")
    else:
        documento.set({
            "vaga_id": str(pk),
            "candidato_id": request.user.pk,
            "candidato_uid": uid,
            "criado_em": firestore.SERVER_TIMESTAMP,
        })
        messages.success(request, "Vaga salva nos favoritos.")

    return redirect(destino)


@login_required
def favoritos(request):
    """Lista as vagas favoritadas pelo candidato logado."""
    uid = getattr(request.user, "firebase_uid", None)
    vagas = []

    for vaga_id in ids_favoritos(uid):
        documento = db.collection("vagas").document(vaga_id).get()
        if documento.exists:
            vagas.append(converter_vaga(documento))

    vagas.sort(
        key=lambda vaga: chave_data(getattr(vaga, "data_publicacao", None)),
        reverse=True,
    )

    return render(request, "jobs_favoritos.html", {"vagas": vagas})


# ---------------------------------------------------------------------------
# Alertas de vagas por filtro salvo
# ---------------------------------------------------------------------------

CAMPOS_ALERTA = ("q", "local", "tipo_contrato", "modalidade")


def alertas_do_candidato(uid):
    """Lista os alertas salvos por um candidato."""
    if not uid:
        return []

    alertas = []

    for documento in (
        db.collection("alertas")
        .where("candidato_uid", "==", str(uid))
        .stream()
    ):
        dados = documento.to_dict() or {}
        dados["pk"] = documento.id
        alertas.append(SimpleNamespace(**dados))

    return alertas


def descrever_alerta(alerta):
    """Monta um resumo legível dos filtros de um alerta."""
    partes = []

    if getattr(alerta, "q", ""):
        partes.append(f'"{alerta.q}"')
    if getattr(alerta, "local", ""):
        partes.append(f'em {alerta.local}')
    if getattr(alerta, "tipo_contrato", ""):
        partes.append(rotulo(TIPO_CONTRATO_LABELS, alerta.tipo_contrato))
    if getattr(alerta, "modalidade", ""):
        partes.append(rotulo(MODALIDADE_LABELS, alerta.modalidade))

    return " · ".join(partes) or "Todas as vagas"


def vaga_casa_com_alerta(vaga, alerta):
    """Confere se uma vaga atende aos filtros salvos em um alerta."""
    tipo = (getattr(alerta, "tipo_contrato", "") or "").lower()
    modalidade = (getattr(alerta, "modalidade", "") or "").lower()
    q = (getattr(alerta, "q", "") or "").lower()
    local = (getattr(alerta, "local", "") or "").lower()

    if tipo and str(vaga.get("tipo_contrato") or "").lower() != tipo:
        return False

    if modalidade and str(vaga.get("modalidade") or "").lower() != modalidade:
        return False

    if q:
        texto = " ".join([
            str(vaga.get("funcao", "")),
            str(vaga.get("nome_empresa", "")),
            str(vaga.get("descricao", "")),
            str(vaga.get("requisitos", "")),
        ]).lower()
        if q not in texto:
            return False

    if local:
        texto_local = " ".join([
            str(vaga.get("endereco", "")),
            str(vaga.get("funcao", "")),
            str(vaga.get("nome_empresa", "")),
        ]).lower()
        if local not in texto_local:
            return False

    return True


def notificar_alertas(vaga):
    """Avisa por e-mail quem tem um alerta que casa com a vaga publicada."""
    try:
        alertas = list(db.collection("alertas").stream())
    except Exception:
        return

    for documento in alertas:
        alerta = SimpleNamespace(**(documento.to_dict() or {}))

        if not vaga_casa_com_alerta(vaga, alerta):
            continue

        destinatario = getattr(alerta, "email", None)

        if not destinatario:
            continue

        funcao = vaga.get("funcao") or "Nova vaga"
        empresa = vaga.get("nome_empresa") or "Empresa"

        enviar_email(
            destinatario,
            f"Oportunet — nova vaga: {funcao}",
            (
                f"Olá!\n\n"
                f"Apareceu uma vaga que combina com o seu alerta:\n\n"
                f"• {funcao}\n"
                f"• {empresa}\n"
                f"• {vaga.get('endereco') or 'Paulistana - PI'}\n\n"
                "Acesse o Oportunet para ver os detalhes e se candidatar.\n\n"
                "Boa sorte!\n"
                "Equipe Oportunet"
            ),
        )


@login_required
def alertas(request):
    """Cria e lista alertas de vagas por filtro salvo (apenas candidato)."""
    if request.user.tipo_usuario != "candidato":
        messages.error(
            request, "Apenas candidatos podem criar alertas de vagas."
        )
        return redirect("core:dashboard")

    uid = getattr(request.user, "firebase_uid", None)

    if request.method == "POST":
        if not uid:
            messages.error(
                request,
                "Sua conta não está vinculada ao Firebase. Entre novamente.",
            )
            return redirect("jobs:alertas")

        filtros = {
            campo: request.POST.get(campo, "").strip().lower()
            if campo in ("tipo_contrato", "modalidade")
            else request.POST.get(campo, "").strip()
            for campo in CAMPOS_ALERTA
        }

        if not any(filtros.values()):
            messages.error(request, "Informe pelo menos um filtro para o alerta.")
        else:
            db.collection("alertas").document().set({
                **filtros,
                "candidato_id": request.user.pk,
                "candidato_uid": uid,
                "email": request.user.email,
                "criado_em": firestore.SERVER_TIMESTAMP,
            })
            messages.success(
                request,
                "Alerta criado! Você será avisado por e-mail quando surgir "
                "uma vaga com esse perfil.",
            )

        return redirect("jobs:alertas")

    meus_alertas = [
        {"pk": alerta.pk, "descricao": descrever_alerta(alerta)}
        for alerta in alertas_do_candidato(uid)
    ]

    return render(request, "jobs_alerts.html", {
        "alertas": meus_alertas,
        "tipo_contrato_choices": TIPO_CONTRATO_CHOICES,
        "modalidade_choices": MODALIDADE_CHOICES,
    })


@login_required
def alerta_remover(request, pk):
    """Remove um alerta salvo (apenas o dono)."""
    if request.method != "POST":
        return redirect("jobs:alertas")

    uid = str(getattr(request.user, "firebase_uid", "") or "")
    documento = db.collection("alertas").document(str(pk)).get()

    if not documento.exists or str(
        (documento.to_dict() or {}).get("candidato_uid")
    ) != uid:
        messages.error(request, "Alerta não encontrado.")
        return redirect("jobs:alertas")

    documento.reference.delete()
    messages.success(request, "Alerta removido.")
    return redirect("jobs:alertas")


# ---------------------------------------------------------------------------
# Mensagens entre empresa e candidato
# ---------------------------------------------------------------------------

def id_conversa(vaga_id, candidato_uid):
    """Id determinístico de uma conversa (vaga + candidato)."""
    return f"{vaga_id}_{candidato_uid}"


def email_do_usuario(uid=None, pk=None):
    """Descobre o e-mail de um usuário pelo uid do Firebase ou pelo id local."""
    usuario = None

    if uid:
        usuario = obter_usuario(uid)

    if usuario is None and pk:
        usuario = obter_usuario_por_identificador(pk)

    if usuario is not None and usuario.email:
        return usuario.email

    if uid:
        documento = db.collection("usuarios").document(str(uid)).get()
        if documento.exists:
            return (documento.to_dict() or {}).get("email")

    return None


def nome_do_candidato(uid):
    """Nome exibível do candidato a partir do uid do Firebase."""
    if not uid:
        return "Candidato"

    usuario = obter_usuario(uid)

    if usuario is not None and usuario.nome_completo:
        return usuario.nome_completo

    documento = db.collection("usuarios").document(str(uid)).get()

    if documento.exists:
        return (documento.to_dict() or {}).get("nome_completo") or "Candidato"

    return "Candidato"


def mensagens_da_conversa(vaga_id, candidato_uid):
    """Carrega as mensagens de uma conversa em ordem cronológica."""
    mensagens = []

    for documento in (
        db.collection("mensagens")
        .where("conversa_id", "==", id_conversa(vaga_id, candidato_uid))
        .stream()
    ):
        dados = documento.to_dict() or {}
        dados["pk"] = documento.id
        mensagens.append(SimpleNamespace(**dados))

    mensagens.sort(key=lambda m: chave_data(getattr(m, "criado_em", None)))
    return mensagens


@login_required
def mensagens(request):
    """Lista as conversas do usuário (empresa ou candidato)."""
    usuario = request.user
    uid = str(getattr(usuario, "firebase_uid", "") or "")

    if usuario.tipo_usuario == "empresa":
        consulta = db.collection("mensagens").where(
            "empresa_id", "==", str(usuario.pk)
        )
    elif uid:
        consulta = db.collection("mensagens").where("candidato_uid", "==", uid)
    else:
        return render(request, "jobs_mensagens.html", {"conversas": []})

    agrupado = {}

    for documento in consulta.stream():
        dados = documento.to_dict() or {}
        chave = dados.get("conversa_id")

        if not chave:
            continue

        item = agrupado.setdefault(chave, {
            "conversa_id": chave,
            "vaga_id": dados.get("vaga_id"),
            "candidato_uid": dados.get("candidato_uid"),
            "total": 0,
            "ultima": "",
            "ultima_chave": 0,
        })

        item["total"] += 1
        momento = chave_data(dados.get("criado_em"))

        if momento >= item["ultima_chave"]:
            item["ultima_chave"] = momento
            item["ultima"] = (dados.get("texto") or "Currículo enviado")[:90]

    conversas = []

    for item in agrupado.values():
        documento_vaga = db.collection("vagas").document(
            str(item["vaga_id"])
        ).get()
        dados_vaga = documento_vaga.to_dict() if documento_vaga.exists else {}

        item["vaga_funcao"] = dados_vaga.get("funcao") or "Vaga"

        if usuario.tipo_usuario == "empresa":
            item["participante"] = nome_do_candidato(item["candidato_uid"])
        else:
            item["participante"] = dados_vaga.get("nome_empresa") or "Empresa"

        conversas.append(item)

    conversas.sort(key=lambda c: c["ultima_chave"], reverse=True)

    return render(request, "jobs_mensagens.html", {"conversas": conversas})


@login_required
def conversa(request, vaga_id, candidato_uid):
    """Exibe e permite responder a conversa entre empresa e candidato."""
    documento_vaga = db.collection("vagas").document(str(vaga_id)).get()

    if not documento_vaga.exists:
        messages.error(request, "Vaga não encontrada.")
        return redirect("jobs:mensagens")

    dados_vaga = documento_vaga.to_dict() or {}
    empresa_id = str(dados_vaga.get("empresa_id", ""))
    uid = str(getattr(request.user, "firebase_uid", "") or "")
    sou_empresa = str(request.user.pk) == empresa_id

    if not sou_empresa and uid != str(candidato_uid):
        messages.error(request, "Você não tem acesso a esta conversa.")
        return redirect("core:dashboard")

    if request.method == "POST":
        texto = request.POST.get("texto", "").strip()
        anexar = request.POST.get("anexar_curriculo") == "on"
        curriculo_url = None

        if anexar and not sou_empresa:
            perfil = obter_perfil(request.user.firebase_uid)

            if perfil is not None and perfil.curriculo_pdf:
                curriculo_url = perfil.curriculo_pdf.url
            else:
                messages.info(
                    request,
                    "Você ainda não enviou um currículo no seu perfil.",
                )

        if not texto and not curriculo_url:
            messages.error(request, "Escreva uma mensagem para enviar.")
        else:
            candidato = obter_usuario(str(candidato_uid))

            db.collection("mensagens").document().set({
                "conversa_id": id_conversa(vaga_id, candidato_uid),
                "vaga_id": str(vaga_id),
                "candidato_id": candidato.pk if candidato else None,
                "candidato_uid": str(candidato_uid),
                "empresa_id": empresa_id,
                "remetente_id": request.user.pk,
                "remetente_tipo": "empresa" if sou_empresa else "candidato",
                "texto": texto,
                "curriculo_url": curriculo_url,
                "criado_em": firestore.SERVER_TIMESTAMP,
            })

            destino = (
                email_do_usuario(uid=candidato_uid)
                if sou_empresa
                else email_do_usuario(pk=empresa_id)
            )

            if destino:
                funcao = dados_vaga.get("funcao") or "a vaga"
                enviar_email(
                    destino,
                    f"Oportunet — nova mensagem sobre {funcao}",
                    (
                        "Olá!\n\n"
                        f"Você recebeu uma nova mensagem sobre a vaga de "
                        f"{funcao}.\n\n"
                        f'"{texto or "Currículo enviado"}"\n\n'
                        "Acesse o Oportunet para responder.\n\n"
                        "Equipe Oportunet"
                    ),
                )

            messages.success(request, "Mensagem enviada.")

            funcao_conversa = dados_vaga.get("funcao") or "a vaga"

            if sou_empresa:
                criar_notificacao(
                    candidato_uid,
                    "Nova mensagem recebida",
                    f"Você recebeu uma mensagem sobre a vaga de {funcao_conversa}.",
                    reverse(
                        "jobs:conversa",
                        kwargs={
                            "vaga_id": vaga_id,
                            "candidato_uid": candidato_uid,
                        },
                    ),
                )
            else:
                empresa_usuario = obter_usuario_por_identificador(empresa_id)

                if empresa_usuario is not None and empresa_usuario.firebase_uid:
                    criar_notificacao(
                        empresa_usuario.firebase_uid,
                        "Nova mensagem recebida",
                        (
                            f"{nome_do_candidato(candidato_uid)} enviou "
                            f"uma mensagem sobre a vaga de {funcao_conversa}."
                        ),
                        reverse(
                            "jobs:conversa",
                            kwargs={
                                "vaga_id": vaga_id,
                                "candidato_uid": candidato_uid,
                            },
                        ),
                    )

        return redirect(
            "jobs:conversa",
            vaga_id=vaga_id,
            candidato_uid=candidato_uid,
        )

    perfil = obter_perfil(str(candidato_uid))

    return render(request, "jobs_conversa.html", {
        "vaga": SimpleNamespace(pk=str(vaga_id), **dados_vaga),
        "candidato_uid": candidato_uid,
        "candidato_nome": nome_do_candidato(candidato_uid),
        "sou_empresa": sou_empresa,
        "mensagens": mensagens_da_conversa(vaga_id, candidato_uid),
        "curriculo_candidato": (
            perfil.curriculo_pdf.url
            if perfil is not None and perfil.curriculo_pdf
            else None
        ),
    })
