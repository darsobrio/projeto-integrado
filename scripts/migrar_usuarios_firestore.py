"""Migra os usuários do antigo SQLite para o Firestore.

Roda de forma independente do Django (lê o ``db.sqlite3`` direto com
``sqlite3``), então continua funcionando agora que o ORM foi removido.

O que faz:
1. Copia cada linha de ``users_customuser`` para ``usuarios/{firebase_uid}``,
   guardando o id numérico antigo no campo ``id_antigo``.
2. Copia ``users_perfilcandidato`` para ``perfis_candidato/{firebase_uid}``.
3. Reescreve as referências antigas (``empresa_id``, ``proprietario_id``,
   ``candidato_id``...) que apontavam para o id numérico, trocando pelo
   ``firebase_uid`` correspondente.

Uso:
    .\\.venv\\Scripts\\python.exe scripts\\migrar_usuarios_firestore.py
"""

import sqlite3
import sys
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

BASE_DIR = Path(__file__).resolve().parent.parent
BANCO = BASE_DIR / "db.sqlite3"
CREDENCIAL = BASE_DIR / "serviceAccountKey.json"

COLECAO_USUARIOS = "usuarios"
COLECAO_PERFIS = "perfis_candidato"

# Campos que podem guardar o id de um usuário em outros documentos.
CAMPOS_REFERENCIA = (
    "usuario_id",
    "empresa_id",
    "proprietario_id",
    "candidato_id",
    "remetente_id",
    "destinatario_id",
    "denunciante_id",
    "autor_id",
)


def iniciar_firestore():
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(str(CREDENCIAL)))

    return firestore.client()


def ler_usuarios(conexao):
    conexao.row_factory = sqlite3.Row
    linhas = conexao.execute("SELECT * FROM users_customuser").fetchall()

    return [dict(linha) for linha in linhas]


def ler_perfis(conexao):
    conexao.row_factory = sqlite3.Row
    linhas = conexao.execute("SELECT * FROM users_perfilcandidato").fetchall()

    return [dict(linha) for linha in linhas]


def montar_documento_usuario(linha):
    return {
        "firebase_uid": linha["firebase_uid"],
        "id_antigo": str(linha["id"]),
        "email": linha["email"] or "",
        "username": linha["username"] or linha["email"] or "",
        "nome_completo": linha["nome_completo"] or "",
        "tipo_usuario": linha["tipo_usuario"] or "candidato",
        "cidade": linha["cidade"],
        "telefone": linha["telefone"],
        "cpf": linha["cpf"],
        "endereco": linha["endereco"],
        "data_nascimento": linha["data_nascimento"],
        "foto_perfil": linha["foto_perfil"] or None,
        "foto_url": None,
        "verificado": bool(linha["verificado"]),
        "is_active": bool(linha["is_active"]),
        "is_staff": bool(linha["is_staff"]),
        "is_superuser": bool(linha["is_superuser"]),
        "origem": "sqlite",
        "atualizado_em": firestore.SERVER_TIMESTAMP,
    }


def montar_documento_perfil(linha):
    return {
        "sobre_mim": linha["sobre_mim"],
        "escolaridade": linha["escolaridade"],
        "instituicao": linha["instituicao"],
        "cursos": linha["cursos"],
        "formacao_academica": linha["formacao_academica"],
        "diplomas": linha["diplomas"],
        "experiencias": linha["experiencias"],
        "habilidades": linha["habilidades"],
        "idiomas": linha["idiomas"],
        "link_portfolio": linha["link_portfolio"],
        "curriculo_pdf": linha["curriculo_pdf"] or None,
        "curriculo_url": None,
        "atualizado_em": firestore.SERVER_TIMESTAMP,
    }


def reescrever_referencias(banco, mapa_ids):
    """Troca ids numéricos antigos pelo ``firebase_uid`` nos documentos."""
    total = 0

    for colecao in banco.collections():
        for documento in colecao.stream():
            dados = documento.to_dict() or {}
            alteracoes = {}

            for campo in CAMPOS_REFERENCIA:
                valor = dados.get(campo)

                if valor is None:
                    continue

                uid = mapa_ids.get(str(valor).strip())

                if uid and uid != valor:
                    alteracoes[campo] = uid

            if alteracoes:
                colecao.document(documento.id).update(alteracoes)
                total += len(alteracoes)
                print(
                    f"  ~ {colecao.id}/{documento.id}: "
                    + ", ".join(f"{c} -> {v}" for c, v in alteracoes.items())
                )

    return total


def main():
    if not BANCO.exists():
        print(f"Banco não encontrado: {BANCO}")
        return 1

    banco = iniciar_firestore()
    conexao = sqlite3.connect(BANCO)

    usuarios = ler_usuarios(conexao)
    perfis = ler_perfis(conexao)
    mapa_ids = {str(u["id"]): u["firebase_uid"] for u in usuarios}

    print(f"Usuários no SQLite: {len(usuarios)}")
    print(f"Perfis no SQLite:   {len(perfis)}")

    for usuario in usuarios:
        uid = usuario["firebase_uid"]

        if not uid:
            print(f"  ! id {usuario['id']} sem firebase_uid — ignorado")
            continue

        banco.collection(COLECAO_USUARIOS).document(uid).set(
            montar_documento_usuario(usuario), merge=True
        )
        print(f"  + usuarios/{uid}  ({usuario['email']})")

    for perfil in perfis:
        uid = mapa_ids.get(str(perfil["usuario_id"]))

        if not uid:
            print(f"  ! perfil {perfil['id']} sem usuário — ignorado")
            continue

        banco.collection(COLECAO_PERFIS).document(uid).set(
            montar_documento_perfil(perfil), merge=True
        )
        print(f"  + perfis_candidato/{uid}")

    print("\nReescrevendo referências antigas nos demais documentos:")
    total = reescrever_referencias(banco, mapa_ids)

    if total == 0:
        print("  (nenhuma referência numérica encontrada)")

    print(f"\nConcluído. {len(usuarios)} usuários e {len(perfis)} perfis migrados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
