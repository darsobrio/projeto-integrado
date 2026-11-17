"""Serializers da API.

Os dados de vagas e imóveis vivem no Firestore e são convertidos em objetos
simples antes de chegar aqui, então os serializers apenas descrevem o formato
de saída (e validam a entrada de candidaturas).

Como documentos antigos podem não ter todos os campos, cada campo de saída
declara um ``default`` para que a ausência de uma chave não quebre a resposta.
"""

from rest_framework import serializers


class VagaSerializer(serializers.Serializer):
    id = serializers.CharField()
    funcao = serializers.CharField(allow_blank=True, default='')
    nome_empresa = serializers.CharField(allow_blank=True, default='')
    cnpj = serializers.CharField(allow_blank=True, default='')
    descricao = serializers.CharField(allow_blank=True, default='')
    requisitos = serializers.CharField(allow_blank=True, default='')
    beneficios = serializers.CharField(allow_blank=True, default='')
    horario = serializers.CharField(allow_blank=True, default='')
    endereco = serializers.CharField(allow_blank=True, default='')
    salario = serializers.FloatField(allow_null=True, default=None)
    salario_display = serializers.CharField(allow_null=True, default=None)
    tipo_contrato = serializers.CharField(allow_blank=True, default='')
    modalidade = serializers.CharField(allow_blank=True, default='')
    qtd_vagas = serializers.IntegerField(allow_null=True, default=None)
    data_publicacao_display = serializers.CharField(allow_blank=True, default='')
    prazo_display = serializers.CharField(allow_blank=True, default='')
    status = serializers.CharField(allow_blank=True, default='')
    aberta = serializers.BooleanField(default=False)


class ImovelSerializer(serializers.Serializer):
    id = serializers.CharField()
    endereco = serializers.CharField(allow_blank=True, default='')
    bairro = serializers.CharField(allow_blank=True, default='')
    cidade = serializers.CharField(allow_blank=True, default='')
    valor_aluguel = serializers.FloatField(allow_null=True, default=None)
    valor_aluguel_display = serializers.CharField(allow_null=True, default=None)
    quartos = serializers.IntegerField(allow_null=True, default=None)
    banheiros = serializers.IntegerField(allow_null=True, default=None)
    garagem = serializers.IntegerField(allow_null=True, default=None)
    area_m2 = serializers.FloatField(allow_null=True, default=None)
    mobiliado = serializers.BooleanField(allow_null=True, default=None)
    aceita_animais = serializers.BooleanField(allow_null=True, default=None)
    descricao = serializers.CharField(allow_blank=True, default='')
    fotos_urls = serializers.ListField(
        child=serializers.CharField(), default=list
    )
    latitude = serializers.FloatField(allow_null=True, default=None)
    longitude = serializers.FloatField(allow_null=True, default=None)
    data_publicacao_display = serializers.CharField(allow_blank=True, default='')


class CandidaturaSerializer(serializers.Serializer):
    vaga_id = serializers.CharField()
    funcao = serializers.CharField(allow_blank=True, default='')
    nome_empresa = serializers.CharField(allow_blank=True, default='')
    status_candidatura = serializers.CharField(allow_blank=True, default='')
    data_envio = serializers.CharField(allow_null=True, default=None)


class CandidaturaCreateSerializer(serializers.Serializer):
    vaga_id = serializers.CharField(
        help_text='Id da vaga (documento do Firestore).'
    )
