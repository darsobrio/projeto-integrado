from datetime import datetime
from types import SimpleNamespace

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, QueryDict
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import InvalidArgumentError

from core import db
from core.firebase_auth import (
    autenticar_firebase,
    cadastrar_firebase,
    verificar_token_firebase,
)
from jobs.views import converter_vaga
from properties.views import converter_imovel
from users.models import CustomUser


def relacionar_candidaturas(candidaturas, vagas, usuarios):
    resultado = []

    for candidatura in candidaturas.values():
        vaga_id = str(getattr(candidatura, "vaga_id", ""))
        candidato_id = str(getattr(candidatura, "candidato_id", ""))
        candidato_uid = str(getattr(candidatura, "candidato_uid", "") or "")

        candidatura.vaga = vagas.get(vaga_id)
        candidatura.candidato = usuarios.get(candidato_uid) or usuarios.get(
            candidato_id
        )

        if candidatura.vaga:
            candidatura.vaga.empresa = usuarios.get(
                str(getattr(candidatura.vaga, "empresa_id", ""))
            )

        resultado.append(candidatura)

    return resultado


def carregar_documentos(nome):
    documentos = {}

    for documento in db.collection(nome).stream():
        dados = documento.to_dict() or {}
        dados["id"] = documento.id
        dados["pk"] = documento.id
        documentos[documento.id] = SimpleNamespace(**dados)

    return documentos


def ordenar_por_data(itens, campo):
    return sorted(
        itens,
        key=lambda item: str(getattr(item, campo, "") or ""),
        reverse=True,
    )


def contar_usuarios_unicos(documentos):
    identificadores = set()

    for documento_id, usuario in documentos.items():
        uid = getattr(usuario, "firebase_uid", None)
        email = (getattr(usuario, "email", "") or "").strip().lower()

        if uid:
            chave = ("uid", str(uid))
        elif email:
            chave = ("email", email)
        else:
            chave = ("documento", documento_id)

        identificadores.add(chave)

    return len(identificadores)


