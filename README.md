# 🏛️ IFPI Oportunidades - Plataforma de Vagas e Imóveis

Plataforma web responsiva desenvolvida como **Projeto Integrador do IFPI Campus Paulistana**, com o objetivo de conectar a comunidade acadêmica e local a oportunidades de **emprego, estágio e moradia** (aluguel de imóveis).

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologia |
|---|---|
| **Backend** | Python 3.8+ + Django 4.2 LTS |
| **Frontend** | HTML5, CSS3, JavaScript + Bootstrap 5.3 (CDN) |
| **Banco de Dados** | PostgreSQL (12+) |
| **Armazenamento (futuro)** | Estrutura preparada para Firebase Storage (campos `FileField` / `ImageField`) |
| **Dependências** | psycopg2-binary, dj-database-url, Pillow, python-dotenv, whitenoise |
| **Controle de Versão** | Git / GitHub |

---

## 📁 Estrutura do Projeto

```
projeto-sem-nome/
├── ifpi_oportunidades/        # 📂 Configurações do projeto Django
│   ├── __init__.py
│   ├── settings.py            # ⚙️ Configurações (PostgreSQL, apps, media, templates)
│   ├── urls.py                # 🔀 Rotas principais
│   ├── wsgi.py / asgi.py
├── users/                     # 👤 App - Gerenciamento de Usuários
│   ├── models.py              # CustomUser + PerfilCandidato
│   ├── admin.py, views.py, urls.py
│   └── migrations/
├── jobs/                      # 💼 App - Vagas e Candidaturas
│   ├── models.py              # Vaga + Candidatura
│   └── ...
├── properties/                # 🏠 App - Imóveis para Aluguel
│   ├── models.py              # Imovel
│   └── ...
├── core/                      # 🧭 App - Páginas Institucionais (Home, Dashboard, Auth)
│   └── views.py (home, login, register, dashboard)
├── templates/                 # 🎨 Templates HTML responsivos
│   ├── base.html
│   ├── home.html
│   ├── login.html / register.html
│   ├── jobs_list.html / job_detail.html
│   ├── properties_list.html
│   └── dashboard.html
├── static/                    # 📦 Arquivos estáticos (CSS/JS locais, se necessário)
├── media/                     # 🖼️ Uploads de usuários (fotos, currículos, imóveis)
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## ✅ Pré-requisitos

Antes de começar, certifique-se de ter instalado em sua máquina:

1. **Python 3.8+** (recomendado 3.10 ou 3.11) — baixe em [python.org/downloads](https://www.python.org/downloads/)
2. **PostgreSQL 12+** instalado e rodando localmente:
   - **Windows:** baixe em [postgresql.org/download/windows](https://www.postgresql.org/download/windows/) (durante a instalação, anote a senha do superusuário `postgres`)
   - **Linux (Debian/Ubuntu):** `sudo apt install postgresql postgresql-contrib`
3. **Pip** (geralmente já vem com o Python) e **venv** (ambiente virtual)
4. (Opcional) **pgAdmin** ou **DBeaver** para gerenciar o banco visualmente.

---

## 🚀 Passo a Passo para Rodar o Projeto

### 1️⃣. Clone / Baixe o projeto

```bash
# Se estiver usando Git
git clone <seu-repositorio>
cd projeto-sem-nome
```

### 2️⃣. Crie um Banco de Dados PostgreSQL

Abra o **pgAdmin** ou o terminal `psql` (SQL Shell) e execute:

```sql
-- Criação do banco
CREATE DATABASE ifpi_oportunidades;

-- (Opcional) Crie um usuário dedicado para a aplicação
CREATE USER ifpi_user WITH PASSWORD 'sua_senha_forte';
GRANT ALL PRIVILEGES ON DATABASE ifpi_oportunidades TO ifpi_user;
ALTER DATABASE ifpi_oportunidades OWNER TO ifpi_user;
```

> 💡 **Anotações importantes:** Anote o **nome do banco**, **usuário** e **senha** — você precisará deles na próxima etapa.

### 3️⃣. Crie e ative um Ambiente Virtual (venv)

```powershell
# Windows (PowerShell / CMD)
python -m venv .venv
.\.venv\Scripts\activate

