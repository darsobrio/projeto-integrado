"""Testes dos tipos de conta no objeto de usuário."""

from unittest.mock import patch

from django.test import SimpleTestCase

from core.user import TIPO_USUARIO_CHOICES, Usuario, criar_usuario


class TipoUsuarioTests(SimpleTestCase):
    def test_opcoes_publicas_nao_incluem_o_tipo_removido(self):
        self.assertEqual(
            TIPO_USUARIO_CHOICES,
            [("candidato", "Candidato"), ("empresa", "Empresa")],
        )

    def test_conta_legada_de_proprietario_carrega_como_candidato(self):
        usuario = Usuario(
            "firebase-uid",
            {"tipo_usuario": "proprietario"},
        )

        self.assertEqual(usuario.tipo_usuario, "candidato")

    def test_tipo_nao_reconhecido_carrega_como_candidato(self):
        usuario = Usuario(
            "firebase-uid",
            {"tipo_usuario": "tipo-invalido"},
        )

        self.assertEqual(usuario.tipo_usuario, "candidato")

    def test_novo_usuario_nao_pode_ser_criado_com_tipo_removido(self):
        with patch("core.user.salvar_usuario") as salvar:
            usuario = criar_usuario(
                firebase_uid="firebase-uid",
                email="usuario@example.com",
                tipo_usuario="proprietario",
            )

        self.assertEqual(usuario.tipo_usuario, "candidato")
        salvar.assert_called_once_with(usuario)
