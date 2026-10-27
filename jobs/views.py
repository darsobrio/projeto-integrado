from types import SimpleNamespace

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from google.cloud import firestore

from core import db
from core.utils import (
    MODALIDADE_CHOICES,
    MODALIDADE_LABELS,
    STATUS_VAGA_LABELS,
    TIPO_CONTRATO_CHOICES,
    TIPO_CONTRATO_LABELS,
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


def vaga_do_usuario(request, pk):
    """Devolve o documento da vaga se ela pertencer ao usuário logado."""
    documento = db.collection("vagas").document(str(pk)).get()

    if not documento.exists:
        return None

    dados = documento.to_dict() or {}

    if str(dados.get("empresa_id", "")) != str(request.user.pk):
        return None

    return documento


def jobs_list(request):
    q = request.GET.get("q", "").strip()
    local = request.GET.get("local", "").strip()
    tipo_contrato = request.GET.get("tipo_contrato", "").strip().lower()
    modalidade = request.GET.get("modalidade", "").strip().lower()
    salario_min = numero_decimal(request.GET.get("salario_min"))
    salario_max = numero_decimal(request.GET.get("salario_max"))

    q_busca = q.lower()
    local_busca = local.lower()
    vagas = []

    for documento in db.collection("vagas").stream():
        dados = documento.to_dict() or {}

        if dados.get("status", "aberta") != "aberta":
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

        if tipo_contrato and (
            str(dados.get("tipo_contrato", "")).lower() != tipo_contrato
        ):
            continue

        if modalidade and (
            str(dados.get("modalidade", "")).lower() != modalidade
        ):
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

    vagas.sort(
        key=lambda vaga: str(
            getattr(vaga, "data_publicacao", "")
        ),
        reverse=True,
    )

    return render(request, "jobs_list.html", {
        "vagas": vagas,
        "filtro_q": q,
        "filtro_local": local,
        "filtro_tipo_contrato": tipo_contrato,
        "filtro_modalidade": modalidade,
        "filtro_salario_min": request.GET.get("salario_min", "").strip(),
        "filtro_salario_max": request.GET.get("salario_max", "").strip(),
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

    if request.user.is_authenticated:
        sou_dono = str(getattr(vaga, "empresa_id", "")) == str(
            request.user.pk
        )

    if tipo_usuario == "candidato":
        ja_candidatou = buscar_candidatura(vaga.pk, uid)

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
        messages.success(request, "Candidatura enviada com sucesso! Boa sorte 🤞")
        return redirect("jobs:detail", pk=vaga.pk)

    return render(request, "job_detail.html", {
        "vaga": vaga,
        "ja_candidatou": ja_candidatou,
        "sou_dono": sou_dono,
    })


@login_required
def job_create(request):
    """Publica uma nova vaga no Firestore (apenas empresas)."""
    if request.user.tipo_usuario != "empresa":
        messages.error(request, "Apenas contas de empresa podem publicar vagas.")
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
            referencia.set({
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
            })
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


@login_required
def candidatura_status(request, pk):
    """Atualiza o status de uma candidatura recebida (apenas a empresa)."""
    if request.user.tipo_usuario != "empresa":
        messages.error(
            request, "Apenas contas de empresa podem gerenciar candidaturas."
        )
        return redirect("core:dashboard")

    if request.method != "POST":
        return redirect("core:dashboard")

    novo_status = request.POST.get("status", "").strip()

    if novo_status not in STATUS_CANDIDATURA_VALIDOS:
        messages.error(request, "Status de candidatura inválido.")
        return redirect("core:dashboard")

    documento = db.collection("candidaturas").document(str(pk)).get()

    if not documento.exists:
        messages.error(request, "Candidatura não encontrada.")
        return redirect("core:dashboard")

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
        return redirect("core:dashboard")

    documento.reference.update({"status_candidatura": novo_status})
    messages.success(request, "Status da candidatura atualizado.")
    return redirect("core:dashboard")
