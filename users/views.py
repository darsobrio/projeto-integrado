from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def register(request):
    return render(request, 'register.html')


def login_view(request):
    return render(request, 'login.html')


@login_required
def perfil(request):
    return render(request, 'dashboard.html')
