"""Rotas da API REST (prefixo /api/)."""

from django.urls import path

from api import views

app_name = 'api'

urlpatterns = [
    path('vagas/', views.VagaListView.as_view(), name='vagas'),
    path('vagas/<str:pk>/', views.VagaDetailView.as_view(), name='vaga_detail'),
    path('imoveis/', views.ImovelListView.as_view(), name='imoveis'),
    path(
        'imoveis/<str:pk>/',
        views.ImovelDetailView.as_view(),
        name='imovel_detail',
    ),
    path(
        'candidaturas/',
        views.CandidaturaView.as_view(),
        name='candidaturas',
    ),
]
