# Roadmap de melhorias — Oportunet

Lista de melhorias planejadas para a plataforma, na ordem de execução.
Legenda: 🔴 alta prioridade · 🟡 média · 🟢 futuro

---

## Bloco A — Lacunas visíveis ao usuário

- [x] 🔴 **1. Upload de arquivos funcionando**
  - Situação: os campos existem (`foto_perfil`, `curriculo_pdf` em `users/models.py`;
    `Imovel.fotos` em `properties/models.py`), mas nenhum template tem
    `enctype="multipart/form-data"` e nenhuma view lê `request.FILES`.
  - Resultado: foto de perfil, currículo em PDF e foto do imóvel não sobem.
  - Onde mexer: `templates/profile.html`, `templates/property_form.html`,
    `users/views.py`, `properties/views.py`.
  - Observação: `imoveis` vivem no Firestore, então o arquivo é salvo em `media/`
    e o caminho/URL é gravado no documento do Firestore.

- [x] 🔴 **2. Tela de perfil do candidato**
  - Situação: o model `PerfilCandidato` está criado e migrado, mas não tem view,
    formulário nem template. `/usuarios/perfil/` apenas reaproveita o dashboard.
  - Conteúdo: sobre mim, escolaridade, instituição, cursos, formação, diplomas,
    experiências, habilidades, idiomas, currículo em PDF e link do portfólio.
  - Extra: barra de "perfil X% completo" para incentivar o preenchimento.

- [x] 🔴 **3. Editar dados da conta**
  - Situação: hoje só é possível editar pelo `/admin/`.
  - Campos: nome completo, telefone, cidade, endereço, data de nascimento, foto.

- [x] 🔴 **4. Recuperar senha e trocar senha**
  - Situação: quem esquece a senha perde a conta.
  - Solução: `firebase_auth.generate_password_reset_link()` + envio por e-mail,
    e tela de troca de senha para o usuário logado.

- [x] 🔴 **5. Notificar o candidato por e-mail**
  - Situação: a empresa muda o status da candidatura
    (enviada → em análise → entrevista → aprovado/recusado) e o candidato nunca sabe.
  - Solução: e-mail automático a cada mudança de status.

---

## Bloco B — Qualidade e desempenho

- [x] 🟡 **6. Filtrar no Firestore em vez de filtrar na memória**
  - Situação: as listagens baixam a coleção inteira e filtram em Python.
  - Solução: montar a consulta com `.where()` / `.order_by()` no Firestore.

- [x] 🟡 **7. Paginação nas listas de vagas e imóveis**
  - Situação: carrega tudo de uma vez.

- [x] 🟡 **8. Ordenação nas listas**
  - Opções: mais recentes, maior salário, menor preço.

- [x] 🟡 **9. Várias fotos por imóvel (galeria)**
  - Situação: `Imovel.fotos` é um único `ImageField` — por isso os cards usam
    capa em gradiente genérica.
  - Solução: coleção/lista de fotos por imóvel, com imagem de capa e galeria.

- [x] 🟡 **10. Validação de CPF/CNPJ com dígito verificador**
  - Situação: hoje só é verificado se o documento já existe; `111.111.111-11` passa.

- [x] 🟡 **11. Fechar vaga pelo prazo**
  - Situação: o campo `prazo` existe em `Vaga`, mas não é usado — vagas vencidas
    continuam aparecendo como abertas.

- [x] 🟡 **12. Favoritar vaga e alerta por filtro salvo**
  - "Me avise quando surgir vaga de estágio em Paulistana".

---

## Bloco C — Estruturais / futuro

- [x] 🟢 **13. Mensagens entre empresa e candidato** dentro da plataforma,
  com envio do currículo anexo.

- [x] 🟢 **14. Mapa de imóveis** por localização, com filtro por proximidade.

- [x] 🟢 **15. Moderação e segurança**: denúncia de anúncio falso, verificação de
  empresa e limite de anúncios por conta.

- [x] 🟢 **16. Migrar de SQLite para PostgreSQL**
  - As dependências (`psycopg2-binary`, `dj-database-url`) e as variáveis
    (`DB_ENGINE` / `DATABASE_URL`) já estão prontas em `settings.py`.
  - Basta definir `DB_ENGINE=postgres` e `DATABASE_URL=...` no ambiente.

- [x] 🟢 **17. Firebase Storage para os uploads**, no lugar do disco local `media/`
  (obrigatório para rodar em produção).
  - Ativar com `USE_FIREBASE_STORAGE=True` + `FIREBASE_STORAGE_BUCKET`.

- [x] 🟢 **18. API REST com Django REST Framework** para viabilizar app mobile.
  - Endpoints em `/api/vagas/`, `/api/vagas/<id>/`, `/api/imoveis/`,
    `/api/imoveis/<id>/` e `/api/candidaturas/` (esta exige login).

- [x] 🟢 **19. Deploy em produção**
  - `DEBUG=False`, `ALLOWED_HOSTS` restrito (hoje é `['*']`), HTTPS e rotação da
    chave que ficou exposta no histórico do Git.
  - As travas de segurança (HSTS, cookies seguros, redirect HTTPS) entram
    automaticamente quando `DEBUG=False`.

- [x] 🟢 **20. Testes automatizados**
  - Suíte em `tests/` (`manage.py test`) cobrindo validação de CPF/CNPJ,
    formatação, paginação, conversão de documentos e serializers da API.
  - CI no GitHub Actions (`.github/workflows/ci.yml`) rodando a cada push/PR.

- [x] 🟢 **21. Compartilhar vaga em redes sociais / WhatsApp** com imagem de prévia
  (`og:` tags).

---

## Ordem de execução

1. Bloco A (itens 1 a 5) — resolve lacunas que o usuário percebe na hora.
2. Bloco B (itens 6 a 12) — desempenho, confiabilidade e usabilidade.
3. Bloco C (itens 13 a 21) — evolução estrutural do produto.
