"""Usuários e perfis de candidato — 100% Firestore.

Este módulo substitui a antiga camada ORM (``users.models``). O documento
``usuarios/{firebase_uid}`` é a única fonte de verdade: a sessão guarda apenas
o ``firebase_uid`` e cada requisição hidrata um objeto :class:`Usuario` a
partir do Firestore.
"""

from datetime import date, datetime

from django.core.files.storage import default_storage
from google.cloud import firestore

from core import db

COLECAO_USUARIOS = "usuarios"
COLECAO_PERFIS = "perfis_candidato"

ESCOLARIDADE_CHOICES = [
    ("fundamental", "Ensino Fundamental"),
    ("medio", "Ensino Médio"),
    ("tecnico", "Curso Técnico"),
    ("superior", "Ensino Superior"),
    ("pos", "Pós-Graduação"),
]

TIPO_USUARIO_CHOICES = [
    ("candidato", "Candidato"),
    ("empresa", "Empresa"),
    ("proprietario", "Proprietário"),
]

CAMPOS_USUARIO = (
    "email",
    "username",
    "nome_completo",
    "tipo_usuario",
    "cidade",
    "telefone",
    "cpf",
    "endereco",
    "data_nascimento",
    "foto_perfil",
    "verificado",
    "is_active",
    "is_staff",
    "is_superuser",
)

CAMPOS_PERFIL = (
    "sobre_mim",
    "escolaridade",
    "instituicao",
    "cursos",
    "formacao_academica",
    "diplomas",
    "experiencias",
    "habilidades",
    "idiomas",
    "link_portfolio",
    "curriculo_pdf",
)


class ArquivoRemoto:
    """Arquivo guardado no storage (disco local) referenciado pelo Firestore.

    O Firestore guarda só o caminho do arquivo; a URL é resolvida na leitura,
    mantendo a mesma interface (``.url``) usada pelos templates.
    """

    def __init__(self, nome=None, url=None):
        self.name = (nome or "").strip()

        if url:
            self.url = url
        elif self.name:
            try:
                self.url = default_storage.url(self.name)
            except Exception:
                self.url = ""
        else:
            self.url = ""

    def __bool__(self):
        return bool(self.name)

    def __str__(self):
        return self.url


def arquivo_do_campo(nome, url=None):
    """Monta um :class:`ArquivoRemoto` a partir dos campos do documento."""
    nome = str(nome or "").strip()
    url = str(url or "").strip()

    if not nome and not url:
        return None

    # Documentos antigos guardavam apenas a URL pronta.
    if nome and not url and (nome.startswith("http") or nome.startswith("/")):
        nome, url = "", nome

    return ArquivoRemoto(nome, url)


def _para_firestore(valor):
    """Converte datas para texto ISO, formato aceito sem ambiguidade."""
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    return valor


def _para_data(valor):
    """Converte o texto ISO guardado no Firestore de volta para ``date``."""
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor or "").strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


class Usuario:
    """Objeto de usuário hidratado do Firestore.

    Imita os atributos usados pelo restante do projeto (``pk``,
    ``is_authenticated``, ``tipo_usuario``, ``firebase_uid``...) para que as
    views continuem simples.
    """

    ESCOLARIDADE_CHOICES = ESCOLARIDADE_CHOICES
    TIPO_USUARIO_CHOICES = TIPO_USUARIO_CHOICES

    is_authenticated = True
    is_anonymous = False

    def __init__(self, uid, dados=None):
        self.firebase_uid = str(uid)
        # Id numérico que a conta tinha no antigo banco local (só para
        # localizar documentos antigos do Firestore).
        self.id_antigo = None
        self.email = ""
        self.username = ""
        self.nome_completo = ""
        self.tipo_usuario = "candidato"
        self.cidade = None
        self.telefone = None
        self.cpf = None
        self.endereco = None
        self.data_nascimento = None
        self.foto_perfil = None
        self.verificado = False
        self.is_active = True
        self.is_staff = False
        self.is_superuser = False

        self._aplicar(dados or {})

    def _aplicar(self, dados):
        for campo, valor in dados.items():
            if campo == "id_antigo":
                self.id_antigo = str(valor)
                continue
            if campo not in CAMPOS_USUARIO:
                continue
            if campo == "data_nascimento":
                valor = _para_data(valor)
            elif campo == "foto_perfil":
                valor = arquivo_do_campo(valor or dados.get("foto_url"))
            setattr(self, campo, valor)

    @property
    def pk(self):
        return self.firebase_uid

    @property
    def id(self):
        return self.firebase_uid

    def get_full_name(self):
        return self.nome_completo or self.email

    def get_short_name(self):
        base = self.nome_completo or self.email or ""
        return base.split()[0] if base.split() else ""

    def save(self, **_kwargs):
        salvar_usuario(self)

    def delete(self, **_kwargs):
        excluir_usuario(self.firebase_uid)

    def __str__(self):
        return self.email or self.firebase_uid


