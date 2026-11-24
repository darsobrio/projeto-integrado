import os
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-chave-padrao-dev')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")

FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_AUTH_DOMAIN = os.getenv(
    "FIREBASE_AUTH_DOMAIN",
    f"{FIREBASE_PROJECT_ID}.firebaseapp.com" if FIREBASE_PROJECT_ID else "",
)
FIREBASE_WEB_APP_ID = os.getenv("FIREBASE_WEB_APP_ID", "")


def _lista_de_env(nome):
    """Lê uma variável de ambiente com valores separados por vírgula."""
    return [item.strip() for item in os.getenv(nome, '').split(',') if item.strip()]


# Em desenvolvimento libera tudo; em produção é obrigatório informar os hosts.
ALLOWED_HOSTS = _lista_de_env('ALLOWED_HOSTS') or (['*'] if DEBUG else [])

CSRF_TRUSTED_ORIGINS = _lista_de_env('CSRF_TRUSTED_ORIGINS')

INSTALLED_APPS = [
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'users',
    'jobs',
    'properties',
    'core',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'core.middleware.SessaoFirebaseMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ifpi_oportunidades.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'core.context_processors.usuario',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.notificacoes',
            ],
        },
    },
]

WSGI_APPLICATION = 'ifpi_oportunidades.wsgi.application'
ASGI_APPLICATION = 'ifpi_oportunidades.asgi.application'

# ---------------------------------------------------------------------------
# Armazenamento de dados
# ---------------------------------------------------------------------------
# Todo o dado da aplicação vive no Firebase (Firestore + Firebase Auth).
# Não há banco local: o projeto roda sem SQLite/PostgreSQL.
DATABASES = {}

# A sessão é guardada em cookie assinado (nada é gravado no servidor).
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Fortaleza'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ---------------------------------------------------------------------------
# Armazenamento de arquivos (uploads)
# ---------------------------------------------------------------------------
# Os dados ficam no Firebase; apenas os ARQUIVOS enviados (foto de perfil,
# currículo, fotos de imóvel, comprovantes) ficam no disco do servidor, em
# MEDIA_ROOT. O Firebase Storage exige o plano pago, por isso não é usado.
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# API REST (Django REST Framework)
# ---------------------------------------------------------------------------
# A paginação é feita no serializer de resposta (core.pagination), então aqui
# ficam apenas permissão e renderização. A API é somente leitura para dados
# públicos; candidaturas exigem usuário autenticado na própria view.
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'core.auth.AutenticacaoFirebase',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'UNAUTHENTICATED_USER': 'core.user.AnonymousUser',
}

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/?logged_out=1'

# ---------------------------------------------------------------------------
# E-mail
# ---------------------------------------------------------------------------
# Em desenvolvimento o padrão é imprimir o e-mail no terminal (console).
# Em produção, defina EMAIL_BACKEND=smtp e as variáveis SMTP no ambiente.
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
    if DEBUG
    else 'django.core.mail.backends.smtp.EmailBackend',
)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'Oportunet <nao-responder@oportunet.local>')

# ---------------------------------------------------------------------------
# Produção
# ---------------------------------------------------------------------------
# Estas travas só valem com DEBUG=False, para não atrapalhar o desenvolvimento.
if not DEBUG:
    if SECRET_KEY.startswith('django-insecure'):
        raise ImproperlyConfigured(
            'Defina uma SECRET_KEY segura no ambiente antes de rodar em produção.'
        )

    if not ALLOWED_HOSTS:
        raise ImproperlyConfigured(
            'Defina ALLOWED_HOSTS com o(s) domínio(s) do site em produção.'
        )

    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True') == 'True'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
