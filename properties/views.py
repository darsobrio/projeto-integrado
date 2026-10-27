from types import SimpleNamespace

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from core import db
from core.utils import (
    formatar_data,
    formatar_moeda,
    numero_decimal,
    numero_inteiro,
)
from google.cloud import firestore


def converter_imovel(documento):
    dados = documento.to_dict() or {}
    dados["id"] = documento.id
    dados["pk"] = documento.id
    dados["valor_aluguel_display"] = formatar_moeda(dados.get("valor_aluguel"))
    dados["valor_condominio_display"] = formatar_moeda(
        dados.get("valor_condominio")
    )
    dados["data_publicacao_display"] = formatar_data(
        dados.get("data_publicacao") or dados.get("criado_em")
    )
    dados["disponibilidade_display"] = formatar_data(
        dados.get("disponibilidade")
    )
    return SimpleNamespace(**dados)


def imovel_do_usuario(request, pk):
    """Devolve o documento do imóvel se ele pertencer ao usuário logado."""
    documento = db.collection("imoveis").document(str(pk)).get()

    if not documento.exists:
        return None

    dados = documento.to_dict() or {}

    if str(dados.get("proprietario_id", "")) != str(request.user.pk):
        return None

    return documento


def properties_list(request):
    q = request.GET.get("q", "").strip()
    local = request.GET.get("local", "").strip()
    preco_min = numero_decimal(request.GET.get("preco_min"))
    preco_max = numero_decimal(request.GET.get("preco_max"))
    quartos = numero_inteiro(request.GET.get("quartos"), 0)
    aceita_animais = request.GET.get("aceita_animais") == "on"
    mobiliado = request.GET.get("mobiliado") == "on"

    q_busca = q.lower()
    local_busca = local.lower()
    imoveis = []

    for documento in db.collection("imoveis").stream():
        dados = documento.to_dict() or {}
        dados["id"] = documento.id
        dados["pk"] = documento.id

        texto_busca = " ".join([
            str(dados.get("endereco") or ""),
            str(dados.get("bairro") or ""),
            str(dados.get("cidade") or ""),
            str(dados.get("descricao") or ""),
            str(dados.get("caracteristicas") or ""),
        ]).lower()

        texto_local = " ".join([
            str(dados.get("cidade") or ""),
            str(dados.get("bairro") or ""),
            str(dados.get("endereco") or ""),
        ]).lower()

        if q_busca and q_busca not in texto_busca:
            continue

        if local_busca and local_busca not in texto_local:
            continue

        valor = numero_decimal(dados.get("valor_aluguel"))

        if preco_min is not None and (valor is None or valor < preco_min):
            continue

        if preco_max is not None and (valor is None or valor > preco_max):
            continue

        if quartos and numero_inteiro(dados.get("quartos"), 0) < quartos:
            continue

        if aceita_animais and not dados.get("aceita_animais"):
            continue

        if mobiliado and not dados.get("mobiliado"):
            continue

        imoveis.append(converter_imovel(documento))

    imoveis.sort(
        key=lambda imovel: str(
            getattr(imovel, "data_cadastro", "")
            or getattr(imovel, "data_publicacao", "")
            or getattr(imovel, "criado_em", "")
        ),
        reverse=True,
    )
    return render(request, "properties_list.html", {
        "imoveis": imoveis,
        "filtro_q": q,
        "filtro_local": local,
        "filtro_preco_min": request.GET.get("preco_min", "").strip(),
        "filtro_preco_max": request.GET.get("preco_max", "").strip(),
        "filtro_quartos": request.GET.get("quartos", "").strip(),
        "filtro_aceita_animais": aceita_animais,
        "filtro_mobiliado": mobiliado,
    })


def property_detail(request, pk):
    documento = db.collection("imoveis").document(str(pk)).get()

    if not documento.exists:
        messages.error(request, "Esse imóvel não foi encontrado.")
        return redirect("properties:list")

    imovel = converter_imovel(documento)
    sou_dono = (
        request.user.is_authenticated
        and str(getattr(imovel, "proprietario_id", "")) == str(request.user.pk)
    )

    return render(request, "property_detail.html", {
        "imovel": imovel,
        "sou_dono": sou_dono,
    })


