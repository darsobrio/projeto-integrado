from django.shortcuts import render, redirect
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.http import QueryDict
from django.urls import reverse_lazy
from django.db.models import Q
from jobs.models import Vaga, Candidatura
from properties.models import Imovel
from users.models import CustomUser
from django.http import JsonResponse
from core import db


def home(request):
    vagas_recentes = Vaga.objects.filter(status='aberta')[:3]
    imoveis_recentes = Imovel.objects.all()[:3]
    context = {
        'vagas_recentes': vagas_recentes,
        'imoveis_recentes': imoveis_recentes,
    }
    return render(request, 'home.html', context)


def busca_rapida(request):
    tipo = request.GET.get('tipo_busca', 'vaga').lower()
    q = request.GET.get('q', '').strip()
    local = request.GET.get('local', '').strip()
    qd = QueryDict(mutable=True)
    if q:
        qd['q'] = q
    if local:
        qd['local'] = local
    querystring = f'?{qd.urlencode()}' if qd else ''
    if tipo == 'imovel':
        return redirect(f'/imoveis/{querystring}')
    return redirect(f'/vagas/{querystring}')


def register(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    if request.method == 'POST':
        nome = request.POST.get('nome_completo', '').strip()
        email = request.POST.get('email', '').strip().lower()
        senha = request.POST.get('password', '')
        tipo = request.POST.get('tipo_usuario', 'candidato')
        if not (nome and email and senha):
            messages.error(request, 'Por favor, preencha todos os campos obrigatórios.')
        elif CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Este e-mail já está cadastrado. Faça login ou use outro e-mail.')
        else:
            try:
                username = email.split('@')[0]
                base_username = username
                i = 1
                while CustomUser.objects.filter(username=username).exists():
                    username = f'{base_username}{i}'
                    i += 1
                usuario = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password=senha,
                    nome_completo=nome,
                    tipo_usuario=tipo,
                    cidade=request.POST.get('cidade', '').strip() or None,
                    telefone=request.POST.get('telefone', '').strip() or None,
                    cpf=request.POST.get('cpf', '').strip() or None,
                )
                login(request, usuario)
                messages.success(request, f'Bem-vindo(a), {usuario.nome_completo.split()[0]}! Cadastro realizado com sucesso.')
                return redirect('core:dashboard')
            except Exception as exc:
                messages.error(request, f'Erro no cadastro: {exc}')
    return render(request, 'register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')
    if request.method == 'POST':
        email = request.POST.get('username', '').strip().lower() or request.POST.get('email', '').strip().lower()
        senha = request.POST.get('password', '')
        usuario = authenticate(request, username=email, password=senha)
        if usuario is None:
            try:
                u = CustomUser.objects.get(email=email)
                usuario = authenticate(request, username=u.username, password=senha)
            except CustomUser.DoesNotExist:
                usuario = None
        if usuario is not None:
            login(request, usuario)
            messages.success(request, f'Olá, {usuario.nome_completo.split()[0] if usuario.nome_completo else usuario.email}! Login realizado com sucesso.')
            proximo = request.POST.get('next') or request.GET.get('next') or reverse_lazy('core:dashboard')
            return redirect(proximo)
        messages.error(request, 'E-mail ou senha incorretos. Verifique suas credenciais.')
    logout_param = request.GET.get('logged_out')
    return render(request, 'login.html', {'logged_out': logout_param})


def logout_view(request):
    logout(request)
    messages.info(request, 'Você saiu com segurança. Volte sempre!')
    return redirect('core:login')


@login_required
def dashboard(request):
    usuario = request.user
    context = {
        'usuario': usuario,
        'total_vagas': Vaga.objects.filter(status='aberta').count(),
        'total_imoveis': Imovel.objects.count(),
        'total_usuarios': CustomUser.objects.count(),
    }
    if usuario.tipo_usuario == 'empresa':
        minhas_vagas = Vaga.objects.filter(empresa=usuario)
        context['vagas'] = minhas_vagas
        context['qtd_vagas_abertas'] = minhas_vagas.filter(status='aberta').count()
        context['qtd_candidaturas_total'] = Candidatura.objects.filter(vaga__empresa=usuario).count()
    elif usuario.tipo_usuario == 'proprietario':
        meus_imoveis = Imovel.objects.filter(proprietario=usuario)
        context['imoveis'] = meus_imoveis
        context['imoveis_disponiveis'] = meus_imoveis.filter(disponibilidade__isnull=False).count()
    else:
        minhas_candidaturas = Candidatura.objects.filter(candidato=usuario)
        context['candidaturas'] = minhas_candidaturas
        context['cand_enviadas'] = minhas_candidaturas.filter(status_candidatura='enviada').count()
        context['cand_analise'] = minhas_candidaturas.filter(status_candidatura='em_analise').count()
        context['cand_entrevista'] = minhas_candidaturas.filter(status_candidatura='entrevista').count()
        context['cand_aprovadas'] = minhas_candidaturas.filter(status_candidatura='aprovado').count()
        vagas_abertas = Vaga.objects.filter(status='aberta').exclude(candidaturas__candidato=usuario)
        context['vagas_recomendadas'] = vagas_abertas[:4]
    return render(request, 'dashboard.html', context)
def testar_firebase(request):
    try:
        docs = db.collection("oportunet").limit(10).stream()

        dados = [
            {
                "id": doc.id,
                **doc.to_dict()
            }
            for doc in docs
        ]

        return JsonResponse({"status": "sucesso","mensagem": "Firebase conectado!","oportunidades": dados})

    except Exception as e:
        return JsonResponse({"status": "erro","mensagem": str(e)}, status=500)