# Plataforma de Oportunidades IFPI - Product Requirements Document

## Overview
- **Summary**: Plataforma web responsiva de oportunidades (Empregos e Aluguel de Imóveis) voltada para a comunidade acadêmica e local do IFPI Campus Paulistana.
- **Purpose**: Conectar a comunidade acadêmica e local a oportunidades de emprego, estágio e moradia acessível através de uma plataforma centralizada e fácil de usar.
- **Target Users**: Candidatos (estudantes e comunidade local), Empresas (oferecendo vagas) e Proprietários (oferecendo imóveis para aluguel).

## Goals
- Criar estrutura base completa do projeto Django organizada em 4 apps (users, jobs, properties, core)
- Implementar toda a modelagem de banco de dados com todos os campos requisitados
- Configurar integração com PostgreSQL
- Preparar estrutura para integração futura com Firebase Storage
- Criar templates HTML responsivos para as páginas essenciais
- Gerar documentação de instalação e execução

## Non-Goals
- Implementar lógica de autenticação completa (apenas estrutura de formulários e templates)
- Integração real com Firebase Storage (apenas preparação da estrutura)
- Funcionalidades de pagamento ou transações financeiras
- API REST completa (apenas estrutura básica do Django)
- Testes automatizados unitários ou de integração
- Deploy em produção (apenas ambiente de desenvolvimento)

## Background & Context
- Projeto Integrador do IFPI Campus Paulistana, entregas previstas até a Semana 4
- Stack tecnológica definida: Python + Django, HTML5/CSS3/JS com Tailwind CSS/Bootstrap 5, PostgreSQL, Firebase Storage, Git/GitHub

## Functional Requirements

### Estrutura do Projeto
- **FR-1**: Projeto Django com 4 apps: `users`, `jobs`, `properties`, `core`
- **FR-2**: Arquivo `requirements.txt` com Django, psycopg2, dj-database-url e dependências essenciais
- **FR-3**: `settings.py` configurado para PostgreSQL com suporte a variáveis de ambiente via dj-database-url
- **FR-4**: `urls.py` principal do projeto roteando para todos os apps
- **FR-5**: Estrutura de pastas para templates e arquivos estáticos (CSS/JS)

### App `users`
- **FR-6**: Modelo CustomUser com: Nome completo, CPF, Data de Nascimento, E-mail, Telefone, Foto de Perfil, Endereço/Cidade, Senha e Tipo de Usuário (CANDIDATO, EMPRESA, PROPRIETARIO)
- **FR-7**: Modelo PerfilCandidato com: Sobre mim, Escolaridade, Instituição, Cursos, Formação Acadêmica, Diplomas, Experiências Anteriores, Habilidades, Idiomas, Currículo (PDF) e Link de Portfólio

### App `jobs`
- **FR-8**: Modelo Vaga com: Nome da Empresa, CNPJ, Endereço, Função, Descrição, Requisitos, Salário, Benefícios, Horário, Tipo de Contrato (CLT, Temporário, Estágio, Jovem Aprendiz, Freelancer), Modalidade (Presencial, Híbrido, Remoto), Qtd. Vagas, Data de Publicação, Prazo, Status (Aberta/Fechada)
- **FR-9**: Modelo Candidatura com: Vaga (FK), Candidato (FK), Data de Envio, Status da Candidatura (Enviada, Em análise, Entrevista, Aprovado, Recusado)

### App `properties`
- **FR-10**: Modelo Imovel com: Fotos, Endereço, Bairro/Cidade, Valor Aluguel, Valor Condomínio, Quartos, Banheiros, Garagem, Área (m²), Mobiliado (Boolean), Aceita Animais (Boolean), Descrição, Características, Regras, Contato do Proprietário, Disponibilidade

### Templates Responsivos
- **FR-11**: `base.html` - Template base com header dinâmico e estrutura CSS responsiva
- **FR-12**: `home.html` - Página inicial com banner de busca rápida e cards de destaque
- **FR-13**: `register.html` / `login.html` - Páginas de cadastro e login com seletor de perfil
- **FR-14**: `jobs_list.html` - Lista de vagas com barra de filtros (cargo, cidade, faixa salarial, tipo de contrato, modalidade)
- **FR-15**: `job_detail.html` - Detalhes completos da vaga com botão de candidatura
- **FR-16**: `properties_list.html` - Lista de imóveis com filtros (cidade/bairro, preço, quartos, aceita animais, mobiliado)
- **FR-17**: `dashboard.html` - Dashboard com visões distintas para Candidato, Empresa e Proprietário

### Documentação
- **FR-18**: README.md com instruções passo a passo para rodar migrações no PostgreSQL e subir o servidor de desenvolvimento

## Non-Functional Requirements
- **NFR-1**: Todos os templates devem ser responsivos (desktop e mobile)
- **NFR-2**: Código deve seguir padrões do Django e PEP 8
- **NFR-3**: Configurações sensíveis devem usar variáveis de ambiente
- **NFR-4**: Modelos devem ter nomes em português, campos em camelCase ou snake_case conforme convenção Django
- **NFR-5**: CSS deve ser estilizado com framework moderno (Bootstrap 5 via CDN para simplicidade)

## Constraints
- **Technical**: Django + Python, PostgreSQL, Bootstrap 5/Tailwind CSS; não usar outras frameworks sem necessidade
- **Business**: Entrega base até Semana 4; foco em estrutura e protótipos, não funcionalidades completas
- **Dependencies**: psycopg2 (PostgreSQL), dj-database-url (configuração DB via URL), Pillow (imagens)

