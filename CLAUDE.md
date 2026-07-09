# CLAUDE.md — 110. Balanca

Documentação do projeto **Balança** — app web de registo diário de peso corporal.

---

## Visão Geral

App web responsiva (browser + telemóvel) para registar e acompanhar o peso diário.  
Corre num servidor Flask no Render.com, com SQLite persistido em Persistent Disk.

---

## Requisitos

### Registo de Dados
1. Registar o peso diário (data + peso)
2. Editar registos de datas passadas
3. No formulário de novo registo, pré-preencher automaticamente:
   - **Data** → dia atual
   - **Peso** → último peso registado
4. Importar ficheiro Excel com dados em bulk (duas colunas: data e peso)

### Gráficos

**5.1 — Gráfico Linear**
- Mostra a evolução do peso ao longo do tempo
- Seletor de timeframe:
  - Última semana
  - Último mês
  - Últimos 3 meses
  - Últimos 6 meses
  - Último ano
  - Últimos 3 anos
  - Últimos 5 anos
  - Since start (todos os dados)

**5.2 — Gráfico Rolling 12 Meses**
- Média móvel de 12 meses
- Seletor para o tamanho da janela de rolling: **2 anos** ou **3 anos**
- O gráfico mostra **sempre desde o início** (todos os dados no eixo X)

### Pesquisa Histórica
6. O utilizador seleciona uma data; a app:
   - Vai buscar o peso registado nessa data
   - Mostra as **últimas 10 datas** em que o peso foi **igual ou inferior** a esse valor

---

## Arquitetura Técnica

### Stack

| Camada | Tecnologia |
|--------|-----------|
| **Frontend** | HTML + Tailwind CSS (CDN) + Chart.js (CDN) + SheetJS (CDN) |
| **Backend** | Python + Flask (REST API JSON) |
| **Base de dados** | SQLite |
| **Persistência** | Render Persistent Disk (~$0.25/mês) |
| **Deploy** | Render.com via GitHub |

### Diagrama

```
Frontend (HTML + Tailwind + Chart.js + SheetJS)
        ↕ REST API (JSON)
Backend (Python + Flask)
        ↕
SQLite (ficheiro em Persistent Disk)
        ↓
Render.com (deploy via GitHub)
```

### Decisões de Arquitetura

- **Persistent Disk em vez de Supabase:** solução mais simples (SQLite puro, sem psycopg2), sem risco de pausa por inatividade (free tier Supabase pausa após 1 semana), custo negligenciável (~$0.25/mês)
- **Flask em vez de frontend estático:** necessário para persistência multi-dispositivo (PC + telemóvel) e para não perder dados entre sessões
- **CDN para bibliotecas frontend:** sem build step, deploy simples

---

## Estrutura da App (4 tabs/secções)

| Tab | Ícone | Conteúdo |
|-----|-------|----------|
| **Registar** | 📝 | Formulário de novo registo e edição de registos passados |
| **Gráficos** | 📊 | Gráfico linear (5.1) + Rolling 12M (5.2) |
| **Pesquisa** | 🔍 | Últimas 10 datas com peso ≤ ao de uma data selecionada |
| **Dados** | ⚙️ | Importar Excel |

---

## Estrutura de Ficheiros (a criar)

```
110. Balanca/
├── CLAUDE.md               # este ficheiro
├── app.py                  # servidor Flask + endpoints REST
├── requirements.txt        # dependências Python
├── render.yaml             # configuração Render (persistent disk)
├── templates/
│   └── index.html          # frontend single-page (Tailwind + Chart.js + SheetJS)
└── data/                   # montagem do persistent disk no Render
    └── balanca.db          # base de dados SQLite
```

---

## Modelo de Dados (SQLite)

```sql
CREATE TABLE registos (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    data    DATE    NOT NULL UNIQUE,
    peso    REAL    NOT NULL
);
```

---

## API REST (Flask) — endpoints a implementar

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/registos` | Lista todos os registos (ordenados por data) |
| `POST` | `/api/registos` | Cria novo registo `{data, peso}` |
| `PUT` | `/api/registos/<id>` | Edita registo existente |
| `DELETE` | `/api/registos/<id>` | Remove registo |
| `POST` | `/api/import` | Importa array de `{data, peso}` em bulk |
| `GET` | `/api/pesquisa?data=YYYY-MM-DD` | Retorna últimas 10 datas com peso ≤ ao da data indicada |

---

## Convenções

- Datas no formato `YYYY-MM-DD` (ISO 8601)
- Peso em **kg** com até 1 casa decimal (ex: `82.5`)
- Linguagem da UI: **Português**
- Design: responsivo mobile-first (Tailwind CSS)