@login_required
def property_create(request):
    """Publica um novo imóvel no Firestore (apenas proprietários)."""
    if request.user.tipo_usuario != "proprietario":
        messages.error(
            request, "Apenas contas de proprietário podem anunciar imóveis."
        )
        return redirect("core:dashboard")

    if request.method == "POST":
        endereco = request.POST.get("endereco", "").strip()
        cidade = request.POST.get("cidade", "").strip()
        valor_aluguel = numero_decimal(request.POST.get("valor_aluguel"))

        if not (endereco and cidade) or valor_aluguel is None:
            messages.error(
                request,
                "Preencha os campos obrigatórios: endereço, cidade e valor do aluguel.",
            )
        else:
            referencia = db.collection("imoveis").document()
            referencia.set({
                "proprietario_id": str(request.user.pk),
                "proprietario_uid": getattr(request.user, "firebase_uid", None),
                "endereco": endereco,
                "bairro": request.POST.get("bairro", "").strip(),
                "cidade": cidade,
                "valor_aluguel": valor_aluguel,
                "valor_condominio": numero_decimal(
                    request.POST.get("valor_condominio")
                ),
                "quartos": numero_inteiro(request.POST.get("quartos"), 1),
                "banheiros": numero_inteiro(request.POST.get("banheiros"), 1),
                "garagem": numero_inteiro(request.POST.get("garagem"), 0),
                "area_m2": numero_decimal(request.POST.get("area_m2")),
                "mobiliado": request.POST.get("mobiliado") == "on",
                "aceita_animais": request.POST.get("aceita_animais") == "on",
                "descricao": request.POST.get("descricao", "").strip(),
                "caracteristicas": request.POST.get("caracteristicas", "").strip(),
                "regras": request.POST.get("regras", "").strip(),
                "contato_proprietario": (
                    request.POST.get("contato_proprietario", "").strip()
                    or request.user.telefone
                ),
                "disponibilidade": request.POST.get("disponibilidade", "").strip(),
                "data_publicacao": firestore.SERVER_TIMESTAMP,
                "criado_em": firestore.SERVER_TIMESTAMP,
                "atualizado_em": firestore.SERVER_TIMESTAMP,
            })
            messages.success(request, "Imóvel anunciado com sucesso!")
            return redirect("properties:detail", pk=referencia.id)

    return render(request, "property_form.html")


@login_required
def property_edit(request, pk):
    """Edita um imóvel existente (apenas o proprietário responsável)."""
    if request.user.tipo_usuario != "proprietario":
        messages.error(
            request, "Apenas contas de proprietário podem editar imóveis."
        )
        return redirect("core:dashboard")

    documento = imovel_do_usuario(request, pk)

    if documento is None:
        messages.error(request, "Imóvel não encontrado ou sem permissão de acesso.")
        return redirect("core:dashboard")

    if request.method == "POST":
        endereco = request.POST.get("endereco", "").strip()
        cidade = request.POST.get("cidade", "").strip()
        valor_aluguel = numero_decimal(request.POST.get("valor_aluguel"))

        if not (endereco and cidade) or valor_aluguel is None:
            messages.error(
                request,
                "Preencha os campos obrigatórios: endereço, cidade e valor do aluguel.",
            )
        else:
            documento.reference.update({
                "endereco": endereco,
                "bairro": request.POST.get("bairro", "").strip(),
                "cidade": cidade,
                "valor_aluguel": valor_aluguel,
                "valor_condominio": numero_decimal(
                    request.POST.get("valor_condominio")
                ),
                "quartos": numero_inteiro(request.POST.get("quartos"), 1),
                "banheiros": numero_inteiro(request.POST.get("banheiros"), 1),
                "garagem": numero_inteiro(request.POST.get("garagem"), 0),
                "area_m2": numero_decimal(request.POST.get("area_m2")),
                "mobiliado": request.POST.get("mobiliado") == "on",
                "aceita_animais": request.POST.get("aceita_animais") == "on",
                "descricao": request.POST.get("descricao", "").strip(),
                "caracteristicas": request.POST.get("caracteristicas", "").strip(),
                "regras": request.POST.get("regras", "").strip(),
                "contato_proprietario": (
                    request.POST.get("contato_proprietario", "").strip()
                    or request.user.telefone
                ),
                "disponibilidade": request.POST.get("disponibilidade", "").strip(),
                "atualizado_em": firestore.SERVER_TIMESTAMP,
            })
            messages.success(request, "Imóvel atualizado com sucesso!")
            return redirect("properties:detail", pk=pk)

    imovel = converter_imovel(documento)

    return render(request, "property_form.html", {
        "imovel": imovel,
        "modo_edicao": True,
    })


@login_required
def property_delete(request, pk):
    """Exclui um imóvel (apenas o proprietário responsável)."""
    if request.method != "POST":
        return redirect("core:dashboard")

    documento = imovel_do_usuario(request, pk)

    if documento is None:
        messages.error(request, "Imóvel não encontrado ou sem permissão de acesso.")
        return redirect("core:dashboard")

    documento.reference.delete()
    messages.success(request, "Imóvel excluído com sucesso.")
    return redirect("core:dashboard")
