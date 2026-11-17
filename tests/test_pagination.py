"""Testes da paginação pós-filtro (core/pagination.py)."""

from django.test import RequestFactory, SimpleTestCase

from core.pagination import paginar


class PaginacaoTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_primeira_pagina(self):
        request = self.factory.get('/vagas/', {'page': '1'})
        resultado = paginar(range(25), request, por_pagina=9)

        self.assertEqual(resultado.pagina, 1)
        self.assertEqual(resultado.total_paginas, 3)
        self.assertEqual(resultado.total_itens, 25)
        self.assertEqual(len(resultado.itens), 9)
        self.assertFalse(resultado.tem_anterior)
        self.assertTrue(resultado.tem_proxima)

    def test_ultima_pagina_tem_resto(self):
        request = self.factory.get('/vagas/', {'page': '3'})
        resultado = paginar(range(25), request, por_pagina=9)

        self.assertEqual(resultado.pagina, 3)
        self.assertEqual(len(resultado.itens), 7)
        self.assertTrue(resultado.tem_anterior)
        self.assertFalse(resultado.tem_proxima)

    def test_pagina_invalida_volta_para_primeira(self):
        request = self.factory.get('/vagas/', {'page': 'abc'})
        self.assertEqual(paginar(range(10), request).pagina, 1)

    def test_pagina_fora_do_intervalo_e_limitada(self):
        request = self.factory.get('/vagas/', {'page': '99'})
        resultado = paginar(range(10), request, por_pagina=9)

        self.assertEqual(resultado.pagina, 2)
        self.assertFalse(resultado.tem_proxima)

    def test_lista_vazia_tem_uma_pagina(self):
        request = self.factory.get('/vagas/')
        resultado = paginar([], request)

        self.assertEqual(resultado.total_paginas, 1)
        self.assertEqual(resultado.itens, [])
        self.assertFalse(resultado.tem_anterior)
        self.assertFalse(resultado.tem_proxima)

    def test_querystring_preserva_filtros(self):
        request = self.factory.get('/vagas/', {'q': 'estagio', 'page': '2'})
        resultado = paginar(range(30), request, por_pagina=9)

        self.assertEqual(resultado.pagina, 2)
        self.assertIn('q=estagio', resultado.querystring)
        self.assertNotIn('page=', resultado.querystring)
