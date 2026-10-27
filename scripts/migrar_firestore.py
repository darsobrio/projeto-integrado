import os
from datetime import date, datetime
from decimal import Decimal
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "ifpi_oportunidades.settings",
)

import django
django.setup()

from django.db.models import Model
from django.utils import timezone

from core import db
from users.models import CustomUser, PerfilCandidato
from jobs.models import Vaga, Candidatura
from properties.models import Imovel


def converter(valor):
    if isinstance(valor, Model):
        return valor.pk

    if isinstance(valor, Decimal):
        return str(valor)

    if isinstance(valor, datetime):
        if timezone.is_aware(valor):
            return valor

        return timezone.make_aware(valor)

    if isinstance(valor, date):
        return valor.isoformat()

    if isinstance(valor, dict):
        return {str(k): converter(v) for k, v in valor.items()}

    if isinstance(valor, (list, tuple)):
        return [converter(v) for v in valor]

    return valor


def campos_do_modelo(objeto):
    dados = {}

    for campo in objeto._meta.concrete_fields:
        nome = campo.name
        valor = getattr(objeto, nome)

        # Campos de relacionamento armazenam o ID do registro relacionado.
        if campo.is_relation:
            dados[nome + "_id"] = converter(valor)
        elif hasattr(campo, "attname") and campo.attname != nome:
            continue
        elif campo.get_internal_type() in (
            "ImageField",
            "FileField",
        ):
            dados[nome] = valor.name if valor else None
        else:
            dados[nome] = converter(valor)

    dados["django_id"] = objeto.pk
    dados["migrado_em"] = timezone.now()

    return dados


def migrar_modelo(modelo, colecao, obter_id=None):
    """Copia um modelo do Django para a coleção do Firestore.

    ``obter_id`` define o ID do documento (por padrão, o ``pk`` do Django).
    Para ``usuarios`` usa-se o ``firebase_uid``, que é a chave lida pelo
    aplicativo.
    """

    total = 0

    for objeto in modelo.objects.all().iterator():
        dados = campos_do_modelo(objeto)

        documento_id = str(obter_id(objeto)) if obter_id else str(objeto.pk)

        db.collection(colecao).document(documento_id).set(
            dados,
            merge=True,
        )

        total += 1

    print(f"{colecao}: {total} registros copiados.")
    return total


def main():
    print("Iniciando cópia do Django para o Firestore...")
    print("O banco SQLite não será alterado.")

    totais_esperados = {
        "usuarios": CustomUser.objects.count(),
        "perfis_candidato": PerfilCandidato.objects.count(),
        "vagas": Vaga.objects.count(),
        "candidaturas": Candidatura.objects.count(),
        "imoveis": Imovel.objects.count(),
    }

    totais_copiados = {
        "usuarios": migrar_modelo(
            CustomUser,
            "usuarios",
            lambda usuario: usuario.firebase_uid or usuario.pk,
        ),
        "perfis_candidato": migrar_modelo(
            PerfilCandidato, "perfis_candidato"
        ),
        "vagas": migrar_modelo(Vaga, "vagas"),
        "candidaturas": migrar_modelo(
            Candidatura, "candidaturas"
        ),
        "imoveis": migrar_modelo(Imovel, "imoveis"),
    }

    print("\nResumo:")
    for colecao, esperado in totais_esperados.items():
        copiado = totais_copiados[colecao]
        situacao = "OK" if esperado == copiado else "DIVERGÊNCIA"
        print(
            f"{colecao}: esperado={esperado}, "
            f"copiado={copiado} — {situacao}"
        )

    print(
        "\nCópia concluída. Confira os documentos no Firestore "
        "antes de realizar qualquer mudança no aplicativo."
    )


if __name__ == "__main__":
    main()
