"""Testes das funções auxiliares de core/utils.py."""

from django.test import SimpleTestCase

from core.utils import (
    TIPO_CONTRATO_LABELS,
    chave_data,
    formatar_data,
    formatar_moeda,
    numero_decimal,
    numero_inteiro,
    rotulo,
    somente_digitos,
    validar_cnpj,
    validar_cpf,
)


class DocumentoBrasileiroTests(SimpleTestCase):
    def test_cpf_valido(self):
        self.assertTrue(validar_cpf('529.982.247-25'))

    def test_cpf_sequencia_repetida_e_rejeitado(self):
        self.assertFalse(validar_cpf('111.111.111-11'))

    def test_cpf_digito_invalido(self):
        self.assertFalse(validar_cpf('123.456.789-00'))

    def test_cpf_curto(self):
        self.assertFalse(validar_cpf('123'))

    def test_cnpj_valido(self):
        self.assertTrue(validar_cnpj('11.222.333/0001-81'))

    def test_cnpj_sequencia_repetida_e_rejeitado(self):
        self.assertFalse(validar_cnpj('11.111.111/1111-11'))

    def test_cnpj_digito_invalido(self):
        self.assertFalse(validar_cnpj('11.222.333/0001-00'))


class FormatacaoTests(SimpleTestCase):
    def test_formatar_moeda_numero(self):
        self.assertEqual(formatar_moeda(2500), '2.500,00')

    def test_formatar_moeda_com_virgula(self):
        self.assertEqual(formatar_moeda('2500,50'), '2.500,50')

    def test_formatar_moeda_vazio(self):
        self.assertIsNone(formatar_moeda(None))

    def test_formatar_data_iso(self):
        self.assertEqual(formatar_data('2026-11-30'), '30/11/2026')

    def test_formatar_data_vazia(self):
        self.assertEqual(formatar_data(None), '')

    def test_numero_decimal_ponto_e_virgula(self):
        self.assertEqual(numero_decimal('1.234,56'), 1234.56)

    def test_numero_decimal_invalido(self):
        self.assertIsNone(numero_decimal('abc'))
        self.assertIsNone(numero_decimal(''))

    def test_numero_inteiro_com_padrao(self):
        self.assertEqual(numero_inteiro('3'), 3)
        self.assertEqual(numero_inteiro(None, 0), 0)

    def test_somente_digitos(self):
        self.assertEqual(somente_digitos('529.982.247-25'), '52998224725')

    def test_rotulo_conhecido(self):
        self.assertEqual(rotulo(TIPO_CONTRATO_LABELS, 'clt'), 'CLT')

    def test_rotulo_padrao(self):
        self.assertEqual(rotulo(TIPO_CONTRATO_LABELS, '', 'x'), 'x')

    def test_chave_data_ordena_datas(self):
        self.assertLess(
            chave_data('2026-01-01T00:00:00'),
            chave_data('2026-05-01T00:00:00'),
        )

    def test_chave_data_vazia(self):
        self.assertEqual(chave_data(None), 0.0)
