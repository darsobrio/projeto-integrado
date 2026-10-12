from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    CANDIDATO = 'candidato'
    EMPRESA = 'empresa'
    PROPRIETARIO = 'proprietario'

    TIPO_USUARIO_CHOICES = [
        (CANDIDATO, 'Candidato'),
        (EMPRESA, 'Empresa'),
        (PROPRIETARIO, 'Proprietário'),
    ]

    ESCOLARIDADE_CHOICES = [
        ('fundamental', 'Ensino Fundamental'),
        ('medio', 'Ensino Médio'),
        ('tecnico', 'Curso Técnico'),
        ('superior', 'Ensino Superior'),
        ('pos', 'Pós-Graduação'),
    ]

    nome_completo = models.CharField(max_length=255, blank=True, null=True)
    cpf = models.CharField(max_length=14, unique=True, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    foto_perfil = models.ImageField(upload_to='perfis/fotos/', blank=True, null=True)
    endereco = models.CharField(max_length=255, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default=CANDIDATO,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return self.email or self.username


class PerfilCandidato(models.Model):
    usuario = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='perfil_candidato',
    )
    sobre_mim = models.TextField(blank=True, null=True)
    escolaridade = models.CharField(
        max_length=20,
        choices=CustomUser.ESCOLARIDADE_CHOICES,
        blank=True,
        null=True,
    )
    instituicao = models.CharField(max_length=255, blank=True, null=True)
    cursos = models.TextField(blank=True, null=True)
    formacao_academica = models.TextField(blank=True, null=True)
    diplomas = models.TextField(blank=True, null=True)
    experiencias = models.TextField(blank=True, null=True)
    habilidades = models.TextField(blank=True, null=True)
    idiomas = models.CharField(max_length=255, blank=True, null=True)
    curriculo_pdf = models.FileField(upload_to='perfis/curriculos/', blank=True, null=True)
    link_portfolio = models.URLField(max_length=255, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Perfil do Candidato'
        verbose_name_plural = 'Perfis dos Candidatos'

    def __str__(self):
        return f'Perfil de {self.usuario.get_full_name() or self.usuario.email}'