# Linux / macOS (bash)
python3 -m venv .venv
source .venv/bin/activate
```

Se deu certo, você verá **`(.venv)`** no início do seu prompt.

### 4️⃣. Instale as dependências do projeto

```bash
pip install -r requirements.txt
```

Isso instalará: **Django 4.2 LTS**, **psycopg2-binary**, **dj-database-url**, **Pillow**, **python-dotenv** e **whitenoise**.

### 5️⃣. Configure as variáveis de ambiente (.env)

Copie o arquivo de exemplo e edite com os dados do seu banco:

```powershell
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Abra o arquivo **`.env`** em um editor de texto e preencha:

```dotenv
# .env

# URL de conexão com o PostgreSQL no formato:
# postgres://USUARIO:SENHA@HOST:PORTA/NOME_BANCO
DATABASE_URL=postgres://ifpi_user:sua_senha_forte@localhost:5432/ifpi_oportunidades
# OU, se você usou o usuário padrão postgres:
# DATABASE_URL=postgres://postgres:SUA_SENHA_POSTGRES@localhost:5432/ifpi_oportunidades

# Chave secreta do Django (altere para algo aleatório e longo em produção!)
SECRET_KEY=django-insecure-altere-essa-chave-em-producao-para-algo-seguro-e-longo-12345

# Modo debug: True em desenvolvimento, False em produção
DEBUG=True
```

> ⚠️ **Nunca compartilhe nem envie o arquivo `.env` para o GitHub** (ele já está incluído no `.gitignore`).

### 6️⃣. Rode as migrações do banco de dados

As migrações criarão todas as tabelas (`CustomUser`, `PerfilCandidato`, `Vaga`, `Candidatura`, `Imovel`, etc.):

```bash
# 1. Gere os arquivos de migração dos apps (caso ainda não existam)
python manage.py makemigrations users jobs properties core

# 2. Aplique todas as migrações no PostgreSQL
python manage.py migrate
```

Se aparecer "OK" para todas as migrações, deu tudo certo! 🎉

### 7️⃣. Crie um superusuário (Admin)

Para acessar o painel administrativo do Django em `/admin/`:

```bash
python manage.py createsuperuser
```

Preencha:
- **E-mail:** seu email (ou `admin@ifpi.edu.br`)
- **Username:** ex: `admin`
- **Senha:** uma senha forte
- Confirme a senha.

### 8️⃣. (Opcional) Colete arquivos estáticos

Apenas necessário em produção, mas pode testar:

```bash
python manage.py collectstatic
```

### 9️⃣. Suba o servidor de desenvolvimento local 🚀

```bash
python manage.py runserver
```

Por padrão, o servidor roda em **http://127.0.0.1:8000/** — abra essa URL no seu navegador.

Para rodar em outra porta, ex: `8080`:
```bash
python manage.py runserver 8080
```

---

## 📌 URLs Principais

| Rota | Descrição |
|---|---|
| `/` | 🏠 Página Inicial (Home) |
| `/vagas/` | 💼 Lista de Vagas de Emprego |
| `/vagas/<id>/` | 📄 Detalhes de uma Vaga |
| `/imoveis/` | 🏠 Lista de Imóveis para Alugar |
| `/dashboard/` | 🎛️ Painel do Usuário (Dashboard) |
| `/cadastro/` | 📝 Formulário de Cadastro |
| `/login/` | 🔐 Tela de Login |
| `/admin/` | ⚙️ Painel Administrativo do Django |

---

## 🎯 Funcionalidades Implementadas (Semanas 1 a 4)

