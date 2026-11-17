"""Paginação simples para as listagens do Oportunet.

As listagens precisam filtrar campos de texto/salário em Python, então a
paginação é aplicada depois do filtro. O helper devolve a fatia da página
atual e os dados necessários para montar os botões de navegação.
"""

from types import SimpleNamespace


def paginar(itens, request, por_pagina=9, parametro="page"):
    """Devolve a fatia da página atual e dados de navegação."""
    itens = list(itens)

    try:
        pagina = int(request.GET.get(parametro, 1))
    except (TypeError, ValueError):
        pagina = 1

    total = len(itens)
    total_paginas = max(1, -(-total // por_pagina))
    pagina = min(max(pagina, 1), total_paginas)

    inicio = (pagina - 1) * por_pagina
    fim = inicio + por_pagina

    parametros = request.GET.copy()
    parametros.pop(parametro, None)
    querystring = parametros.urlencode()

    # Janela de páginas ao redor da atual (no máximo 5 botões).
    inicio_janela = max(1, pagina - 2)
    fim_janela = min(total_paginas, inicio_janela + 4)
    inicio_janela = max(1, fim_janela - 4)
    numeros = list(range(inicio_janela, fim_janela + 1))

    return SimpleNamespace(
        itens=itens[inicio:fim],
        pagina=pagina,
        total_paginas=total_paginas,
        total_itens=total,
        tem_anterior=pagina > 1,
        tem_proxima=pagina < total_paginas,
        pagina_anterior=pagina - 1,
        pagina_proxima=pagina + 1,
        numeros=numeros,
        querystring=querystring,
        parametro=parametro,
    )
