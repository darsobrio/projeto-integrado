# 🏛️ Oportunet — Plataforma de Vagas e Imóveis

Plataforma web responsiva desenvolvida como **Projeto Integrador do IFPI Campus Paulistana**, com o objetivo de conectar a comunidade acadêmica e local a oportunidades de **emprego, estágio e moradia** (aluguel de imóveis).

---

## 🛠️ Tecnologias Utilizadas

| Camada | Tecnologia |
|---|---|
| **Backend** | Python 3.12+ + Django 4.2 LTS |
| **Banco de dados** | **Firestore** (Firebase Admin SDK) para vagas, imóveis, candidaturas e afins; **SQLite** para usuários (`CustomUser` / `PerfilCandidato`) |
| **Autenticação** | Firebase Authentication (login/cadastro) + `CustomUser` do Django |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5.3 (CDN), Bootstrap Icons, Leaflet (mapas) |
| **API** | Django REST Framework |
| **Uploads** | Disco local `media/` em desenvolvimento; **Firebase Storage** opcional em produção |
| **E-mail** | Console em desenvolvimento; SMTP em produção |
| **Outros** | WhiteNoise, Pillow, python-dotenv, dj-database-url, psycopg2-binary (PostgreSQL opcional) |
| **Controle de Versão** | Git / GitHub (CI com GitHub Actions) |

---

## 📁 Estrutura do Projeto

```
Oportunet/
├── ifpi_oportunidades/    # ⚙️ Configurações do projeto Django
│   ├── settings.py        # Configurações (apps, banco, storage, e-mail, produção)
│   ├── urls.py            # Rotas principais
│   └── wsgi.py / asgi.py
├── core/                  # 🧭 Páginas institucionais, dashboard, moderação, helpers
├── users/                 # 👤 CustomUser + PerfilCandidato
├── jobs/                  # 💼 Vagas, candidaturas, favoritos, alertas, mensagens
├── properties/            # 🏠 Imóveis para aluguel
├── api/                   # 🔌 Endpoints REST (Django REST Framework)
├── templates/             # 🎨 Templates HTML responsivos
├── static/                # 📦 Arquivos estáticos locais
├── tests/                 # 🧪 Suíte de testes automatizados
├── .github/workflows/     # 🔁 CI (GitHub Actions)
├── media/                 # 🖼️ Uploads locais (fotos, currículos, imóveis)
├── manage.py
├── requirements.txt
├── .env.example
├── ROADMAP.md             # 📋 Melhorias planejadas/implementadas
└── README.md
```

---

## ✅ Pré-requisitos

1. **Python 3.12+** — [python.org/downloads](https://www.python.org/downloads/)
2. **Conta/projeto no Firebase** com **Firestore** e **Authentication** habilitados
3. O arquivo **`serviceAccountKey.json`** (credencial do Admin SDK) na raiz do projeto
4. (Opcional) **PostgreSQL 12+** caso queira usar outro banco para os usuários

---

## 🚀 Passo a Passo

### 1️⃣. Clone o projeto

```bash
git clone https://github.com/darsobrio/projeto-integrado.git
cd Oportunet
```

### 2️⃣. Crie e ative um ambiente virtual (venv)

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3️⃣. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4️⃣. Configure as variáveis de ambiente (.env)

```powershell
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

Edite o `.env` conforme necessário (veja os comentários do [.env.example](.env.example)). No desenvolvimento, o padrão `DB_ENGINE=sqlite` já funciona.

> ⚠️ **Nunca versione o `.env` nem o `serviceAccountKey.json`** — já estão no `.gitignore`.

### 5️⃣. Coloque a credencial do Firebase

Baixe o `serviceAccountKey.json` no console do Firebase (Configurações do projeto → Contas de serviço) e coloque-o **na raiz do projeto**. O site inicializa o Firebase Admin SDK ao importar o app `core`.

### 6️⃣. Rode as migrações

```bash
python manage.py migrate
```

### 7️⃣. Crie um superusuário (Admin)

```bash
python manage.py createsuperuser
```

### 8️⃣. Suba o servidor de desenvolvimento 🚀

```bash
python manage.py runserver
```

Acesse **http://127.0.0.1:8000/**.

---

## 🧪 Testes

```bash
python manage.py test
```

A suíte cobre validação de CPF/CNPJ, formatação de valores, paginação, conversão dos documentos do Firestore e os serializers da API. O CI (`.github/workflows/ci.yml`) roda `manage.py check` e os testes a cada *push* e *pull request*.

---

## 📌 URLs Principais

| Rota | Descrição |
|---|---|
| `/` | 🏠 Página Inicial |
| `/vagas/` | 💼 Lista de Vagas |
| `/vagas/<id>/` | 📄 Detalhes de uma Vaga |
| `/imoveis/` | 🏠 Lista de Imóveis |
| `/dashboard/` | 🎛️ Painel do Usuário |
| `/usuarios/perfil/` | 👤 Meu perfil (dados, currículo, segurança) |
| `/cadastro/` · `/login/` | 📝 Cadastro e 🔐 Login |
| `/moderacao/` | 🛡️ Painel de moderação (equipe) |
| `/api/vagas/` · `/api/imoveis/` | 🔌 API REST (JSON) |
| `/api/candidaturas/` | 🔌 Candidaturas do usuário (requer login) |
| `/admin/` | ⚙️ Painel Administrativo do Django |

---

## 🎯 Funcionalidades

- **Cadastro/login** com Firebase Auth, dois tipos de conta (candidato e empresa)
- **Vagas**: publicar (empresa), filtrar, favoritar, alertas por filtro salvo, candidatar-se, compartilhar
- **Imóveis**: qualquer usuário autenticado pode publicar; galeria de fotos, mapa (Leaflet), filtro por proximidade
- **Perfil do candidato**: escolaridade, experiências, habilidades, currículo em PDF e barra de completude
- **Candidaturas**: acompanhamento de status pela empresa, com notificação por e-mail
- **Mensagens** entre empresa e candidato dentro da plataforma
- **Moderação**: denúncia de anúncio, verificação de empresa (selo), limite de anúncios por conta
- **API REST** para futuros apps móveis

---

## 📋 Roadmap

As melhorias planejadas e já implementadas estão registradas em [ROADMAP.md](ROADMAP.md).

---

## 🐛 Troubleshooting

### ❌ `ModuleNotFoundError: No module named 'django'`
O ambiente virtual não está ativado. Repita o **Passo 2**.

### ❌ `ModuleNotFoundError: No module named 'firebase_admin'`
Provavelmente há **outro venv ativado** por cima do local. Rode `deactivate` e ative o `.venv` do projeto.

### ❌ Erro ao inicializar o Firebase (credencial)
Confirme que o **`serviceAccountKey.json`** está na raiz do projeto.

### ❌ Porta 8000 ocupada após parar o servidor
O subprocesso do `StatReloader` pode segurar a porta. Identifique e encerre o processo:
```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen
```

---

## 📞 Suporte

Dúvidas? Entre em contato com a equipe do Projeto Integrador — IFPI Campus Paulistana.

---

> **Feito com 💚 pela comunidade IFPI.** Projeto educacional para fins de integração acadêmica.