def home(request):
    vagas = []
    for documento in db.collection("vagas").stream():
        vaga = converter_vaga(documento)
        if getattr(vaga, "status", "aberta") != "aberta":
            continue
        vagas.append(vaga)

    imoveis = [
        converter_imovel(documento)
        for documento in db.collection("imoveis").stream()
    ]

    vagas_recentes = ordenar_por_data(vagas, "data_publicacao")[:3]
    imoveis_recentes = ordenar_por_data(imoveis, "data_publicacao")[:3]

    context = {
        "vagas_recentes": vagas_recentes,
        "imoveis_recentes": imoveis_recentes,
        "total_vagas": len(vagas),
        "total_imoveis": len(imoveis),
    }

    return render(request, "home.html", context)


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

    if request.method != 'POST':
        return render(request, 'register.html')

    nome = request.POST.get('nome_completo', '').strip()
    email = request.POST.get('email', '').strip().lower()
    senha = request.POST.get('password', '')
    tipo = request.POST.get('tipo_usuario', 'candidato')

    if tipo not in {'candidato', 'empresa', 'proprietario'}:
        tipo = 'candidato'

    if len(nome) < 3 or not email or not senha:
        messages.error(request, 'Preencha nome, e-mail e senha.')
        return render(request, 'register.html')

    if len(senha) < 6:
        messages.error(request, 'A senha deve ter pelo menos 6 caracteres.')
        return render(request, 'register.html')

    if senha != request.POST.get('password_confirm', ''):
        messages.error(request, 'As senhas não conferem.')
        return render(request, 'register.html')

    if CustomUser.objects.filter(email__iexact=email).exists():
        messages.error(
            request,
            'Este e-mail já está cadastrado. Faça login ou use outro e-mail.',
        )
        return render(request, 'register.html')

    cpf = request.POST.get('cpf', '').strip() or None

    if cpf and CustomUser.objects.filter(cpf=cpf).exists():
        messages.error(request, 'Este CPF/CNPJ já está cadastrado.')
        return render(request, 'register.html')

    data_nascimento = None
    data_informada = request.POST.get('data_nascimento', '').strip()

    if data_informada:
        try:
            data_nascimento = datetime.strptime(
                data_informada, '%Y-%m-%d'
            ).date()
        except ValueError:
            messages.error(request, 'Data de nascimento inválida.')
            return render(request, 'register.html')

    uid = None
    usuario = None

    try:
        dados_firebase = cadastrar_firebase(
            email=email,
            senha=senha,
            nome=nome,
        )
        uid = dados_firebase['uid']

        usuario = CustomUser.objects.create_user(
            username=email,
            email=email,
            password=senha,
            nome_completo=nome,
            tipo_usuario=tipo,
            cidade=request.POST.get('cidade', '').strip() or None,
            telefone=request.POST.get('telefone', '').strip() or None,
            cpf=cpf,
            data_nascimento=data_nascimento,
            firebase_uid=uid,
        )

        db.collection('usuarios').document(uid).set({
            'firebase_uid': uid,
            'username': usuario.username,
            'email': usuario.email,
            'nome_completo': usuario.nome_completo,
            'tipo_usuario': usuario.tipo_usuario,
            'cidade': usuario.cidade,
            'telefone': usuario.telefone,
            'cpf': usuario.cpf,
            'data_nascimento': (
                usuario.data_nascimento.isoformat()
                if usuario.data_nascimento
                else None
            ),
            'is_active': usuario.is_active,
        })

        login(request, usuario)
        messages.success(
            request,
            f'Bem-vindo(a), {usuario.nome_completo.split()[0]}! '
            'Cadastro realizado com sucesso.',
        )
        return redirect('core:dashboard')

    except firebase_auth.EmailAlreadyExistsError:
        messages.error(
            request,
            'Este e-mail já está cadastrado. Faça login ou use outro e-mail.',
        )
    except InvalidArgumentError:
        messages.error(
            request,
            'E-mail inválido ou senha muito fraca. Use uma senha com pelo '
            'menos 6 caracteres.',
        )
    except Exception:
        # Desfaz o que já foi criado para não deixar dados órfãos.
        if usuario is not None:
            try:
                usuario.delete()
            except Exception:
                pass

        if uid:
            try:
                db.collection('usuarios').document(uid).delete()
                firebase_auth.delete_user(uid)
            except Exception:
                pass

        messages.error(
            request,
            'Não foi possível concluir o cadastro agora. Tente novamente.',
        )

    return render(request, 'register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        email = (
            request.POST.get('username', '').strip().lower()
            or request.POST.get('email', '').strip().lower()
        )
        senha = request.POST.get('password', '')
        usuario = None

        try:
            dados = autenticar_firebase(email, senha)
            if dados and dados.get('id_token'):
                token_verificado = verificar_token_firebase(dados['id_token'])
                if token_verificado:
                    uid = token_verificado.get('uid')
                    email_verificado = token_verificado.get('email', '').strip().lower()
                    if uid and email_verificado == email:
                        usuario = CustomUser.objects.filter(
                            firebase_uid=uid,
                            email__iexact=email_verificado,
                        ).first()
        except Exception:
            usuario = None

        if usuario is None:
            usuario_django = CustomUser.objects.filter(
                email__iexact=email
            ).first()

            if usuario_django and usuario_django.has_usable_password():
                usuario = authenticate(
                    request,
                    username=usuario_django.username,
                    password=senha,
                )

        if usuario is not None:
            login(request, usuario)
            primeiro_nome = (
                usuario.nome_completo.split()[0]
                if usuario.nome_completo
                else usuario.email
            )
            messages.success(
                request,
                f'Olá, {primeiro_nome}! Login realizado com sucesso.',
            )
            proximo = (
                request.POST.get('next')
                or request.GET.get('next')
                or reverse_lazy('core:dashboard')
            )
            return redirect(proximo)

        messages.error(
            request,
            'E-mail ou senha incorretos. Verifique suas credenciais.',
        )

    logout_param = request.GET.get('logged_out')
    return render(request, 'login.html', {
        'logged_out': logout_param,
        'next': request.POST.get('next') or request.GET.get('next', ''),
    })


def logout_view(request):
    logout(request)
    messages.info(request, 'Você saiu com segurança. Volte sempre!')
    return redirect('core:login')


