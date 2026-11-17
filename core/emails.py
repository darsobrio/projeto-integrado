"""Envio de e-mails do Oportunet.

Centraliza o envio para que falhas de e-mail (SMTP fora do ar, credenciais
ausentes em desenvolvimento) nunca quebrem o fluxo principal do usuário.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def enviar_email(destinatario, assunto, mensagem):
    """Envia um e-mail em texto puro. Devolve True/False sem levantar erro."""
    if not destinatario:
        return False

    remetente = getattr(settings, "DEFAULT_FROM_EMAIL", None) or "nao-responder@oportunet.local"

    try:
        send_mail(
            subject=assunto,
            message=mensagem,
            from_email=remetente,
            recipient_list=[destinatario],
            fail_silently=False,
        )
        return True
    except Exception:
        logger.exception("Falha ao enviar e-mail para %s", destinatario)
        return False
