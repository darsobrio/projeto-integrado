from django.db import models
from django.conf import settings


class Vaga(models.Model):
    CLT = 'clt'
    TEMPORARIO = 'temporario'
    ESTAGIO = 'estagio'
    JOVEM_APRENDIZ = 'jovem_aprendiz'
    FREELANCER = 'freelancer'

    TIPO_CONTRATO_CHOICES = [
        (CLT, 'CLT'),
        (TEMPORARIO, 'Temporário'),
        (ESTAGIO, 'Estágio'),
        (JOVEM_APRENDIZ, 'Jovem Aprendiz'),
        (FREELANCER, 'Freelancer'),
    ]

    PRESENCIAL = 'presencial'
    HIBRIDO = 'hibrido'
    REMOTO = 'remoto'

    MODALIDADE_CHOICES = [
        (PRESENCIAL, 'Presencial'),
        (HIBRIDO, 'Híbrido'),
        (REMOTO, 'Remoto'),
    ]

    ABERTA = 'aberta'
    FECHADA = 'fechada'

    STATUS_CHOICES = [
        (ABERTA, 'Aberta'),
        (FECHADA, 'Fechada'),
    ]

    empresa = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vagas_publicadas',
        limit_choices_to={'tipo_usuario': 'empresa'},
    )
    nome_empresa = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    funcao = models.CharField(max_length=255)
    descricao = models.TextField()
    requisitos = models.TextField()
    salario = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    beneficios = models.TextField(blank=True, null=True)
    horario = models.CharField(max_length=100, blank=True, null=True)
    tipo_contrato = models.CharField(
        max_length=20,
        choices=TIPO_CONTRATO_CHOICES,
        default=CLT,
    )
    modalidade = models.CharField(
        max_length=20,
        choices=MODALIDADE_CHOICES,
        default=PRESENCIAL,
    )
    qtd_vagas = models.PositiveIntegerField(default=1)
    data_publicacao = models.DateTimeField(auto_now_add=True)
    prazo = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=ABERTA,
    )

    class Meta:
        verbose_name = 'Vaga'
        verbose_name_plural = 'Vagas'
        ordering = ['-data_publicacao']

    def __str__(self):
        return f'{self.funcao} - {self.nome_empresa}'


class Candidatura(models.Model):
    ENVIADA = 'enviada'
    EM_ANALISE = 'em_analise'
    ENTREVISTA = 'entrevista'
    APROVADO = 'aprovado'
    RECUSADO = 'recusado'

    STATUS_CHOICES = [
        (ENVIADA, 'Enviada'),
        (EM_ANALISE, 'Em análise'),
        (ENTREVISTA, 'Entrevista'),
        (APROVADO, 'Aprovado'),
        (RECUSADO, 'Recusado'),
    ]

    vaga = models.ForeignKey(
        Vaga,
        on_delete=models.CASCADE,
        related_name='candidaturas',
    )
    candidato = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='candidaturas_enviadas',
        limit_choices_to={'tipo_usuario': 'candidato'},
    )
    data_envio = models.DateTimeField(auto_now_add=True)
    status_candidatura = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=ENVIADA,
    )
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Candidatura'
        verbose_name_plural = 'Candidaturas'
        unique_together = ('vaga', 'candidato')
        ordering = ['-data_envio']

    def __str__(self):
        return f'{self.candidato} -> {self.vaga}'
