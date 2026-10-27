from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.jobs_list, name='list'),
    path('nova/', views.job_create, name='create'),
    path(
        'candidaturas/<str:pk>/status/',
        views.candidatura_status,
        name='candidatura_status',
    ),
    path('<str:pk>/', views.job_detail, name='detail'),
    path('<str:pk>/editar/', views.job_edit, name='edit'),
    path('<str:pk>/status/', views.job_toggle_status, name='toggle_status'),
    path('<str:pk>/excluir/', views.job_delete, name='delete'),
]
