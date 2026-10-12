from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Vaga, Candidatura


def jobs_list(request):
    vagas = Vaga.objects.filter(status='aberta')
    q = request.GET.get('q', '').strip()
    local = request.GET.get('local', '').strip()
    if q:
        vagas = vagas.filter(
            Q(funcao__icontains=q) |
            Q(nome_empresa__icontains=q) |
            Q(descricao__icontains=q) |
            Q(requisitos__icontains=q)
        )
    if local:
        vagas = vagas.filter(
            Q(endereco__icontains=local) |
            Q(funcao__icontains=local) |
            Q(nome_empresa__icontains=local)
        )
    return render(request, 'jobs_list.html', {
        'vagas': vagas,
        'filtro_q': q,
        'filtro_local': local,
    })


@login_required
def job_detail(request, pk):
    vaga = get_object_or_404(Vaga, pk=pk)
    ja_candidatou = False
    if request.user.tipo_usuario == 'candidato':
        ja_candidatou = Candidatura.objects.filter(vaga=vaga, candidato=request.user).exists()
    if request.method == 'POST' and request.user.tipo_usuario == 'candidato' and not ja_candidatou:
        Candidatura.objects.create(vaga=vaga, candidato=request.user)
        messages.success(request, 'Candidatura enviada com sucesso! Boa sorte 🤞')
        return redirect('jobs:detail', pk=vaga.pk)
    return render(request, 'job_detail.html', {'vaga': vaga, 'ja_candidatou': ja_candidatou})
