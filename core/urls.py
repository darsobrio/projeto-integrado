from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('buscar/', views.busca_rapida, name='busca_rapida'),
    path('cadastro/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path("testar-firebase/",views.testar_firebase,name="testar_firebase"),
]