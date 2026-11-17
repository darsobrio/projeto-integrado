"""Funções auxiliares compartilhadas entre os apps do Oportunet."""

from datetime import date, datetime

from django.utils import timezone

# Rótulos legíveis para os valores gravados no Firestore
TIPO_CONTRATO_LABELS = {
    'clt': 'CLT',
    'temporario': 'Temporário',
    'estagio': 'Estágio',
    'jovem_aprendiz': 'Jovem Aprendiz',
    'freelancer': 'Freelancer',
}

MODALIDADE_LABELS = {
    'presencial': 'Presencial',
    'hibrido': 'Híbrido',
    'remoto': 'Remoto',
}

STATUS_VAGA_LABELS = {
    'aberta': 'Aberta',
    'fechada': 'Fechada',
}

STATUS_CANDIDATURA_LABELS = {
    'enviada': 'Enviada',
    'em_analise': 'Em análise',
    'entrevista': 'Entrevista',
    'aprovado': 'Aprovado',
    'recusado': 'Recusado',
}

# Opções usadas nos formulários de publicação
TIPO_CONTRATO_CHOICES = list(TIPO_CONTRATO_LABELS.items())
MODALIDADE_CHOICES = list(MODALIDADE_LABELS.items())


def rotulo(mapa, valor, padrao=''):
    """Devolve o rótulo amigável de um valor, aceitando o próprio rótulo."""
    if valor in (None, ''):
        return padrao
    chave = str(valor).strip().lower()
    return mapa.get(chave, str(valor))


def formatar_moeda(valor):
    """Formata um número como moeda brasileira (ex.: 2500 -> 2.500,00)."""
    if valor in (None, ''):
        return None

    if isinstance(valor, (int, float)):
        numero = float(valor)
    else:
        texto = str(valor).strip()
        try:
            numero = float(texto)
        except ValueError:
            try:
                numero = float(texto.replace('.', '').replace(',', '.'))
            except ValueError:
                return texto

    return f'{numero:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def formatar_data(valor):
    """Formata datas/datetimes como dd/mm/aaaa.

    Aceita objetos date/datetime, timestamps do Firestore já convertidos e
    strings ISO (ex.: "2026-11-30" ou "2026-11-30T12:00:00").

    Datetimes com fuso são convertidos para o fuso local antes de formatar,
    evitando exibir o dia errado em horários próximos da meia-noite.
    """
    if not valor:
        return ''

    if isinstance(valor, datetime):
        if timezone.is_aware(valor):
            valor = timezone.localtime(valor)
        return valor.strftime('%d/%m/%Y')

    if isinstance(valor, date):
        return valor.strftime('%d/%m/%Y')

    texto = str(valor).strip()
    if not texto:
        return ''

    try:
        convertido = datetime.fromisoformat(texto.replace('Z', '+00:00'))
    except ValueError:
        return texto

    if timezone.is_aware(convertido):
        convertido = timezone.localtime(convertido)

    return convertido.strftime('%d/%m/%Y')


def chave_data(valor):
    """Normaliza datas/timestamps (Firestore, ISO ou date) em número ordenável."""
    if isinstance(valor, datetime):
        return valor.timestamp()

    if isinstance(valor, date):
        return datetime(valor.year, valor.month, valor.day).timestamp()

    texto = str(valor or '').strip()

    if not texto:
        return 0.0

    try:
        return datetime.fromisoformat(texto.replace('Z', '+00:00')).timestamp()
    except ValueError:
        return 0.0


def numero_decimal(valor):
    """Converte um valor de formulário em float, aceitando vírgula."""
    if valor in (None, ''):
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    if ',' in texto:
        texto = texto.replace('.', '').replace(',', '.')
    try:
        return float(texto)
    except ValueError:
        return None


def numero_inteiro(valor, padrao=0):
    """Converte um valor de formulário em inteiro."""
    numero = numero_decimal(valor)
    if numero is None:
        return padrao
    return int(numero)


def somente_digitos(valor):
    """Remove tudo que não for dígito (pontos, traços, barras)."""
    return ''.join(caractere for caractere in str(valor or '') if caractere.isdigit())


def validar_cpf(valor):
    """Valida um CPF pelo dígito verificador (rejeita sequências repetidas)."""
    cpf = somente_digitos(valor)

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11
        if digito == 10:
            digito = 0
        if digito != int(cpf[tamanho]):
            return False

    return True


def validar_cnpj(valor):
    """Valida um CNPJ pelo dígito verificador (rejeita sequências repetidas)."""
    cnpj = somente_digitos(valor)

    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    for pesos, posicao in ((pesos_1, 12), (pesos_2, 13)):
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(posicao))
        digito = soma % 11
        digito = 0 if digito < 2 else 11 - digito
        if digito != int(cnpj[posicao]):
            return False

    return True


def validar_cpf_cnpj(valor):
    """Valida CPF (11 dígitos) ou CNPJ (14 dígitos). Vazio é aceito (opcional)."""
    digitos = somente_digitos(valor)

    if not digitos:
        return True

    if len(digitos) == 11:
        return validar_cpf(digitos)

    if len(digitos) == 14:
        return validar_cnpj(digitos)

    return False
