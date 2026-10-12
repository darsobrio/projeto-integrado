from django.db import models
from django.conf import settings


class Imovel(models.Model):
    proprietario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='imoveis',
        limit_choices_to={'tipo_usuario': 'proprietario'},
    )
    fotos = models.ImageField(upload_to='imoveis/fotos/', blank=True, null=True)
    endereco = models.CharField(max_length=255)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100)
    valor_aluguel = models.DecimalField(max_digits=10, decimal_places=2)
    valor_condominio = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    quartos = models.PositiveIntegerField(default=1)
    banheiros = models.PositiveIntegerField(default=1)
    garagem = models.PositiveIntegerField(default=0)
    area_m2 = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    mobiliado = models.BooleanField(default=False)
    aceita_animais = models.BooleanField(default=False)
    descricao = models.TextField(blank=True, null=True)
    caracteristicas = models.TextField(blank=True, null=True)
    regras = models.TextField(blank=True, null=True)
    contato_proprietario = models.CharField(max_length=255, blank=True, null=True)
    disponibilidade = models.DateField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Imóvel'
        verbose_name_plural = 'Imóveis'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.endereco} - {self.bairro or self.cidade}'
