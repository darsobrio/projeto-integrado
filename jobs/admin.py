from django.contrib import admin
from .models import Vaga, Candidatura


class CandidaturaInline(admin.TabularInline):
    model = Candidatura
    extra = 0
    readonly_fields = ('data_envio',)


@admin.register(Vaga)
class VagaAdmin(admin.ModelAdmin):
    list_display = (
        'funcao',
        'nome_empresa',
        'tipo_contrato',
        'modalidade',
        'salario',
        'status',
        'data_publicacao',
    )
    list_filter = ('tipo_contrato', 'modalidade', 'status')
    search_fields = ('funcao', 'nome_empresa', 'descricao')
    inlines = (CandidaturaInline,)
    readonly_fields = ('data_publicacao',)


@admin.register(Candidatura)
class CandidaturaAdmin(admin.ModelAdmin):
    list_display = ('vaga', 'candidato', 'status_candidatura', 'data_envio')
    list_filter = ('status_candidatura', 'data_envio')
    search_fields = ('vaga__funcao', 'candidato__email', 'candidato__nome_completo')
    readonly_fields = ('data_envio',)
