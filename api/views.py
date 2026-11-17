"""Endpoints REST do Oportunet (Django REST Framework).

Os dados vivem no Firestore, então as views convertem os documentos com os
mesmos helpers usados no site (``converter_vaga`` / ``converter_imovel``) para
manter o formato consistente entre web e API.
"""

from google.cloud import firestore
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import (
    CandidaturaCreateSerializer,
    CandidaturaSerializer,
    ImovelSerializer,
    VagaSerializer,
)
from core import db
from core.pagination import paginar
from core.utils import numero_decimal, numero_inteiro
from jobs.views import converter_vaga, vaga_vencida
from properties.views import converter_imovel


def _resposta_paginada(paginacao, serializador):
    return Response({
        'total': paginacao.total_itens,
        'pagina': paginacao.pagina,
        'total_paginas': paginacao.total_paginas,
        'resultados': serializador(paginacao.itens, many=True).data,
    })


class VagaListView(APIView):
    """GET /api/vagas/ — lista de vagas abertas, com os mesmos filtros do site."""

    permission_classes = [AllowAny]

    def get(self, request):
        q = request.query_params.get('q', '').strip().lower()
        local = request.query_params.get('local', '').strip().lower()
        tipo = request.query_params.get('tipo_contrato', '').strip().lower()
        modalidade = request.query_params.get('modalidade', '').strip().lower()
        salario_min = numero_decimal(request.query_params.get('salario_min'))
        salario_max = numero_decimal(request.query_params.get('salario_max'))

        consulta = db.collection('vagas').where('status', '==', 'aberta')

        if tipo:
            consulta = consulta.where('tipo_contrato', '==', tipo)
        if modalidade:
            consulta = consulta.where('modalidade', '==', modalidade)

        vagas = []

        for documento in consulta.stream():
            dados = documento.to_dict() or {}

            if vaga_vencida(dados):
                continue

            if q:
                texto = ' '.join([
                    str(dados.get('funcao', '')),
                    str(dados.get('nome_empresa', '')),
                    str(dados.get('descricao', '')),
                    str(dados.get('requisitos', '')),
                ]).lower()
                if q not in texto:
                    continue

            if local:
                texto_local = ' '.join([
                    str(dados.get('endereco', '')),
                    str(dados.get('funcao', '')),
                    str(dados.get('nome_empresa', '')),
                ]).lower()
                if local not in texto_local:
                    continue

            salario = numero_decimal(dados.get('salario'))

            if salario_min is not None and (salario is None or salario < salario_min):
                continue
            if salario_max is not None and (salario is None or salario > salario_max):
                continue

            vagas.append(converter_vaga(documento))

        vagas.sort(
            key=lambda v: str(getattr(v, 'data_publicacao', '') or ''),
            reverse=True,
        )

        return _resposta_paginada(paginar(vagas, request, por_pagina=9), VagaSerializer)


