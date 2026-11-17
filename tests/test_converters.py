"""Testes da conversão dos documentos do Firestore e dos serializers da API.

Estes testes não acessam o Firestore: usam um documento falso que só precisa
expor ``id`` e ``to_dict()``, como o objeto devolvido pelo SDK.
"""

from django.test import SimpleTestCase

from api.serializers import ImovelSerializer, VagaSerializer
from jobs.views import converter_vaga, vaga_vencida
from properties.views import converter_imovel


class DocumentoFalso:
    """Imita um DocumentSnapshot do Firestore para os testes."""

    def __init__(self, identificador, dados):
        self.id = identificador
        self._dados = dados

    def to_dict(self):
        return dict(self._dados)

    @property
    def exists(self):
        return True


class VagaVencidaTests(SimpleTestCase):
    def test_vaga_com_prazo_futuro_continua_aberta(self):
        self.assertFalse(vaga_vencida({'prazo': '2999-12-31'}))

    def test_vaga_com_prazo_passado_esta_vencida(self):
        self.assertTrue(vaga_vencida({'prazo': '2000-01-01'}))

    def test_vaga_sem_prazo_nunca_vence(self):
        self.assertFalse(vaga_vencida({'prazo': ''}))
        self.assertFalse(vaga_vencida({}))


class ConverterVagaTests(SimpleTestCase):
    def test_converter_preenche_campos_calculados(self):
        documento = DocumentoFalso('vaga-1', {
            'funcao': 'Estágio em Informática',
            'nome_empresa': 'IFPI',
            'salario': 1200,
            'tipo_contrato': 'estagio',
            'modalidade': 'presencial',
            'status': 'aberta',
            'data_publicacao': '2026-11-01',
        })

        vaga = converter_vaga(documento)

        self.assertEqual(vaga.id, 'vaga-1')
        self.assertEqual(vaga.funcao, 'Estágio em Informática')
        self.assertEqual(vaga.salario_display, '1.200,00')
        self.assertEqual(vaga.tipo_contrato_display, 'Estágio')
        self.assertEqual(vaga.data_publicacao_display, '01/11/2026')
        self.assertTrue(vaga.aberta)

    def test_converter_marca_vaga_vencida_como_encerrada(self):
        documento = DocumentoFalso('vaga-2', {
            'funcao': 'Auxiliar',
            'status': 'aberta',
            'prazo': '2000-01-01',
        })

        vaga = converter_vaga(documento)

        self.assertTrue(vaga.vencida)
        self.assertFalse(vaga.aberta)
        self.assertEqual(vaga.status_display, 'Encerrada')

    def test_serializer_de_vaga_tolera_campos_ausentes(self):
        documento = DocumentoFalso('vaga-3', {'funcao': 'Vaga mínima'})
        dados = VagaSerializer(converter_vaga(documento)).data

        self.assertEqual(dados['id'], 'vaga-3')
        self.assertEqual(dados['cnpj'], '')
        self.assertIsNone(dados['salario'])
        # Sem "status" no documento, a vaga é tratada como aberta.
        self.assertTrue(dados['aberta'])


class ConverterImovelTests(SimpleTestCase):
    def test_galeria_com_varias_fotos(self):
        documento = DocumentoFalso('imovel-1', {
            'endereco': 'Rua A, 123',
            'valor_aluguel': 800,
            'fotos': ['fachada.jpg', 'sala.jpg'],
        })

        imovel = converter_imovel(documento)

        self.assertEqual(imovel.valor_aluguel_display, '800,00')
        self.assertEqual(len(imovel.fotos_urls), 2)
        self.assertTrue(imovel.foto_url.endswith('fachada.jpg'))

    def test_foto_unica_antiga_vira_galeria(self):
        documento = DocumentoFalso('imovel-2', {'foto': 'unica.jpg'})

        imovel = converter_imovel(documento)

        self.assertEqual(imovel.fotos_urls, [imovel.foto_url])
        self.assertTrue(imovel.foto_url.endswith('unica.jpg'))

    def test_imovel_sem_fotos(self):
        imovel = converter_imovel(DocumentoFalso('imovel-3', {}))

        self.assertEqual(imovel.fotos_urls, [])
        self.assertIsNone(imovel.foto_url)

    def test_mapa_so_existe_com_latitude_e_longitude(self):
        com_mapa = converter_imovel(DocumentoFalso('imovel-4', {
            'latitude': '-7.9',
            'longitude': '-40.8',
        }))
        sem_mapa = converter_imovel(DocumentoFalso('imovel-5', {}))

        self.assertTrue(com_mapa.tem_mapa)
        self.assertFalse(sem_mapa.tem_mapa)

    def test_serializer_de_imovel(self):
        documento = DocumentoFalso('imovel-6', {
            'cidade': 'Paulistana',
            'fotos': ['a.jpg'],
        })
        dados = ImovelSerializer(converter_imovel(documento)).data

        self.assertEqual(dados['id'], 'imovel-6')
        self.assertEqual(dados['cidade'], 'Paulistana')
        self.assertEqual(len(dados['fotos_urls']), 1)
