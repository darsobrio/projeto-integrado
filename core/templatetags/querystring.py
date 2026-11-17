"""Filtros e tags usados nos templates do projeto."""

from django import template
from django.http import QueryDict

register = template.Library()


@register.simple_tag(takes_context=True)
def querystring(context, **kwargs):
    """Monta a querystring atual trocando ou removendo parâmetros.

    Use ``None`` ou string vazia para remover um parâmetro. Ao alterar
    qualquer filtro, a paginação volta para a primeira página.

    Exemplos nos templates::

        <a href="?{% querystring q=None %}">remover busca</a>
        <a href="?{% querystring ordem='recentes' %}">mais recentes</a>
    """
    request = context.get("request")
    parametros = request.GET.copy() if request else QueryDict(mutable=True)

    for chave, valor in kwargs.items():
        if valor in (None, ""):
            parametros.pop(chave, None)
        else:
            parametros[chave] = valor

    if kwargs:
        parametros.pop("page", None)

    return parametros.urlencode()
