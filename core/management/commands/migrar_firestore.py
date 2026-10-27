from firebase_admin import firestore
from core import db
from users.models import CustomUser, PerfilCandidato
from jobs.models import Vaga, Candidatura
from properties.models import Imovel
from django.core.management.base import BaseCommand, CommandError
from decimal import Decimal
from datetime import date, datetime


def converter(valor):
    """Converte valores Django para formatos aceitos pelo Firestore."""

    if isinstance(valor, Decimal):
        return float(valor)

    if isinstance(valor, (date, datetime)):
        return valor.isoformat()

    if hasattr(valor, "name") and hasattr(valor, "storage"):
        return valor.name or None

    return valor


def gravar_colecao(nome, registros, montar_documento, obter_id=None):
    """Grava documentos usando IDs determinísticos para permitir reexecução.

    ``obter_id`` define o ID do documento (por padrão, o ``pk`` do Django).
    Para ``usuarios`` usa-se o ``firebase_uid`` porque é essa a chave que o
    aplicativo utiliza ao ler o documento.
    """

    batch = db.batch()
    quantidade = 0
    total = 0

    for registro in registros.iterator(chunk_size=200):
        documento_id = str(obter_id(registro)) if obter_id else str(registro.pk)
        referencia = db.collection(nome).document(documento_id)

        dados = montar_documento(registro)
        dados["django_id"] = str(registro.pk)

        batch.set(referencia, dados, merge=True)
        quantidade += 1
        total += 1
        if quantidade >= 400:
            batch.commit()
            batch = db.batch()
            quantidade = 0

    if quantidade:
        batch.commit()

    return total


def dados_usuario(usuario):
    return {
        "firebase_uid": usuario.firebase_uid,
        "username": usuario.username,
        "email": usuario.email,
        "nome_completo": usuario.nome_completo,
        "cpf": usuario.cpf,
        "data_nascimento": converter(usuario.data_nascimento),
        "telefone": usuario.telefone,
        "endereco": usuario.endereco,
        "cidade": usuario.cidade,
        "tipo_usuario": usuario.tipo_usuario,
        "is_active": usuario.is_active,
        "is_staff": usuario.is_staff,
        "is_superuser": usuario.is_superuser,
    }


def dados_perfil(perfil):
    campos = [
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
    ]

    dados = {
        campo: getattr(perfil, campo)
        for campo in campos
    }

    dados.update({
        "usuario_id": str(perfil.usuario_id),
        "curriculo_pdf": perfil.curriculo_pdf.name or None,
        "criado_em": converter(perfil.criado_em),
        "atualizado_em": converter(perfil.atualizado_em),
    })

    return dados


def dados_vaga(vaga):
    return {
        "empresa_id": str(vaga.empresa_id),
        "nome_empresa": vaga.nome_empresa,
        "cnpj": vaga.cnpj,
        "endereco": vaga.endereco,
        "funcao": vaga.funcao,
        "descricao": vaga.descricao,
        "requisitos": vaga.requisitos,
        "salario": converter(vaga.salario),
        "beneficios": vaga.beneficios,
        "horario": vaga.horario,
        "tipo_contrato": vaga.tipo_contrato,
        "modalidade": vaga.modalidade,
        "qtd_vagas": vaga.qtd_vagas,
        "data_publicacao": converter(vaga.data_publicacao),
        "prazo": converter(vaga.prazo),
        "status": vaga.status,
    }


def dados_candidatura(candidatura):
    return {
        "vaga_id": str(candidatura.vaga_id),
        "candidato_id": str(candidatura.candidato_id),
        "data_envio": converter(candidatura.data_envio),
        "status_candidatura": candidatura.status_candidatura,
        "observacoes": candidatura.observacoes,
    }


def dados_imovel(imovel):
    return {
        "proprietario_id": str(imovel.proprietario_id),
        "fotos": imovel.fotos.name or None,
        "endereco": imovel.endereco,
        "bairro": imovel.bairro,
        "cidade": imovel.cidade,
        "valor_aluguel": converter(imovel.valor_aluguel),
        "valor_condominio": converter(imovel.valor_condominio),
        "quartos": imovel.quartos,
        "banheiros": imovel.banheiros,
        "garagem": imovel.garagem,
        "area_m2": converter(imovel.area_m2),
        "mobiliado": imovel.mobiliado,
        "aceita_animais": imovel.aceita_animais,
        "descricao": imovel.descricao,
        "caracteristicas": imovel.caracteristicas,
        "regras": imovel.regras,
        "contato_proprietario": imovel.contato_proprietario,
        "disponibilidade": converter(imovel.disponibilidade),
        "criado_em": converter(imovel.criado_em),
        "atualizado_em": converter(imovel.atualizado_em),
    }


class Command(BaseCommand):
    help = "Copia os dados do Django para o Cloud Firestore."

    def handle(self, *args, **options):
        colecoes = [
            (
                "usuarios",
                CustomUser.objects.all(),
                dados_usuario,
                lambda usuario: usuario.firebase_uid or usuario.pk,
            ),
            (
                "perfis_candidato",
                PerfilCandidato.objects.select_related("usuario").all(),
                dados_perfil,
            ),
            (
                "vagas",
                Vaga.objects.all(),
                dados_vaga,
            ),
            (
                "candidaturas",
                Candidatura.objects.all(),
                dados_candidatura,
            ),
            (
                "imoveis",
                Imovel.objects.all(),
                dados_imovel,
            ),
        ]

        try:
            for nome, registros, montar, *extra in colecoes:
                total = gravar_colecao(
                    nome,
                    registros,
                    montar,
                    extra[0] if extra else None,
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"{nome}: {total} documentos gravados."))
        except Exception as exc:
            raise CommandError(f"Falha durante a migração: {exc}") from exc
        self.stdout.write(
            self.style.SUCCESS("Migração concluída. O banco Django foi preservado."))