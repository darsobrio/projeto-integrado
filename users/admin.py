from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PerfilCandidato


class PerfilCandidatoInline(admin.StackedInline):
    model = PerfilCandidato
    can_delete = False
    verbose_name_plural = 'Perfil do Candidato'


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    inlines = (PerfilCandidatoInline,)
    list_display = ('email', 'nome_completo', 'tipo_usuario', 'cidade', 'is_staff')
    list_filter = ('tipo_usuario', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        (
            'Informações Adicionais',
            {
                'fields': (
                    'nome_completo',
                    'cpf',
                    'data_nascimento',
                    'telefone',
                    'foto_perfil',
                    'endereco',
                    'cidade',
                    'tipo_usuario',
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'Informações Adicionais',
            {
                'fields': (
                    'email',
                    'nome_completo',
                    'tipo_usuario',
                )
            },
        ),
    )
    search_fields = ('email', 'nome_completo', 'cpf')
    ordering = ('email',)


admin.site.register(CustomUser, CustomUserAdmin)
