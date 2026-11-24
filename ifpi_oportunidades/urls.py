from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from django.views.static import serve as servir_arquivo

urlpatterns = [
    path('', include('core.urls')),
    path('usuarios/', include('users.urls')),
    path('vagas/', include('jobs.urls')),
    path('imoveis/', include('properties.urls')),
    path('api/', include('api.urls')),
]

# ---------------------------------------------------------------------------
# Arquivos enviados pelos usuários (foto de perfil, currículo em PDF, fotos
# dos imóveis, comprovantes).
# ---------------------------------------------------------------------------
# Como o Firebase Storage não é usado, os uploads ficam no disco do servidor
# (MEDIA_ROOT). Eles precisam ser servidos pelo Django também em produção:
# o helper ``static()`` do Django vira no-op quando DEBUG=False, então a rota
# é registrada de forma explícita.
urlpatterns += [
    re_path(
        r'^media/(?P<path>.*)$',
        servir_arquivo,
        {'document_root': settings.MEDIA_ROOT},
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
