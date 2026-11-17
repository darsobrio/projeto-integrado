"""Middleware que hidrata ``request.user`` a partir da sessão.

Substitui o ``AuthenticationMiddleware`` do Django: o usuário é carregado do
Firestore usando o ``firebase_uid`` guardado no cookie de sessão assinado.
"""

from core.auth import usuario_da_sessao
from core.user import AnonymousUser


class SessaoFirebaseMiddleware:
    """Coloca em ``request.user`` o usuário logado (ou um anônimo)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        usuario = None

        try:
            usuario = usuario_da_sessao(request)
        except Exception:
            # Se o Firestore estiver indisponível, o visitante segue anônimo
            # em vez de derrubar a página inteira.
            usuario = None

        request.user = usuario or AnonymousUser()

        return self.get_response(request)
