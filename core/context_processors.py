"""Context processors globais do Oportunet."""

from core.notificacoes import contar_nao_lidas, notificacoes_do_usuario


def usuario(request):
    """Expõe o usuário da requisição como ``user`` nos templates.

    Substitui o ``django.contrib.auth.context_processors.auth``.
    """
    return {"user": getattr(request, "user", None)}


def notificacoes(request):
    """Expõe o contador e as últimas notificações do usuário na navbar."""
    usuario = getattr(request, "user", None)

    if usuario is None or not usuario.is_authenticated:
        return {}

    uid = getattr(usuario, "firebase_uid", None)

    return {
        "nao_lidas": contar_nao_lidas(uid),
        "ultimas_notificacoes": notificacoes_do_usuario(uid, limite=6),
    }
