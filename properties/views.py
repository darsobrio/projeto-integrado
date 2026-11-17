import os
from math import asin, cos, radians, sin, sqrt
from types import SimpleNamespace
from uuid import uuid4

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from core import db
from core.moderation import LIMITE_IMOVEIS_POR_PROPRIETARIO
from core.pagination import paginar
from core.utils import (
    chave_data,
    formatar_data,
    formatar_moeda,
    numero_decimal,
    numero_inteiro,
)
from google.cloud import firestore

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
TAMANHO_MAXIMO_IMAGEM = 5 * 1024 * 1024


MAXIMO_FOTOS = 6


def salvar_uma_foto(arquivo):
    """Valida e salva uma imagem, devolvendo o caminho relativo."""
    extensao = os.path.splitext(arquivo.name)[1].lower()

    if extensao not in EXTENSOES_IMAGEM:
        raise ValidationError(
            "Envie as fotos em um destes formatos: JPG, PNG, WEBP ou GIF."
        )

    if arquivo.size > TAMANHO_MAXIMO_IMAGEM:
        raise ValidationError("Cada foto deve ter no máximo 5 MB.")

    return default_storage.save(
        f"imoveis/fotos/{uuid4().hex}{extensao}", arquivo
    )


def salvar_fotos_imovel(request):
    """Salva as fotos enviadas (várias) e devolve a lista de caminhos.

    Aceita o campo múltiplo ``fotos`` e, por compatibilidade, o campo único
    ``foto``. No máximo ``MAXIMO_FOTOS`` imagens por anúncio.
    """
    arquivos = [a for a in request.FILES.getlist("fotos") if a]

    avulsa = request.FILES.get("foto")
    if avulsa:
        arquivos.append(avulsa)

    if not arquivos:
        return []

    if len(arquivos) > MAXIMO_FOTOS:
        raise ValidationError(
            f"Envie no máximo {MAXIMO_FOTOS} fotos por anúncio."
        )

    return [salvar_uma_foto(arquivo) for arquivo in arquivos]


def remover_foto_imovel(caminho):
    """Apaga do disco uma foto antiga, se ela existir."""
    if not caminho:
        return

    try:
        default_storage.delete(caminho)
    except Exception:
        pass


def remover_fotos_imovel(caminhos):
    for caminho in caminhos or []:
        remover_foto_imovel(caminho)


def resolver_url_foto(caminho):
    if not caminho:
        return None

    try:
        return default_storage.url(caminho)
    except Exception:
        return None


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

    dados["latitude"] = numero_decimal(dados.get("latitude"))
    dados["longitude"] = numero_decimal(dados.get("longitude"))
    dados["tem_mapa"] = (
        dados["latitude"] is not None and dados["longitude"] is not None
    )

    # Galeria: usa a lista de fotos e, se não houver, a foto única antiga.
    caminhos = list(dados.get("fotos") or [])
    if not caminhos and dados.get("foto"):
        caminhos = [dados["foto"]]

    dados["fotos_urls"] = [
        url for url in (resolver_url_foto(c) for c in caminhos) if url
    ]
    dados["foto_url"] = dados["fotos_urls"][0] if dados["fotos_urls"] else None

    return SimpleNamespace(**dados)


def distancia_km(lat1, lng1, lat2, lng2):
    """Distância aproximada (fórmula de Haversine) em quilômetros."""
    raio_terra = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    )
    return 2 * raio_terra * asin(sqrt(a))


def imovel_do_usuario(request, pk):
    """Devolve o documento do imóvel se ele pertencer ao usuário logado."""
    documento = db.collection("imoveis").document(str(pk)).get()

    if not documento.exists:
        return None

    dados = documento.to_dict() or {}

    if str(dados.get("proprietario_id", "")) != str(request.user.pk):
        return None

    return documento


def id_favorito_imovel(imovel_id, uid):
    """Id determinístico de um imóvel favoritado."""
    return f"{imovel_id}_{uid}"


def ids_favoritos_imoveis(uid):
    """Conjunto com os ids dos imóveis favoritados por um usuário."""
    if not uid:
        return set()

    return {
        str((documento.to_dict() or {}).get("imovel_id"))
        for documento in db.collection("favoritos_imoveis")
        .where("usuario_uid", "==", str(uid))
        .stream()
    }


ORDENACOES_IMOVEIS = {
    "recentes": ("data_publicacao", True),
    "menor_preco": ("valor_aluguel", False),
    "maior_preco": ("valor_aluguel", True),
}

ORDENACAO_IMOVEIS_CHOICES = [
    ("recentes", "Mais recentes"),
    ("menor_preco", "Menor preço"),
    ("maior_preco", "Maior preço"),
]


