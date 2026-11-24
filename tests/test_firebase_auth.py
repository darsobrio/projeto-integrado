"""Testes das validações de token do Firebase Auth."""

from django.test import SimpleTestCase

from core.firebase_auth import token_tem_google_verificado


class TokenGoogleTests(SimpleTestCase):
    def test_aceita_login_direto_com_google_verificado(self):
        token = {
            "email_verified": True,
            "firebase": {"sign_in_provider": "google.com"},
        }

        self.assertTrue(token_tem_google_verificado(token))

    def test_aceita_google_vinculado_a_conta_existente(self):
        token = {
            "email_verified": True,
            "firebase": {
                "sign_in_provider": "password",
                "identities": {"google.com": ["google-user-id"]},
            },
        }

        self.assertTrue(token_tem_google_verificado(token))

    def test_rejeita_conta_sem_identidade_google(self):
        token = {
            "email_verified": True,
            "firebase": {
                "sign_in_provider": "password",
                "identities": {"email": ["user@example.com"]},
            },
        }

        self.assertFalse(token_tem_google_verificado(token))

    def test_rejeita_email_google_nao_verificado(self):
        token = {
            "email_verified": False,
            "firebase": {"sign_in_provider": "google.com"},
        }

        self.assertFalse(token_tem_google_verificado(token))

    def test_rejeita_token_ausente(self):
        self.assertFalse(token_tem_google_verificado(None))