## Assumptions
- PostgreSQL estará instalado e configurado localmente pelo usuário
- O usuário terá Python 3.8+ instalado
- Firebase Storage será integrado em fase posterior, por enquanto apenas campos de arquivo preparados
- Bootstrap 5 via CDN é aceitável para agilizar o desenvolvimento dos protótipos

## Acceptance Criteria

### AC-1: Estrutura de Projeto Django Completa
- **Type**: `rule`
- **Given**: Um diretório de projeto vazio
- **When**: Os arquivos do projeto são criados
- **Then**: Deve existir a estrutura completa com: manage.py, projeto_config com settings/urls/wsgi/asgi, e 4 apps (users, jobs, properties, core) cada um com models.py, views.py, urls.py, admin.py, apps.py e migrations/
- **Pass Condition**: Árvore de diretórios completa e estruturada corretamente conforme padrão Django
- **Evidence**: Listagem do diretório via comando `tree` ou `ls -R`

### AC-2: Configuração do PostgreSQL
- **Type**: `rule`
- **Given**: O arquivo settings.py do projeto
- **When**: O settings.py é inspecionado
- **Then**: Deve conter configuração DATABASES usando dj-database-url com suporte a PostgreSQL, e INSTALLED_APPS incluindo todos os 4 apps
- **Pass Condition**: settings.py tem DATABASES configurado para PostgreSQL com dj-database-url, e todas as apps listadas em INSTALLED_APPS
- **Evidence**: Leitura do arquivo settings.py

### AC-3: Models do App users Completos
- **Type**: `rule`
- **Given**: O arquivo users/models.py
- **When**: O models.py é inspecionado
- **Then**: Deve conter CustomUser (herdando AbstractUser) com todos os campos requisitados e PerfilCandidato com todos os campos requisitados, com tipos de usuário (choices) definidos
- **Pass Condition**: Ambos os modelos existem com todos os campos e relacionamentos corretos
- **Evidence**: Leitura do arquivo users/models.py

### AC-4: Models do App jobs Completos
- **Type**: `rule`
- **Given**: O arquivo jobs/models.py
- **When**: O models.py é inspecionado
- **Then**: Deve conter Vaga com todos os campos e choices para TipoContrato, Modalidade, Status; e Candidatura com FK para Vaga e CustomUser (candidato), mais StatusCandidatura
- **Pass Condition**: Ambos os modelos existem com todos os campos, choices e relacionamentos corretos
- **Evidence**: Leitura do arquivo jobs/models.py

### AC-5: Models do App properties Completos
- **Type**: `rule`
- **Given**: O arquivo properties/models.py
- **When**: O models.py é inspecionado
- **Then**: Deve conter Imovel com todos os campos, incluindo BooleanFields para Mobiliado e AceitaAnimais, FK para Proprietário (CustomUser)
- **Pass Condition**: Modelo Imovel existe com todos os campos e relacionamentos corretos
- **Evidence**: Leitura do arquivo properties/models.py

### AC-6: requirements.txt com Todas as Dependências
- **Type**: `rule`
- **Given**: O arquivo requirements.txt
- **When**: O requirements.txt é inspecionado
- **Then**: Deve listar Django (versão LTS recomendada), psycopg2-binary, dj-database-url, Pillow, python-dotenv e whitenoise
- **Pass Condition**: Todas as dependências essenciais estão listadas com versões
- **Evidence**: Leitura do arquivo requirements.txt

### AC-7: Templates HTML Responsivos
- **Type**: `rubric`
- **Dimension**: Qualidade e completude dos templates HTML
- **Scale**: 1-5
- **Anchors**: 1 = Falta mais da metade dos templates; 3 = Todos templates existem mas sem estilização; 5 = Todos templates completos, estilizados com Bootstrap 5, responsivos, com seções requisitadas
- **Pass Threshold**: >= 4
- **Evidence**: Leitura dos arquivos de template em templates/

### AC-8: README.md com Instruções de Instalação
- **Type**: `rule`
- **Given**: O arquivo README.md
- **When**: O README.md é inspecionado
- **Then**: Deve conter: pré-requisitos, instalação de dependências, configuração do PostgreSQL, criação de .env, comandos de migração (makemigrations e migrate), criação de superusuário e comando para rodar servidor
- **Pass Condition**: Todas as seções de instrução existem e são passíveis de execução
- **Evidence**: Leitura do arquivo README.md

### AC-9: URLs Configuradas Corretamente
- **Type**: `rule`
- **Given**: O urls.py principal e os urls.py de cada app
- **When**: Os arquivos de URL são inspecionados
- **Then**: O urls.py principal deve incluir include() para cada app, e cada app deve ter seu urls.py com paths definidos para as views principais
- **Pass Condition**: Roteamento configurado entre projeto e apps
- **Evidence**: Leitura dos arquivos urls.py

### AC-10: Preparação para Firebase Storage
- **Type**: `rule`
- **Given**: O settings.py e modelos com campos de arquivo/imagem
- **When**: O código é inspecionado
- **Then**: Deve haver campos FileField/ImageField nos modelos (foto_perfil, curriculo_pdf, fotos_imovel) configurados com upload_to, e settings.py com MEDIA_ROOT e MEDIA_URL definidos
- **Pass Condition**: Campos de arquivo preparados e configuração de media presente
- **Evidence**: Leitura de settings.py e models.py dos apps

## Open Questions
- [ ] Nenhuma questão em aberto; todos os requisitos foram fornecidos explicitamente no prompt do usuário.