def properties_list(request):
    q = request.GET.get("q", "").strip()
    local = request.GET.get("local", "").strip()
    preco_min = numero_decimal(request.GET.get("preco_min"))
    preco_max = numero_decimal(request.GET.get("preco_max"))
    quartos = numero_inteiro(request.GET.get("quartos"), 0)
    aceita_animais = request.GET.get("aceita_animais") == "on"
    mobiliado = request.GET.get("mobiliado") == "on"
    ordem = request.GET.get("ordem", "recentes").strip().lower()

    if ordem not in ORDENACOES_IMOVEIS:
        ordem = "recentes"

    q_busca = q.lower()
    local_busca = local.lower()

    # Filtros de igualdade (booleanos) direto no Firestore.
    consulta = db.collection("imoveis")

    if mobiliado:
        consulta = consulta.where("mobiliado", "==", True)

    if aceita_animais:
        consulta = consulta.where("aceita_animais", "==", True)

    imoveis = []

    for documento in consulta.stream():
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

        imoveis.append(converter_imovel(documento))

    # Filtro por proximidade: usa a localização informada (ou "perto de mim")
    # e mantém apenas os imóveis dentro do raio, ordenados por distância.
    lat = numero_decimal(request.GET.get("lat"))
    lng = numero_decimal(request.GET.get("lng"))
    raio_km = numero_decimal(request.GET.get("raio")) or 25.0
    modo_proximidade = lat is not None and lng is not None

    if modo_proximidade:
        proximos = []

        for imovel in imoveis:
            if not getattr(imovel, "tem_mapa", False):
                continue

            distancia = distancia_km(
                lat, lng, imovel.latitude, imovel.longitude
            )

            if distancia <= raio_km:
                imovel.distancia_km = round(distancia, 1)
                proximos.append(imovel)

        proximos.sort(key=lambda imovel: imovel.distancia_km)
        imoveis = proximos
    else:
        campo, decrescente = ORDENACOES_IMOVEIS[ordem]

        if campo == "valor_aluguel":
            imoveis.sort(
                key=lambda imovel: (
                    numero_decimal(getattr(imovel, "valor_aluguel", None)) or 0.0
                ),
                reverse=decrescente,
            )
        else:
            imoveis.sort(
                key=lambda imovel: chave_data(
                    getattr(imovel, "data_publicacao", None)
                    or getattr(imovel, "criado_em", None)
                ),
                reverse=decrescente,
            )

    # Pontos para o mapa (somente imóveis com coordenadas).
    mapa_imoveis = [
        {
            "id": imovel.pk,
            "lat": imovel.latitude,
            "lng": imovel.longitude,
            "endereco": imovel.endereco,
            "cidade": imovel.cidade,
            "valor": imovel.valor_aluguel_display,
            "url": f"/imoveis/{imovel.pk}/",
        }
        for imovel in imoveis
        if getattr(imovel, "tem_mapa", False)
    ]

    if modo_proximidade:
        centro = {"lat": lat, "lng": lng}
    elif mapa_imoveis:
        centro = {
            "lat": sum(p["lat"] for p in mapa_imoveis) / len(mapa_imoveis),
            "lng": sum(p["lng"] for p in mapa_imoveis) / len(mapa_imoveis),
        }
    else:
        # Centro padrão: Paulistana - PI.
        centro = {"lat": -8.3828, "lng": -41.4464}

    paginacao = paginar(imoveis, request, por_pagina=9)

    return render(request, "properties_list.html", {
        "imoveis": paginacao.itens,
        "paginacao": paginacao,
        "mapa_imoveis": mapa_imoveis,
        "mapa_centro": centro,
        "modo_proximidade": modo_proximidade,
        "filtro_lat": request.GET.get("lat", "").strip(),
        "filtro_lng": request.GET.get("lng", "").strip(),
        "filtro_raio": request.GET.get("raio", "").strip(),
        "filtro_q": q,
        "filtro_local": local,
        "filtro_preco_min": request.GET.get("preco_min", "").strip(),
        "filtro_preco_max": request.GET.get("preco_max", "").strip(),
        "filtro_quartos": request.GET.get("quartos", "").strip(),
        "filtro_aceita_animais": aceita_animais,
        "filtro_mobiliado": mobiliado,
        "filtro_ordem": ordem,
        "ordenacao_choices": ORDENACAO_IMOVEIS_CHOICES,
        "favoritos": ids_favoritos_imoveis(
            getattr(request.user, "firebase_uid", None)
        ),
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
    favoritos = ids_favoritos_imoveis(
        getattr(request.user, "firebase_uid", None)
    )

    # Imóveis semelhantes: prioriza anúncios da mesma cidade.
    if getattr(imovel, "cidade", None):
        consulta_similares = db.collection("imoveis").where(
            "cidade", "==", imovel.cidade
        )
    else:
        consulta_similares = db.collection("imoveis")

    imoveis_similares = []

    for documento_similar in consulta_similares.limit(40).stream():
        if documento_similar.id == imovel.pk:
            continue

        imoveis_similares.append(converter_imovel(documento_similar))

        if len(imoveis_similares) >= 3:
            break

    return render(request, "property_detail.html", {
        "imovel": imovel,
        "sou_dono": sou_dono,
        "favoritado": str(pk) in favoritos,
        "imoveis_similares": imoveis_similares,
    })


@login_required
def property_create(request):
    """Publica um novo imóvel no Firestore.

    Qualquer conta autenticada pode anunciar (candidato, empresa ou
    proprietário), já que uma mesma pessoa pode buscar vagas e alugar imóveis.
    """
    anunciados = db.collection("imoveis").where(
        "proprietario_id", "==", str(request.user.pk)
    ).stream()
    total_anunciados = sum(1 for _ in anunciados)

    if total_anunciados >= LIMITE_IMOVEIS_POR_PROPRIETARIO:
        messages.error(
            request,
            f"Você atingiu o limite de {LIMITE_IMOVEIS_POR_PROPRIETARIO} "
            "imóveis anunciados por conta. Exclua um anúncio para publicar outro.",
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
            try:
                fotos = salvar_fotos_imovel(request)
            except ValidationError as erro:
                messages.error(request, erro.messages[0])
                return render(request, "property_form.html")

            dados = {
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
                "latitude": numero_decimal(request.POST.get("latitude")),
                "longitude": numero_decimal(request.POST.get("longitude")),
                "data_publicacao": firestore.SERVER_TIMESTAMP,
                "criado_em": firestore.SERVER_TIMESTAMP,
                "atualizado_em": firestore.SERVER_TIMESTAMP,
            }

            if fotos:
                dados["fotos"] = fotos
                dados["foto"] = fotos[0]

            referencia = db.collection("imoveis").document()
            referencia.set(dados)
            messages.success(request, "Imóvel anunciado com sucesso!")
            return redirect("properties:detail", pk=referencia.id)

    return render(request, "property_form.html")


@login_required
def property_edit(request, pk):
    """Edita um imóvel existente (apenas o responsável pelo anúncio)."""
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
            try:
                fotos = salvar_fotos_imovel(request)
            except ValidationError as erro:
                messages.error(request, erro.messages[0])
                return redirect("properties:edit", pk=pk)

            dados = {
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
                "latitude": numero_decimal(request.POST.get("latitude")),
                "longitude": numero_decimal(request.POST.get("longitude")),
                "atualizado_em": firestore.SERVER_TIMESTAMP,
            }

            if fotos:
                dados["fotos"] = fotos
                dados["foto"] = fotos[0]
                antigas = (documento.to_dict() or {})
                remover_fotos_imovel(antigas.get("fotos"))
                remover_foto_imovel(antigas.get("foto"))

            documento.reference.update(dados)
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


# ---------------------------------------------------------------------------
# Favoritos de imóveis
# ---------------------------------------------------------------------------

def destino_seguro(request, padrao):
    """Devolve o parâmetro ``next`` apenas se apontar para o próprio site."""
    destino = request.POST.get("next") or ""
    if destino and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}
    ):
        return destino
    return padrao


@login_required
def favoritar_imovel(request, pk):
    """Adiciona ou remove um imóvel dos favoritos do usuário (POST)."""
    destino = destino_seguro(
        request, reverse("properties:detail", kwargs={"pk": pk})
    )

    if request.method != "POST":
        return redirect(destino)

    uid = getattr(request.user, "firebase_uid", None)

    if not uid:
        messages.error(
            request,
            "Sua conta não está vinculada ao Firebase. Entre novamente.",
        )
        return redirect(destino)

    documento = db.collection("favoritos_imoveis").document(
        id_favorito_imovel(pk, uid)
    )

    if documento.get().exists:
        documento.delete()
        messages.info(request, "Imóvel removido dos favoritos.")
    else:
        documento.set({
            "imovel_id": str(pk),
            "usuario_id": request.user.pk,
            "usuario_uid": uid,
            "criado_em": firestore.SERVER_TIMESTAMP,
        })
        messages.success(request, "Imóvel salvo nos favoritos.")

    return redirect(destino)


@login_required
def favoritos_imoveis(request):
    """Lista os imóveis favoritados pelo usuário logado."""
    uid = getattr(request.user, "firebase_uid", None)
    imoveis = []

    for imovel_id in ids_favoritos_imoveis(uid):
        documento = db.collection("imoveis").document(imovel_id).get()
        if documento.exists:
            imoveis.append(converter_imovel(documento))

    imoveis.sort(
        key=lambda imovel: chave_data(
            getattr(imovel, "data_publicacao", None)
            or getattr(imovel, "criado_em", None)
        ),
        reverse=True,
    )

    return render(request, "properties_favoritos.html", {"imoveis": imoveis})
