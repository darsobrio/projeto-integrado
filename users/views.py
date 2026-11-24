"""Perfil do usuário: dados da conta, perfil profissional e segurança."""

import os
from datetime import datetime

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.shortcuts import redirect, render
from django.urls import reverse
from google.cloud import firestore

from core import db
from core.auth import login_required
from core.firebase_auth import alterar_senha, autenticar_firebase
from core.user import (
    ArquivoRemoto,
    obter_perfil,
    obter_usuario_por_identificador,
    salvar_perfil,
    salvar_usuario,
)
from core.utils import chave_data
from jobs.views import converter_vaga

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
TAMANHO_MAXIMO_IMAGEM = 5 * 1024 * 1024
TAMANHO_MAXIMO_CURRICULO = 10 * 1024 * 1024

CAMPOS_CONTA = [
    "nome_completo",
    "telefone",
    "cidade",
    "endereco",
    "data_nascimento",
    "foto_perfil",
]

CAMPOS_PROFISSIONAIS = [
    "sobre_mim",
    "escolaridade",
    "instituicao",
    "cursos",
    "formacao_academica",
    "diplomas",
    "experiencias",
    "habilidades",
    "idiomas",
    "link_portfolio",
    "curriculo_pdf",
]


def validar_imagem(arquivo):
    extensao = os.path.splitext(arquivo.name)[1].lower()

    if extensao not in EXTENSOES_IMAGEM:
        raise ValidationError(
            "Envie a foto em um destes formatos: JPG, PNG, WEBP ou GIF."
        )

    if arquivo.size > TAMANHO_MAXIMO_IMAGEM:
        raise ValidationError("A foto deve ter no máximo 5 MB.")


def validar_curriculo(arquivo):
    extensao = os.path.splitext(arquivo.name)[1].lower()

    if extensao != ".pdf":
        raise ValidationError("O currículo deve ser um arquivo PDF.")

    if arquivo.size > TAMANHO_MAXIMO_CURRICULO:
        raise ValidationError("O currículo deve ter no máximo 10 MB.")


def calcular_completude(usuario, perfil_candidato):
    """Percentual de preenchimento do perfil (conta + perfil profissional)."""
    campos = [(usuario, campo) for campo in CAMPOS_CONTA]

    if usuario.tipo_usuario == "candidato" and perfil_candidato is not None:
        campos += [(perfil_candidato, campo) for campo in CAMPOS_PROFISSIONAIS]

    preenchidos = sum(
        1 for objeto, campo in campos if getattr(objeto, campo, None)
    )

    return round(100 * preenchidos / len(campos)) if campos else 0


ROTULOS_CAMPOS = {
    "nome_completo": "Nome completo",
    "telefone": "Telefone",
    "cidade": "Cidade",
    "endereco": "Endereço",
    "data_nascimento": "Data de nascimento",
    "foto_perfil": "Foto de perfil",
    "sobre_mim": "Sobre mim",
    "escolaridade": "Escolaridade",
    "instituicao": "Instituição",
    "cursos": "Cursos",
    "formacao_academica": "Formação acadêmica",
    "diplomas": "Diplomas",
    "experiencias": "Experiências",
    "habilidades": "Habilidades",
    "idiomas": "Idiomas",
    "link_portfolio": "Portfólio (link)",
    "curriculo_pdf": "Currículo em PDF",
}


def campos_pendentes(usuario, perfil_candidato):
    """Campos que ainda estão vazios, com o rótulo e a aba onde são preenchidos."""
    campos = [(usuario, campo, "conta") for campo in CAMPOS_CONTA]

    if usuario.tipo_usuario == "candidato" and perfil_candidato is not None:
        campos += [
            (perfil_candidato, campo, "profissional")
            for campo in CAMPOS_PROFISSIONAIS
        ]

    return [
        {
            "campo": campo,
            "rotulo": ROTULOS_CAMPOS.get(campo, campo),
            "secao": secao,
        }
        for objeto, campo, secao in campos
        if not getattr(objeto, campo, None)
    ]


def salvar_dados_conta(request, usuario):
    nome = request.POST.get("nome_completo", "").strip()

    if len(nome) < 3:
        messages.error(request, "Informe o nome completo (mínimo 3 letras).")
        return False

    foto = request.FILES.get("foto_perfil")

    if foto:
        try:
            validar_imagem(foto)
        except ValidationError as erro:
            messages.error(request, erro.messages[0])
            return False

    usuario.nome_completo = nome
    usuario.telefone = request.POST.get("telefone", "").strip() or None
    usuario.cidade = request.POST.get("cidade", "").strip() or None
    usuario.endereco = request.POST.get("endereco", "").strip() or None

    data_nascimento = request.POST.get("data_nascimento", "").strip()

    if data_nascimento:
        try:
            usuario.data_nascimento = datetime.strptime(
                data_nascimento, "%Y-%m-%d"
            ).date()
        except ValueError:
            messages.error(request, "Data de nascimento inválida.")
            return False

    if foto:
        extensao = os.path.splitext(foto.name)[1].lower()
        caminho = default_storage.save(
            f"perfis/{usuario.firebase_uid}{extensao}", foto
        )
        usuario.foto_perfil = ArquivoRemoto(caminho)

    salvar_usuario(usuario)
    messages.success(request, "Dados da conta atualizados com sucesso.")
    return True


