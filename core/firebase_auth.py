import requests
from django.conf import settings
from firebase_admin import auth


FIREBASE_SIGNIN_URL = (
    "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
)


def cadastrar_firebase(email, senha, nome):
    usuario_firebase = auth.create_user(
        email=email,
        password=senha,
        display_name=nome,
        email_verified=False,
    )

    return {
        "uid": usuario_firebase.uid,
        "email": usuario_firebase.email,
    }


def autenticar_firebase(email, senha):
    api_key = settings.FIREBASE_API_KEY

    resposta = requests.post(
        f"{FIREBASE_SIGNIN_URL}?key={api_key}",
        json={
            "email": email,
            "password": senha,
            "returnSecureToken": True,
        },
        timeout=15,
    )

    if not resposta.ok:
        return None

    dados = resposta.json()

    return {
        "uid": dados.get("localId"),
        "email": dados.get("email"),
        "id_token": dados.get("idToken"),
    }


def verificar_token_firebase(id_token):
    try:
        return auth.verify_id_token(id_token)
    except Exception:
        return None


def token_tem_google_verificado(dados_token):
    """Aceita login Google direto ou uma conta Google já vinculada."""
    if (
        not isinstance(dados_token, dict)
        or dados_token.get("email_verified") is not True
    ):
        return False

    firebase_claims = dados_token.get("firebase") or {}
    if firebase_claims.get("sign_in_provider") == "google.com":
        return True

    identities = firebase_claims.get("identities") or {}
    return bool(identities.get("google.com"))


def gerar_link_redefinicao(email):
    """Gera o link de redefinição de senha do Firebase para o e-mail informado.

    Devolve ``None`` quando o e-mail não pertence a nenhuma conta — assim o
    fluxo de "esqueci minha senha" não revela quais e-mails existem.
    """
    try:
        return auth.generate_password_reset_link(email)
    except Exception:
        return None


def alterar_senha(uid, nova_senha):
    """Troca a senha do usuário no Firebase Authentication."""
    auth.update_user(uid, password=nova_senha)
