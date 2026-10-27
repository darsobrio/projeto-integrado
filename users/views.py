from django.contrib.auth.decorators import login_required

from core.views import dashboard


@login_required
def perfil(request):
    """Exibe o painel/perfil do usuário logado.

    O cadastro e o login são centralizados em ``core`` (que também
    sincroniza o Firestore), então aqui apenas reaproveitamos o painel.
    """
    return dashboard(request)
