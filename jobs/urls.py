from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.jobs_list, name='list'),
    path('nova/', views.job_create, name='create'),
    path('favoritos/', views.favoritos, name='favoritos'),
    path('alertas/', views.alertas, name='alertas'),
    path('alertas/<str:pk>/remover/', views.alerta_remover, name='alerta_remover'),
    path('candidaturas/', views.candidaturas_recebidas, name='candidaturas'),
    path(
        'minhas-candidaturas/',
        views.minhas_candidaturas,
        name='minhas_candidaturas',
    ),
    path('mensagens/', views.mensagens, name='mensagens'),
    path(
        'mensagens/<str:vaga_id>/<str:candidato_uid>/',
        views.conversa,
        name='conversa',
    ),
    path(
        'candidaturas/<str:pk>/status/',
        views.candidatura_status,
        name='candidatura_status',
    ),
    path('<str:pk>/', views.job_detail, name='detail'),
    path('<str:pk>/favoritar/', views.favoritar, name='favoritar'),
    path('<str:pk>/editar/', views.job_edit, name='edit'),
    path('<str:pk>/status/', views.job_toggle_status, name='toggle_status'),
    path('<str:pk>/excluir/', views.job_delete, name='delete'),
]