class VagaDetailView(APIView):
    """GET /api/vagas/<pk>/ — detalhes de uma vaga."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        documento = db.collection('vagas').document(str(pk)).get()

        if not documento.exists:
            return Response(
                {'detail': 'Vaga não encontrada.'}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(VagaSerializer(converter_vaga(documento)).data)


class ImovelListView(APIView):
    """GET /api/imoveis/ — lista de imóveis, com filtros básicos."""

    permission_classes = [AllowAny]

    def get(self, request):
        q = request.query_params.get('q', '').strip().lower()
        local = request.query_params.get('local', '').strip().lower()
        preco_min = numero_decimal(request.query_params.get('preco_min'))
        preco_max = numero_decimal(request.query_params.get('preco_max'))
        quartos = numero_inteiro(request.query_params.get('quartos'), 0)
        mobiliado = request.query_params.get('mobiliado') in ('1', 'true', 'on')
        aceita_animais = request.query_params.get('aceita_animais') in ('1', 'true', 'on')

        consulta = db.collection('imoveis')

        if mobiliado:
            consulta = consulta.where('mobiliado', '==', True)
        if aceita_animais:
            consulta = consulta.where('aceita_animais', '==', True)

        imoveis = []

        for documento in consulta.stream():
            dados = documento.to_dict() or {}

            if q:
                texto = ' '.join([
                    str(dados.get('endereco') or ''),
                    str(dados.get('bairro') or ''),
                    str(dados.get('cidade') or ''),
                    str(dados.get('descricao') or ''),
                ]).lower()
                if q not in texto:
                    continue

            if local:
                texto_local = ' '.join([
                    str(dados.get('cidade') or ''),
                    str(dados.get('bairro') or ''),
                    str(dados.get('endereco') or ''),
                ]).lower()
                if local not in texto_local:
                    continue

            valor = numero_decimal(dados.get('valor_aluguel'))

            if preco_min is not None and (valor is None or valor < preco_min):
                continue
            if preco_max is not None and (valor is None or valor > preco_max):
                continue
            if quartos and numero_inteiro(dados.get('quartos'), 0) < quartos:
                continue

            imoveis.append(converter_imovel(documento))

        imoveis.sort(
            key=lambda i: str(getattr(i, 'data_publicacao', '') or ''),
            reverse=True,
        )

        return _resposta_paginada(
            paginar(imoveis, request, por_pagina=9), ImovelSerializer
        )


class ImovelDetailView(APIView):
    """GET /api/imoveis/<pk>/ — detalhes de um imóvel."""

    permission_classes = [AllowAny]

    def get(self, request, pk):
        documento = db.collection('imoveis').document(str(pk)).get()

        if not documento.exists:
            return Response(
                {'detail': 'Imóvel não encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(ImovelSerializer(converter_imovel(documento)).data)


class CandidaturaView(APIView):
    """GET/POST /api/candidaturas/ — lista e cria candidaturas do usuário."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        uid = str(getattr(request.user, 'firebase_uid', '') or '')

        if not uid:
            return Response(
                {'detail': 'Conta sem vínculo com o Firebase.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        candidaturas = []

        for documento in (
            db.collection('candidaturas')
            .where('candidato_uid', '==', uid)
            .stream()
        ):
            dados = documento.to_dict() or {}
            vaga = db.collection('vagas').document(
                str(dados.get('vaga_id', ''))
            ).get()
            dados_vaga = vaga.to_dict() if vaga.exists else {}

            candidaturas.append({
                'vaga_id': str(dados.get('vaga_id', '')),
                'funcao': dados_vaga.get('funcao', ''),
                'nome_empresa': dados_vaga.get('nome_empresa', ''),
                'status_candidatura': dados.get('status_candidatura', ''),
                'data_envio': dados.get('data_envio'),
            })

        return Response(CandidaturaSerializer(candidaturas, many=True).data)

    def post(self, request):
        entrada = CandidaturaCreateSerializer(data=request.data)

        if not entrada.is_valid():
            return Response(entrada.errors, status=status.HTTP_400_BAD_REQUEST)

        vaga_id = str(entrada.validated_data['vaga_id'])
        documento = db.collection('vagas').document(vaga_id).get()

        if not documento.exists:
            return Response(
                {'detail': 'Vaga não encontrada.'}, status=status.HTTP_404_NOT_FOUND
            )

        if not getattr(request.user, 'firebase_uid', None):
            return Response(
                {'detail': 'Conta sem vínculo com o Firebase.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        uid = request.user.firebase_uid
        referencia = db.collection('candidaturas').document(f'{vaga_id}_{uid}')

        if referencia.get().exists:
            return Response(
                {'detail': 'Você já se candidatou a esta vaga.'},
                status=status.HTTP_409_CONFLICT,
            )

        referencia.set({
            'vaga_id': vaga_id,
            'candidato_id': request.user.pk,
            'candidato_uid': uid,
            'data_envio': firestore.SERVER_TIMESTAMP,
            'status_candidatura': 'enviada',
            'observacoes': '',
        })

        return Response(
            {'detail': 'Candidatura enviada com sucesso.', 'vaga_id': vaga_id},
            status=status.HTTP_201_CREATED,
        )
