# Plataforma de Oportunidades IFPI - Independent Review

- [x] CP-R1: Estrutura de projeto Django completa com 4 apps (users, jobs, properties, core) e configuração base
  - **Type**: `rule`
  - **Covers**: AC-1, AC-2, AC-9
  - **Evidence**: Diretório listado em LS contém: manage.py, ifpi_oportunidades (settings/urls/wsgi/asgi), users, jobs, properties, core — cada app com models, views, urls, admin, apps, migrations/__init__.py. settings.py tem INSTALLED_APPS com os 4 apps, DATABASES com dj-database-url (PostgreSQL), MEDIA_ROOT/MEDIA_URL, AUTH_USER_MODEL, TEMPLATES com DIRS apontando para templates/. urls.py principal inclui todos os apps via include().

- [x] CP-R2: Models dos apps users, jobs e properties completos com todos os campos, choices e relacionamentos
  - **Type**: `rule`
  - **Covers**: AC-3, AC-4, AC-5, AC-10
  - **Evidence**: Leitura dos models:
    - users/models.py: CustomUser (AbstractUser) com nome_completo, cpf, data_nascimento, email, telefone, foto_perfil (ImageField), endereco, cidade, tipo_usuario (choices CANDIDATO/EMPRESA/PROPRIETARIO). PerfilCandidato com OneToOne para CustomUser + sobre_mim, escolaridade, instituicao, cursos, formacao_academica, diplomas, experiencias, habilidades, idiomas, curriculo_pdf (FileField), link_portfolio.
    - jobs/models.py: Vaga com nome_empresa, cnpj, endereco, funcao, descricao, requisitos, salario, beneficios, horario, tipo_contrato (5 choices), modalidade (3), qtd_vagas, data_publicacao, prazo, status (Aberta/Fechada), FK empresa. Candidatura com FK vaga+candidato, data_envio, status_candidatura (5 choices), unique_together.
    - properties/models.py: Imovel com fotos (ImageField), endereco, bairro, cidade, valor_aluguel/condominio, quartos, banheiros, garagem, area_m2, mobiliado (bool), aceita_animais (bool), descricao, caracteristicas, regras, contato_proprietario, disponibilidade, FK proprietario.

- [x] CP-R3: requirements.txt com todas as dependências essenciais
  - **Type**: `rule`
  - **Covers**: AC-6
  - **Evidence**: requirements.txt contém: Django>=4.2,<5.0 (LTS), psycopg2-binary>=2.9.9, dj-database-url>=2.1.0, Pillow>=10.0.0, python-dotenv>=1.0.0, whitenoise>=6.6.0.

- [x] CP-R4: README.md completo com instruções passo a passo
  - **Type**: `rule`
  - **Covers**: AC-8
  - **Evidence**: README.md contém: Pré-requisitos (Python, PostgreSQL), Passo 1 (clone), Passo 2 (criar DB SQL), Passo 3 (venv), Passo 4 (pip install -r requirements.txt), Passo 5 (.env.example → .env com DATABASE_URL, SECRET_KEY, DEBUG), Passo 6 (makemigrations + migrate), Passo 7 (createsuperuser), Passo 9 (runserver). Inclui seção Troubleshooting e URLs principais.

- [x] CP-R5: Arquivo .env.example criado com variáveis essenciais
  - **Type**: `rule`
  - **Covers**: AC-2, AC-8
  - **Evidence**: .env.example contém DATABASE_URL, SECRET_KEY, DEBUG.

- [x] CP-U1: Qualidade e completude dos templates HTML responsivos
  - **Type**: `rubric`
  - **Covers**: AC-7
  - **Scale**: 1-5
  - **Anchors**: 1 = Falta mais da metade; 3 = Existem mas sem estilização; 5 = Completos, Bootstrap 5, responsivos, com todas as seções requisitadas
  - **Pass Threshold**: >= 4
  - **Score**: 5
  - **Rationale**: Todos os 8 templates existem (base, home, login, register, jobs_list, job_detail, properties_list, dashboard). base.html tem Bootstrap 5.3 CDN + Bootstrap Icons, navegação dinâmica (header autenticado/não autenticado), {% block content %}, footer. home.html com hero/busca rápida, vagas em destaque, imóveis recentes, CTAs. register.html com seletor de perfil (3 opções visuais) e formulário completo. login.html completo com lembrar-me, esqueci senha, login social. jobs_list com sidebar/offcanvas de filtros (cargo, cidade, salário, tipo contrato, modalidade) + cards. job_detail com informações completas + sidebar de candidatura e progresso. properties_list com filtros (local, preço, quartos, switches mobiliado/pet) + galeria de cards. dashboard com 3 visões condicionais baseadas em usuario.tipo_usuario (Candidato com stats, tabela, completude, recomendações; Empresa com estatísticas e tabela de vagas; Proprietário com estatísticas e tabela de imóveis). Todos usam grid responsivo do Bootstrap.
  - **Evidence**: Leitura direta dos 8 arquivos em templates/.

## Review History

### Review R1
- **Result**: `pass`
- **Evidence**: Todos os 6 checkpoints (5 rules + 1 rubric de score 5/5) passaram. Árvore de diretórios completa, modelos com todos os campos e relacionamentos corretos, settings.py com PostgreSQL + AUTH_USER_MODEL + MEDIA, requirements.txt com 6 dependências essenciais, README e .env.example completos, 8 templates responsivos com Bootstrap 5 e conteúdo substancial para todas as páginas essenciais.
