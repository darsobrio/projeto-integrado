from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('buscar/', views.busca_rapida, name='busca_rapida'),
    path('cadastro/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('login/google/', views.login_google, name='login_google'),
    path('recuperar-senha/', views.password_reset, name='password_reset'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('notificacoes/', views.notificacoes_lista, name='notificacoes'),
    path('notificacoes/marcar-lidas/', views.notificacoes_marcar_lidas, name='notificacoes_marcar_lidas'),
    path('notificacoes/<str:pk>/abrir/', views.notificacao_abrir, name='notificacao_abrir'),
    path('moderacao/', views.moderacao, name='moderacao'),
    path('verificacao/solicitar/', views.solicitar_verificacao, name='solicitar_verificacao'),
    path('denunciar/<str:tipo>/<str:alvo_id>/', views.denunciar, name='denunciar'),
    path("testar-firebase/",views.testar_firebase,name="testar_firebase"),
]