def salvar_perfil_profissional(request, perfil_candidato):
    curriculo = request.FILES.get("curriculo_pdf")

    if curriculo:
        try:
            validar_curriculo(curriculo)
        except ValidationError as erro:
            messages.error(request, erro.messages[0])
            return False

    for campo in CAMPOS_PROFISSIONAIS:
        if campo == "curriculo_pdf":
            continue
        setattr(perfil_candidato, campo, request.POST.get(campo, "").strip() or None)

    if curriculo:
        caminho = default_storage.save(
            f"curriculos/{perfil_candidato.firebase_uid}.pdf", curriculo
        )
        perfil_candidato.curriculo_pdf = ArquivoRemoto(caminho)

    salvar_perfil(perfil_candidato)
    messages.success(request, "Perfil profissional atualizado com sucesso.")
    return True


def salvar_nova_senha(request, usuario):
    senha_atual = request.POST.get("senha_atual", "")
    nova_senha = request.POST.get("nova_senha", "")
    confirmacao = request.POST.get("confirmar_senha", "")

    if len(nova_senha) < 6:
        messages.error(request, "A nova senha deve ter pelo menos 6 caracteres.")
        return False

    if nova_senha != confirmacao:
        messages.error(request, "A confirmação não confere com a nova senha.")
        return False

    if not getattr(usuario, "firebase_uid", None):
        messages.error(
            request,
            "Sua conta não está vinculada ao Firebase. Entre novamente.",
        )
        return False

    if autenticar_firebase(usuario.email, senha_atual) is None:
        messages.error(request, "A senha atual está incorreta.")
        return False

    try:
        alterar_senha(usuario.firebase_uid, nova_senha)
    except Exception:
        messages.error(
            request, "Não foi possível alterar a senha agora. Tente novamente."
        )
        return False

    messages.success(request, "Senha alterada com sucesso.")
    return True


@login_required
def perfil(request):
    """Exibe e atualiza os dados da conta e o perfil profissional."""
    usuario = request.user
    perfil_candidato = None

    if usuario.tipo_usuario == "candidato":
        perfil_candidato = obter_perfil(usuario.firebase_uid, criar=True)

    if request.method == "POST":
        secao = request.POST.get("secao", "conta")

        if secao == "conta":
            salvar_dados_conta(request, usuario)
        elif secao == "profissional" and perfil_candidato is not None:
            salvar_perfil_profissional(request, perfil_candidato)
        elif secao == "seguranca":
            salvar_nova_senha(request, usuario)

        return redirect(f"{reverse('users:perfil')}?aba={secao}")

    return render(
        request,
        "profile.html",
        {
            "perfil_candidato": perfil_candidato,
            "completude": calcular_completude(usuario, perfil_candidato),
            "pendentes": campos_pendentes(usuario, perfil_candidato),
            "escolaridade_choices": usuario.ESCOLARIDADE_CHOICES,
            "aba": request.GET.get("aba", "conta"),
        },
    )


# ---------------------------------------------------------------------------
# Perfis públicos
# ---------------------------------------------------------------------------


def perfil_do_usuario(usuario):
    if usuario.tipo_usuario == "candidato":
        return obter_perfil(usuario.firebase_uid, criar=True)

    return None


def empresa_detalhe(request, uid):
    """Perfil público da empresa, com todas as vagas abertas."""
    empresa = obter_usuario_por_identificador(uid)

    if empresa is None or empresa.tipo_usuario != "empresa":
        messages.error(request, "Empresa não encontrada.")
        return redirect("jobs:list")

    uid_empresa = getattr(empresa, "firebase_uid", None)

    vagas = []

    for documento in db.collection("vagas").stream():
        dados = documento.to_dict() or {}

        pertence = (
            str(dados.get("empresa_id", "")) == str(empresa.pk)
            or (
                uid_empresa
                and str(dados.get("empresa_uid", "")) == str(uid_empresa)
            )
        )

        if pertence:
            vagas.append(converter_vaga(documento))

    vagas.sort(key=lambda vaga: chave_data(vaga.data_publicacao), reverse=True)
    abertas = [vaga for vaga in vagas if vaga.aberta]

    return render(request, "empresa_publica.html", {
        "empresa": empresa,
        "vagas": abertas,
        "total_vagas": len(vagas),
        "total_abertas": len(abertas),
        "total_encerradas": len(vagas) - len(abertas),
        "sou_dono": (
            request.user.is_authenticated
            and request.user.pk == empresa.pk
        ),
    })


def candidato_detalhe(request, uid):
    """Perfil público do candidato.

    O currículo em PDF só é liberado para o próprio candidato e para
    empresas autenticadas (privacidade dos dados pessoais).
    """
    candidato = obter_usuario_por_identificador(uid)

    if candidato is None or candidato.tipo_usuario != "candidato":
        messages.error(request, "Candidato não encontrado.")
        return redirect("jobs:list")

    perfil = perfil_do_usuario(candidato)
    sou_dono = (
        request.user.is_authenticated and request.user.pk == candidato.pk
    )
    pode_ver_curriculo = sou_dono or (
        request.user.is_authenticated
        and getattr(request.user, "tipo_usuario", None) == "empresa"
    )

    return render(request, "candidato_publico.html", {
        "candidato": candidato,
        "perfil": perfil,
        "sou_dono": sou_dono,
        "pode_ver_curriculo": pode_ver_curriculo,
    })
