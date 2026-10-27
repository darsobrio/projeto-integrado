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