from django.shortcuts import render
from django.db.models import Q
from .models import Imovel


def properties_list(request):
    imoveis = Imovel.objects.all()
    q = request.GET.get('q', '').strip()
    local = request.GET.get('local', '').strip()
    if q:
        imoveis = imoveis.filter(
            Q(endereco__icontains=q) |
            Q(bairro__icontains=q) |
            Q(cidade__icontains=q) |
            Q(descricao__icontains=q) |
            Q(caracteristicas__icontains=q)
        )
    if local:
        imoveis = imoveis.filter(
            Q(cidade__icontains=local) |
            Q(bairro__icontains=local) |
            Q(endereco__icontains=local)
        )
    return render(request, 'properties_list.html', {
        'imoveis': imoveis,
        'filtro_q': q,
        'filtro_local': local,
    })
