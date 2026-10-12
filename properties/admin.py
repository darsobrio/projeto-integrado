from django.contrib import admin
from .models import Imovel


@admin.register(Imovel)
class ImovelAdmin(admin.ModelAdmin):
    list_display = (
        'endereco',
        'bairro',
        'cidade',
        'valor_aluguel',
        'quartos',
        'mobiliado',
        'aceita_animais',
        'criado_em',
    )
    list_filter = (
        'cidade',
        'mobiliado',
        'aceita_animais',
        'quartos',
        'criado_em',
    )
    search_fields = ('endereco', 'bairro', 'cidade', 'descricao')
    readonly_fields = ('criado_em', 'atualizado_em')
