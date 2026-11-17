from django.urls import path

from . import views

app_name = 'users'

urlpatterns = [
    path('perfil/', views.perfil, name='perfil'),
    path('empresa/<str:uid>/', views.empresa_detalhe, name='empresa_detalhe'),
    path('candidato/<str:uid>/', views.candidato_detalhe, name='candidato_detalhe'),
]