@login_required
def dashboard(request):
    usuario = request.user

    usuarios = carregar_documentos("usuarios")
    candidaturas_dict = carregar_documentos("candidaturas")

    vagas_dict = {
        documento.id: converter_vaga(documento)
        for documento in db.collection("vagas").stream()
    }
    imoveis_dict = {
        documento.id: converter_imovel(documento)
        for documento in db.collection("imoveis").stream()
    }

    vagas = list(vagas_dict.values())
    imoveis = list(imoveis_dict.values())

    candidaturas = relacionar_candidaturas(
        candidaturas_dict,
        vagas_dict,
        usuarios,
    )

    vagas_abertas = [
        vaga for vaga in vagas
        if getattr(vaga, "status", "aberta") == "aberta"
    ]

    def ordenar(itens, campo):
        return sorted(
            itens,
            key=lambda item: str(
                getattr(item, campo, "") or ""
            ),
            reverse=True,
        )

    context = {
        "usuario": usuario,
        "total_vagas": len(vagas_abertas),
        "total_imoveis": len(imoveis),
        "total_usuarios": contar_usuarios_unicos(usuarios),
    }

    if usuario.tipo_usuario == "empresa":
        minhas_vagas = [
            vaga for vaga in vagas
            if str(getattr(vaga, "empresa_id", ""))
            == str(usuario.pk)
        ]

        ids_minhas_vagas = {
            str(vaga.pk) for vaga in minhas_vagas
        }

        candidaturas_empresa = [
            candidatura for candidatura in candidaturas
            if str(getattr(candidatura, "vaga_id", ""))
            in ids_minhas_vagas
        ]

        for vaga in minhas_vagas:
            vaga.qtd_candidaturas = sum(
                1 for candidatura in candidaturas_empresa
                if str(getattr(candidatura, "vaga_id", ""))
                == str(vaga.pk)
            )

        context["vagas"] = ordenar(
            minhas_vagas, "data_publicacao"
        )
        context["qtd_vagas_abertas"] = sum(
            1 for vaga in minhas_vagas
            if getattr(vaga, "status", "aberta") == "aberta"
        )
        context["qtd_candidaturas_total"] = len(
            candidaturas_empresa
        )
        context["candidaturas_recebidas"] = candidaturas_empresa

    elif usuario.tipo_usuario == "proprietario":
        meus_imoveis = [
            imovel for imovel in imoveis
            if str(getattr(imovel, "proprietario_id", ""))
            == str(usuario.pk)
        ]

        context["imoveis"] = ordenar(meus_imoveis, "criado_em")
        context["imoveis_disponiveis"] = sum(
            1 for imovel in meus_imoveis
            if getattr(imovel, "disponibilidade", None)
        )

    else:
        minhas_candidaturas = [
            candidatura for candidatura in candidaturas
            if (
                str(getattr(candidatura, "candidato_id", ""))
                == str(usuario.pk)
                or (
                    getattr(usuario, "firebase_uid", None)
                    and getattr(candidatura, "candidato_uid", None)
                    == usuario.firebase_uid
                )
            )
        ]

        context["candidaturas"] = ordenar(
            minhas_candidaturas, "data_envio"
        )

        context["cand_enviadas"] = sum(
            1 for c in minhas_candidaturas
            if getattr(c, "status_candidatura", "") == "enviada"
        )
        context["cand_analise"] = sum(
            1 for c in minhas_candidaturas
            if getattr(c, "status_candidatura", "") == "em_analise"
        )
        context["cand_entrevista"] = sum(
            1 for c in minhas_candidaturas
            if getattr(c, "status_candidatura", "") == "entrevista"
        )
        context["cand_aprovadas"] = sum(
            1 for c in minhas_candidaturas
            if getattr(c, "status_candidatura", "") == "aprovado"
        )

        ids_candidatados = {
            str(getattr(c, "vaga_id", ""))
            for c in minhas_candidaturas
        }

        context["vagas_recomendadas"] = [
            vaga for vaga in ordenar(vagas_abertas, "data_publicacao")
            if str(vaga.pk) not in ids_candidatados
        ][:4]

    return render(request, "dashboard.html", context)


@login_required
def testar_firebase(request):
    try:
        docs = db.collection("vagas").limit(10).stream()

        dados = [
            {
                "id": doc.id,
                **doc.to_dict()
            }
            for doc in docs
        ]

        return JsonResponse({
            "status": "sucesso",
            "mensagem": "Firebase conectado!",
            "vagas": dados,
        })

    except Exception as e:
        return JsonResponse({"status": "erro", "mensagem": str(e)}, status=500)