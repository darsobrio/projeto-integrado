# Plataforma de Oportunidades IFPI - Implementation Plan

## Task 1: Criar estrutura base do projeto Django (manage.py + config)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - Criar manage.py
  - Criar pasta de configuração do projeto (ifpi_oportunidades) com __init__.py, settings.py, urls.py, wsgi.py, asgi.py
  - Configurar settings.py com PostgreSQL via dj-database-url, INSTALLED_APPS com os 4 apps, configuração de media e templates
  - Configurar urls.py principal com rotas para cada app
- **Acceptance Criteria Addressed**: AC-1, AC-2, AC-9, AC-10
- **Test Requirements**:
  - `rule` TR-1.1: Arquivo manage.py existe e importa django.core.management corretamente
  - `rule` TR-1.2: settings.py tem DATABASES configurado com dj-database-url, INSTALLED_APPS com users, jobs, properties, core, MEDIA_ROOT/MEDIA_URL definidos
  - `rule` TR-1.3: urls.py principal inclui path() para cada app com include()
- **Notes**: Nome da pasta de configuração será `ifpi_oportunidades`

## Task 2: Criar requirements.txt e .env.example
- **Status**: `pending`
- **Priority**: high
- **Depends On**: None
- **Description**:
  - Criar requirements.txt com Django LTS, psycopg2-binary, dj-database-url, Pillow, python-dotenv, whitenoise
  - Criar .env.example com DATABASE_URL, SECRET_KEY, DEBUG
- **Acceptance Criteria Addressed**: AC-6
- **Test Requirements**:
  - `rule` TR-2.1: requirements.txt lista todas as dependências (Django, psycopg2-binary, dj-database-url, Pillow, python-dotenv, whitenoise)
  - `rule` TR-2.2: .env.example existe com as 3 variáveis

## Task 3: Criar App users (estrutura + models.py + admin.py + urls.py + views.py)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - Criar pasta users com __init__.py, apps.py, admin.py, models.py, views.py, urls.py, migrations/__init__.py
  - Em models.py: CustomUser (AbstractUser) com nome_completo, cpf, data_nascimento, telefone, foto_perfil, endereco, cidade, tipo_usuario (choices CANDIDATO/EMPRESA/PROPRIETARIO); PerfilCandidato com sobre_mim, escolaridade, instituicao, cursos, formacao_academica, diplomas, experiencias, habilidades, idiomas, curriculo_pdf, link_portfolio (OneToOne com CustomUser)
  - Em settings.py: AUTH_USER_MODEL = 'users.CustomUser'
  - Em admin.py: registrar CustomUser e PerfilCandidato
  - Em urls.py e views.py: rotas e views placeholder
- **Acceptance Criteria Addressed**: AC-3, AC-10
- **Test Requirements**:
  - `rule` TR-3.1: models.py contém CustomUser herdando AbstractUser com todos os campos e choices TIPO_USUARIO
  - `rule` TR-3.2: models.py contém PerfilCandidato com OneToOneField para CustomUser e todos os campos
  - `rule` TR-3.3: AUTH_USER_MODEL definido no settings.py

## Task 4: Criar App jobs (estrutura + models.py + admin.py + urls.py + views.py)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - Criar pasta jobs com arquivos padrão Django
  - Em models.py: Vaga com nome_empresa, cnpj, endereco, funcao, descricao, requisitos, salario, beneficios, horario, tipo_contrato (choices), modalidade (choices), qtd_vagas, data_publicacao, prazo, status (Aberta/Fechada), empresa (FK CustomUser); Candidatura com vaga (FK Vaga), candidato (FK CustomUser), data_envio, status_candidatura (choices)
  - Registrar modelos no admin
  - Criar urls.py e views.py placeholders
- **Acceptance Criteria Addressed**: AC-4
- **Test Requirements**:
  - `rule` TR-4.1: models.py contém Vaga com todos os campos e choices para tipo_contrato, modalidade, status
  - `rule` TR-4.2: models.py contém Candidatura com FKs para Vaga e CustomUser e choices status_candidatura

