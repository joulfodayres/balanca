# CLAUDE.md — 110. Balanca

Documentação do projeto **Balança** — app web de registo diário de peso corporal.

---

## Visão Geral

App web responsiva (browser + telemóvel) para registar e acompanhar o peso diário.
Corre num servidor Flask no Render.com, com base de dados PostgreSQL no Supabase.

---

## Requisitos Implementados

### Registo de Dados
1. Registar o peso diário (data + peso)
2. Editar registos de datas passadas
3. No formulário de novo registo, pré-preencher automaticamente:
   - **Data** → dia atual (hora local, não UTC)
   - **Peso** → último peso registado
4. Importar ficheiro Excel com dados em bulk (duas colunas: data e peso)
   - Suporta datas em formato datetime nativo do Excel, DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY
5. Exportar todos os dados para ficheiro Excel (`balanca.xlsx`)
6. Apagar todos os dados (protegido por password: `1973`)

### Gráficos

**5.1 — Gráfico Linear**
- Mostra a evolução do peso ao longo do tempo
- Seletor de timeframe: 7d / 1M / 3M / 6M / 1A / 3A / 5A / Tudo

**5.2 — Gráfico Rolling 12 Meses**
- Média móvel de 12 meses sobreposta ao peso real
- Seletor para o tamanho da janela de rolling: **2 anos** ou **3 anos**
- O gráfico mostra **sempre desde o início** (todos os dados no eixo X)

### Pesquisa Histórica
- O utilizador seleciona uma data; a app mostra as **últimas 10 datas** em que o peso foi **igual ou inferior** ao peso dessa data

---

## Arquitetura Técnica

### Stack

| Camada | Tecnologia |
|--------|-----------|
| **Frontend** | HTML + Tailwind CSS (CDN) + Chart.js (CDN) + SheetJS (CDN) |
| **Backend** | Python + Flask (REST API JSON) |
| **Base de dados** | PostgreSQL (Supabase — free tier) |
| **Deploy** | Render.com (free tier) via GitHub |

### Diagrama

```
Frontend (HTML + Tailwind + Chart.js + SheetJS)
        ↕ REST API (JSON)
Backend (Python + Flask) — Render.com
        ↕ psycopg2 (Transaction Pooler, porta 6543)
PostgreSQL — Supabase
```

### Decisões de Arquitetura

- **Supabase em vez de Persistent Disk:** o Persistent Disk do Render requer plano pago ($7/mês); Supabase oferece PostgreSQL gratuito. Para uso diário não há risco de pausa (free tier pausa após 1 semana de inatividade).
- **Transaction Pooler (porta 6543):** o free tier do Render bloqueia ligações diretas PostgreSQL (porta 5432); usa-se o pooler do Supabase na porta 6543.
- **Password sem caracteres especiais na DATABASE_URL:** caracteres como `!` ou `@` na password causam erros de parsing na connection string.
- **Flask em vez de frontend estático:** necessário para persistência multi-dispositivo (PC + telemóvel).
- **CDN para bibliotecas frontend:** sem build step, deploy simples.

---

## Estrutura da App (4 tabs/secções)

| Tab | Ícone | Conteúdo |
|-----|-------|----------|
| **Registar** | 📝 | Formulário de novo registo, edição e lista de registos |
| **Gráficos** | 📊 | Gráfico linear (5.1) + Rolling 12M (5.2) |
| **Pesquisa** | 🔍 | Últimas 10 datas com peso ≤ ao de uma data selecionada |
| **Dados** | ⚙️ | Importar Excel, Exportar Excel, Apagar todos os dados |

---

## Estrutura de Ficheiros

```
110. Balanca/
├── CLAUDE.md               # este ficheiro
├── app.py                  # servidor Flask + endpoints REST
├── requirements.txt        # dependências Python
├── render.yaml             # configuração Render
├── templates/
│   └── index.html          # frontend single-page (Tailwind + Chart.js + SheetJS)
└── Import.xlsx             # ficheiro de dados históricos para importação
```

---

## Modelo de Dados (PostgreSQL)

```sql
CREATE TABLE registos (
    id   SERIAL PRIMARY KEY,
    data DATE    NOT NULL UNIQUE,
    peso REAL    NOT NULL
);
```

Acessível via **Supabase → SQL Editor**. Exemplos de queries úteis:
```sql
SELECT * FROM registos ORDER BY data DESC;
SELECT * FROM registos WHERE peso < 80 ORDER BY data DESC LIMIT 10;
SELECT AVG(peso) FROM registos WHERE data >= '2025-01-01';
```

---

## API REST (Flask)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/registos` | Lista todos os registos (ordenados por data) |
| `POST` | `/api/registos` | Cria novo registo `{data, peso}` |
| `PUT` | `/api/registos/<id>` | Edita registo existente |
| `DELETE` | `/api/registos/<id>` | Remove registo |
| `POST` | `/api/import` | Importa array de `{data, peso}` em bulk |
| `GET` | `/api/export` | Exporta todos os registos para Excel |
| `DELETE` | `/api/apagar-tudo` | Apaga todos os registos (requer `{password: "1973"}`) |
| `GET` | `/api/pesquisa?data=YYYY-MM-DD` | Últimas 10 datas com peso ≤ ao da data indicada |

---

## Variáveis de Ambiente (Render)

| Variável | Valor |
|----------|-------|
| `DATABASE_URL` | `postgresql://postgres.PROJETO:PASSWORD@aws-0-eu-west-3.pooler.supabase.com:6543/postgres` |

⚠️ Usar sempre o **Transaction Pooler** (porta 6543), não a Direct Connection (porta 5432).
⚠️ A password **não deve conter caracteres especiais** (`!`, `@`, `#`, etc.).

---

## Backlog

| ID | Descrição | Estado |
|----|-----------|--------|
| BACKLOG-001 | Redesign UX/UI: dark mode, ícones maiores, otimizado para iPhone, fontes maiores | ✅ Implementado — dark mode por defeito, bottom nav mobile, fontes maiores, botões maiores |
| BACKLOG-002 | Pesquisa por peso: mostrar as 10 datas mais recentes com peso inferior ao valor pesquisado | ✅ Implementado — novo campo "Por peso" no tab Pesquisa + endpoint `/api/pesquisa-peso` |

---

## Defects Conhecidos

| ID | Descrição | Estado |
|----|-----------|--------|
| DEF-005 | Data no formulário de registo mostra mm/dd/yyyy em vez de dd/mm/yyyy | ✅ Corrigido — input texto DD/MM/AAAA com formatação automática |
| DEF-006 | Data no ecrã de pesquisa mostra mm/dd/yyyy em vez de dd/mm/yyyy | ✅ Corrigido — input texto DD/MM/AAAA com formatação automática |

---

## Convenções

- Datas internas no formato `YYYY-MM-DD` (ISO 8601)
- Datas apresentadas ao utilizador no formato `DD/MM/YYYY`
- Peso em **kg** com até 1 casa decimal (ex: `82.5`)
- Linguagem da UI: **Português**
- Design: responsivo mobile-first (Tailwind CSS)
