from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.properties_list, name='list'),
    path('novo/', views.property_create, name='create'),
    path('<str:pk>/', views.property_detail, name='detail'),
    path('<str:pk>/editar/', views.property_edit, name='edit'),
    path('<str:pk>/excluir/', views.property_delete, name='delete'),
]