### ✅ Backend / Banco de Dados
- [x] **Projeto Django organizado** com 4 apps (`users`, `jobs`, `properties`, `core`)
- [x] **CustomUser** (Usuário customizado): Nome completo, CPF, Data Nascimento, Telefone, Foto de Perfil, Endereço, Cidade e **Tipo de Usuário** (Candidato / Empresa / Proprietário)
- [x] **PerfilCandidato**: Sobre mim, Escolaridade, Instituição, Cursos, Formação, Diplomas, Experiências, Habilidades, Idiomas, Currículo PDF e Link do Portfólio
- [x] **Vaga + Candidatura**: Todos os campos e choices (Tipo Contrato, Modalidade, Status Vaga, Status Candidatura)
- [x] **Imovel**: Todos os campos, incluindo Mobiliado, Aceita Animais, Garagem, Área, etc.
- [x] `settings.py` **configurado para PostgreSQL** via `dj-database-url`, apps instaladas, `AUTH_USER_MODEL`, `MEDIA_ROOT` / `MEDIA_URL` (preparado para Firebase Storage depois)
- [x] **Admin customizado** para gerenciar todos os modelos

### ✅ Frontend / Protótipos (HTML + Bootstrap 5 responsivo)
- [x] `base.html` — Layout base com Bootstrap Icons, header dinâmico, footer
- [x] `home.html` — Hero com busca rápida, destaques de vagas e imóveis, CTAs
- [x] `register.html` — Formulário com **seletor de perfil** (Candidato / Empresa / Proprietário)
- [x] `login.html` — Formulário de login com "Lembrar-me" e Google
- [x] `jobs_list.html` — Filtros (cargo, cidade, salário, tipo contrato, modalidade) + cards
- [x] `job_detail.html` — Informações completas + botão de candidatura + estatísticas
- [x] `properties_list.html` — Filtros (local, preço, quartos, mobiliado, pet friendly) + galeria
- [x] `dashboard.html` — **3 visões condicionais**:
  - 🧑‍🎓 **Candidato**: cards resumo, histórico de candidaturas, completude do perfil, vagas recomendadas
  - 🏢 **Empresa**: cards estatísticos, tabela de vagas publicadas, ações
  - 🏠 **Proprietário**: cards estatísticos, tabela de imóveis, ações

Todos os templates são **100% responsivos** (desktop, tablet e mobile). 📱💻

---

## 📖 Próximos Passos (Semanas Futuras)

- [ ] Implementar autenticação real (cadastro / login / logout com `django.contrib.auth`)
- [ ] Views de CRUD reais para Vagas e Imóveis (publicar, editar, excluir)
- [ ] Lógica de candidatura a vagas com envio de e-mail
- [ ] Upload de arquivos integrado ao **Firebase Storage**
- [ ] Formulários reais com `django.forms` e validação de CPF/CNPJ
- [ ] API REST com **Django REST Framework** (para futuros apps móveis)
- [ ] Deploy em produção (ex: Heroku, Render, Vercel, Fly.io)

---

## 🐛 Troubleshooting Comum

### ❌ Erro: `django.db.utils.OperationalError: FATAL: password authentication failed`
**Solução:** Verifique o arquivo `.env` — a `DATABASE_URL` deve ter usuário e senha corretos do PostgreSQL. Teste o login no pgAdmin/psql.

### ❌ Erro: `relation "users_customuser" does not exist`
**Solução:** Você esqueceu de rodar as migrações. Execute:
```bash
python manage.py makemigrations
python manage.py migrate
```

### ❌ Erro no Windows: `psycopg2.OperationalError: could not translate host name`
**Solução:** Certifique-se de que o **serviço PostgreSQL está iniciado** (procure por "services" no Windows e inicie o serviço `postgresql-x64-XX`).

### ❌ Erro: `ModuleNotFoundError: No module named 'django'`
**Solução:** Seu ambiente virtual não está ativado! Repita o **Passo 3** (`.\.venv\Scripts\activate` no Windows).

### ❌ Problemas com caracteres acentuados no PostgreSQL
**Solução:** Certifique-se de que o banco foi criado com **encoding UTF8** (no pgAdmin, o padrão já é UTF-8).

---

## 📞 Suporte

Dúvidas? Entre em contato com a equipe do Projeto Integrador — IFPI Campus Paulistana.

---

> **Feito com 💚 pela comunidade IFPI.** Projeto educacional para fins de integração acadêmica.