## Task 5: Criar App properties (estrutura + models.py + admin.py + urls.py + views.py)
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1
- **Description**:
  - Criar pasta properties com arquivos padrão Django
  - Em models.py: Imovel com fotos, endereco, bairro, cidade, valor_aluguel, valor_condominio, quartos, banheiros, garagem, area_m2, mobiliado (bool), aceita_animais (bool), descricao, caracteristicas, regras, contato_proprietario, disponibilidade, proprietario (FK CustomUser)
  - Registrar modelos no admin
  - Criar urls.py e views.py placeholders
- **Acceptance Criteria Addressed**: AC-5
- **Test Requirements**:
  - `rule` TR-5.1: models.py contém Imovel com todos os campos incluindo BooleanFields e FK para CustomUser

## Task 6: Criar App core (estrutura + views.py + urls.py)
- **Status**: `pending`
- **Priority**: medium
- **Depends On**: Task 1
- **Description**:
  - Criar pasta core com arquivos padrão Django
  - Criar views para home, register, login, dashboard (renderizando templates)
  - Criar urls.py com rotas para as views do core
- **Acceptance Criteria Addressed**: AC-1
- **Test Requirements**:
  - `rule` TR-6.1: App core existe com arquivos padrão
  - `rule` TR-6.2: views.py contém view functions para home, register, login, dashboard

## Task 7: Criar diretório de templates e base.html
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 1, Task 6
- **Description**:
  - Criar diretório templates/ na raiz do projeto
  - Criar base.html com Bootstrap 5 CDN, header dinâmico com navegação, bloco content, footer
  - Configurar settings.py TEMPLATES com DIRS apontando para templates/
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `rule` TR-7.1: base.html existe com Bootstrap 5 CDN, header, bloco {% content %}, footer
  - `rule` TR-7.2: settings.py TEMPLATES['DIRS'] inclui BASE_DIR / 'templates'

## Task 8: Criar templates home.html, register.html, login.html
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 7
- **Description**:
  - Criar home.html estendendo base.html: banner de busca para vagas e imóveis, cards de destaque
  - Criar register.html: formulário com seletor de tipo de usuário (Candidato/Empresa/Proprietário)
  - Criar login.html: formulário de login
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `rubric` TR-8.1: Qualidade dos templates; escala 1-5; 1=vazios, 3=sem estilização, 5=completos com Bootstrap responsivo; threshold >= 4

## Task 9: Criar templates jobs_list.html, job_detail.html
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 7
- **Description**:
  - jobs_list.html: barra lateral/topo com filtros (cargo, cidade, faixa salarial, tipo contrato, modalidade), lista de cards de vagas
  - job_detail.html: informações completas da vaga, botão de candidatura
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `rubric` TR-9.1: Qualidade e completude dos templates de vagas; escala 1-5; threshold >= 4

## Task 10: Criar templates properties_list.html, dashboard.html
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Task 7
- **Description**:
  - properties_list.html: filtros (cidade/bairro, preço, quartos, animais, mobiliado), galeria/cards de imóveis
  - dashboard.html: 3 visões condicionais (Candidato: histórico de candidaturas; Empresa: gerenciar vagas; Proprietário: gerenciar imóveis)
- **Acceptance Criteria Addressed**: AC-7
- **Test Requirements**:
  - `rubric` TR-10.1: Qualidade e completude dos templates; escala 1-5; threshold >= 4

## Task 11: Criar README.md com instruções de instalação
- **Status**: `pending`
- **Priority**: high
- **Depends On**: Todos os anteriores
- **Description**:
  - Escrever README.md em português com: pré-requisitos, instalação venv e pip install -r requirements.txt, configuração PostgreSQL, cópia de .env.example para .env, makemigrations + migrate, createsuperuser, runserver
- **Acceptance Criteria Addressed**: AC-8
- **Test Requirements**:
  - `rule` TR-11.1: README.md contém todas as seções: pré-requisitos, instalação, configuração DB, migrações, superusuário, runserver
