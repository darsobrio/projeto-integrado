from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('cadastro/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('perfil/', views.perfil, name='perfil'),
]
