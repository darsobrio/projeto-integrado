"""Autenticação e sessão sem banco de dados.

As credenciais continuam no Firebase Authentication e os dados do usuário no
Firestore. A sessão guarda apenas o ``firebase_uid`` em um cookie assinado —
nenhum registro de login é gravado em banco local.

Este módulo substitui os utilitários do ``django.contrib.auth`` usados pelo
projeto: :func:`login`, :func:`logout`, :func:`login_required` e
:func:`staff_member_required`.
"""

from functools import wraps
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, resolve_url
from rest_framework.authentication import BaseAuthentication

from core.user import AnonymousUser, obter_usuario

SESSION_UID_KEY = "firebase_uid"


def login(request, usuario):
    """Inicia a sessão do usuário autenticado no Firebase."""
    request.session[SESSION_UID_KEY] = usuario.firebase_uid
    request.session["firebase_email"] = usuario.email
    request.user = usuario


def logout(request):
    """Encerra a sessão atual."""
    request.session.flush()
    request.user = AnonymousUser()


def update_session_auth_hash(request, usuario):
    """Compatibilidade com o fluxo antigo.

    Com sessão em cookie assinado não existe hash de senha a renovar: o cookie
    continua válido enquanto o ``firebase_uid`` estiver na sessão.
    """
    return None


def usuario_da_sessao(request):
    """Recupera o usuário da sessão ou ``None`` quando não há login."""
    uid = request.session.get(SESSION_UID_KEY)

    if not uid:
        return None

    return obter_usuario(uid)


def _redirecionar_para_login(request):
    destino = resolve_url(settings.LOGIN_URL)
    return HttpResponseRedirect(
        f"{destino}?{urlencode({'next': request.get_full_path()})}"
    )


def login_required(view):
    """Exige um usuário autenticado; senão manda para a tela de login."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not getattr(request.user, "is_authenticated", False):
            return _redirecionar_para_login(request)

        return view(request, *args, **kwargs)

    return wrapper


def staff_member_required(view):
    """Restringe a view a contas com acesso de moderação (staff)."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        usuario = getattr(request, "user", None)

        if not getattr(usuario, "is_authenticated", False):
            return _redirecionar_para_login(request)

        if not (usuario.is_staff or usuario.is_superuser):
            messages.error(
                request, "Você não tem permissão para acessar esta página."
            )
            return redirect("core:home")

        return view(request, *args, **kwargs)

    return wrapper


class AutenticacaoFirebase(BaseAuthentication):
    """Autenticação do DRF baseada na sessão do Django (cookie assinado)."""

    def authenticate(self, request):
        usuario = getattr(getattr(request, "_request", None), "user", None)

        if usuario is None or not getattr(usuario, "is_authenticated", False):
            return None

        return (usuario, None)