class AnonymousUser:
    """Visitante sem sessão — mantém a mesma interface de :class:`Usuario`."""

    pk = None
    id = None
    firebase_uid = None
    username = ""
    email = ""
    nome_completo = ""
    tipo_usuario = None
    cidade = None
    telefone = None
    cpf = None
    endereco = None
    data_nascimento = None
    foto_perfil = None
    verificado = False
    is_active = False
    is_staff = False
    is_superuser = False
    is_authenticated = False
    is_anonymous = True

    def __str__(self):
        return "Anônimo"


class PerfilCandidato:
    """Perfil profissional de um candidato (``perfis_candidato/{uid}``)."""

    def __init__(self, uid, dados=None):
        self.firebase_uid = str(uid)
        self.sobre_mim = None
        self.escolaridade = None
        self.instituicao = None
        self.cursos = None
        self.formacao_academica = None
        self.diplomas = None
        self.experiencias = None
        self.habilidades = None
        self.idiomas = None
        self.link_portfolio = None
        self.curriculo_pdf = None

        for campo, valor in (dados or {}).items():
            if campo in CAMPOS_PERFIL:
                if campo == "curriculo_pdf":
                    valor = arquivo_do_campo(valor, dados.get("curriculo_url"))
                setattr(self, campo, valor)

    @property
    def pk(self):
        return self.firebase_uid

    def save(self, **_kwargs):
        salvar_perfil(self)

    def delete(self, **_kwargs):
        db.collection(COLECAO_PERFIS).document(self.firebase_uid).delete()


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------


def _doc_usuario(uid):
    return db.collection(COLECAO_USUARIOS).document(str(uid))


def _montar_usuario(documento):
    if not documento.exists:
        return None
    return Usuario(documento.id, documento.to_dict() or {})


def obter_usuario(uid):
    """Busca um usuário pelo ``firebase_uid``."""
    uid = str(uid or "").strip()

    if not uid:
        return None

    return _montar_usuario(_doc_usuario(uid).get())


def obter_usuario_por_identificador(valor):
    """Busca pelo ``firebase_uid`` ou pelo id numérico usado antigamente."""
    valor = str(valor or "").strip()

    if not valor:
        return None

    usuario = obter_usuario(valor)

    if usuario is not None:
        return usuario

    for documento in db.collection(COLECAO_USUARIOS).stream():
        dados = documento.to_dict() or {}
        if str(dados.get("id_antigo") or "") == valor:
            return Usuario(documento.id, dados)

    return None


def listar_usuarios():
    """Todos os usuários cadastrados."""
    return [
        Usuario(documento.id, documento.to_dict() or {})
        for documento in db.collection(COLECAO_USUARIOS).stream()
    ]


def obter_usuarios(uids):
    """Devolve ``{firebase_uid: Usuario}`` para os uids informados."""
    alvo = {str(uid) for uid in uids if uid}

    if not alvo:
        return {}

    return {
        documento.id: Usuario(documento.id, documento.to_dict() or {})
        for documento in db.collection(COLECAO_USUARIOS).stream()
        if documento.id in alvo
    }


def obter_perfis(uids):
    """Devolve ``{firebase_uid: PerfilCandidato}`` para os uids informados."""
    alvo = {str(uid) for uid in uids if uid}

    if not alvo:
        return {}

    return {
        documento.id: PerfilCandidato(documento.id, documento.to_dict() or {})
        for documento in db.collection(COLECAO_PERFIS).stream()
        if documento.id in alvo
    }


def contar_usuarios():
    return sum(1 for _ in db.collection(COLECAO_USUARIOS).stream())


def existe_email(email):
    """Diz se o e-mail já pertence a alguma conta."""
    email = (email or "").strip().lower()

    if not email:
        return False

    return any(
        str((documento.to_dict() or {}).get("email") or "").strip().lower()
        == email
        for documento in db.collection(COLECAO_USUARIOS).stream()
    )


def existe_cpf(cpf):
    """Diz se o CPF/CNPJ já pertence a alguma conta."""
    cpf = (cpf or "").strip()

    if not cpf:
        return False

    return any(
        str((documento.to_dict() or {}).get("cpf") or "") == cpf
        for documento in db.collection(COLECAO_USUARIOS).stream()
    )


# ---------------------------------------------------------------------------
# Escrita
# ---------------------------------------------------------------------------


def salvar_usuario(usuario):
    """Grava (ou atualiza) o documento do usuário no Firestore."""
    uid = str(getattr(usuario, "firebase_uid", "") or "").strip()

    if not uid:
        raise ValueError("O usuário não possui um UID do Firebase.")

    dados = {
        campo: _para_firestore(getattr(usuario, campo, None))
        for campo in CAMPOS_USUARIO
        if campo != "foto_perfil"
    }

    foto = getattr(usuario, "foto_perfil", None)

    if isinstance(foto, ArquivoRemoto):
        dados["foto_perfil"] = foto.name or None
        dados["foto_url"] = foto.url or None
    else:
        dados["foto_perfil"] = None
        dados["foto_url"] = None

    dados["firebase_uid"] = uid
    dados["atualizado_em"] = firestore.SERVER_TIMESTAMP

    if getattr(usuario, "id_antigo", None):
        dados["id_antigo"] = str(usuario.id_antigo)

    _doc_usuario(uid).set(dados, merge=True)


def criar_usuario(
    *,
    firebase_uid,
    email,
    nome_completo="",
    tipo_usuario="candidato",
    username="",
    cidade=None,
    telefone=None,
    cpf=None,
    data_nascimento=None,
):
    """Cria um usuário no Firestore (a credencial fica no Firebase Auth)."""
    usuario = Usuario(firebase_uid)
    usuario.email = email
    usuario.username = username or email
    usuario.nome_completo = nome_completo
    usuario.tipo_usuario = tipo_usuario
    usuario.cidade = cidade
    usuario.telefone = telefone
    usuario.cpf = cpf
    usuario.data_nascimento = data_nascimento
    salvar_usuario(usuario)
    return usuario


def definir_verificado(uid, verificado=True):
    """Liga/desliga o selo de verificação de uma conta."""
    uid = str(uid or "").strip()

    if not uid:
        return False

    documento = _doc_usuario(uid).get()

    if not documento.exists:
        return False

    _doc_usuario(uid).update({"verificado": bool(verificado)})
    return True


def excluir_usuario(uid):
    """Remove o usuário e o perfil dele do Firestore."""
    uid = str(uid or "").strip()

    if not uid:
        return

    _doc_usuario(uid).delete()
    db.collection(COLECAO_PERFIS).document(uid).delete()


# ---------------------------------------------------------------------------
# Perfil do candidato
# ---------------------------------------------------------------------------


def obter_perfil(uid, criar=False):
    """Carrega o perfil profissional de um candidato."""
    uid = str(uid or "").strip()

    if not uid:
        return None

    documento = db.collection(COLECAO_PERFIS).document(uid).get()

    if documento.exists:
        return PerfilCandidato(uid, documento.to_dict() or {})

    if not criar:
        return None

    perfil = PerfilCandidato(uid)
    perfil.save()
    return perfil


def salvar_perfil(perfil):
    """Grava (ou atualiza) o perfil profissional no Firestore."""
    uid = str(getattr(perfil, "firebase_uid", "") or "").strip()

    if not uid:
        raise ValueError("O perfil não está vinculado a um usuário.")

    referencia = db.collection(COLECAO_PERFIS).document(uid)
    dados = {
        campo: getattr(perfil, campo, None)
        for campo in CAMPOS_PERFIL
        if campo != "curriculo_pdf"
    }

    curriculo = getattr(perfil, "curriculo_pdf", None)

    if isinstance(curriculo, ArquivoRemoto):
        dados["curriculo_pdf"] = curriculo.name or None
        dados["curriculo_url"] = curriculo.url or None
    else:
        dados["curriculo_pdf"] = None
        dados["curriculo_url"] = None

    dados["atualizado_em"] = firestore.SERVER_TIMESTAMP

    if not referencia.get().exists:
        dados["criado_em"] = firestore.SERVER_TIMESTAMP

    referencia.set(dados, merge=True)
