# Project Handoff: Deep Audit Knowledge Engine

## ¿Qué es esto?

Motor multi-agente de ingesta de conocimiento técnico. Toma contenido de YouTube, GitHub, blogs web, feeds RSS y recetas de cocina, lo analiza con Gemini 2.0 Flash usando prompts Jinja2 externalizados, y genera notas estructuradas en Markdown directamente en un vault de Obsidian. Incluye deduplicación automática, historial persistente en Supabase, y dashboard de analytics.

---

## Setup desde cero

### 1. Requisitos previos
- Python 3.11+
- Git
- Docker + Docker Compose (para deploy)

### 2. Entorno local (desarrollo)

```bash
git clone https://github.com/luuisaguilar/deep-audit-knowledge-engine.git
cd deep-audit-knowledge-engine
python -m venv venv
.\\venv\\Scripts\\activate        # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

### 3. Credenciales

Crear el archivo `.env` en la raíz del proyecto (NO commitear):

```env
GEMINI_API_KEY=tu_clave_aqui
GITHUB_TOKEN=tu_pat_aqui
SUPABASE_URL=https://tuproyecto.supabase.co
SUPABASE_KEY=tu_anon_key_aqui
VAULT_PATH=/mnt/obsidian-vault
```

- **Gemini API Key**: console.cloud.google.com → APIs → Generative Language API
- **GitHub PAT**: github.com → Settings → Developer Settings → Personal Access Tokens → Fine-grained → permisos: `repo:read`, `metadata:read`
- **Supabase**: supabase.com → Project Settings → API → `URL` y `anon/public` key

### 4. Arranque local

```bash
streamlit run app.py
```

### 5. Deploy en producción (Docker)

```bash
# Configurar .env con todas las variables
docker-compose up -d --build

# Verificar que los servicios están corriendo
docker-compose ps

# Ver logs de la API
docker-compose logs -f api
```

Acceso público UI: `https://knowledge.tudominio.com`
Acceso interno API (para n8n): `http://knowledge-engine-api:8000/api/v1/...`

---

## Estado actual del proyecto

### Sprint completados: 1, 2, 3, 3.5, 4, 5, 5.5, 6, 7, 8

### Sprint activo: 9 — Orquestación y Automatización

Objetivo: Proveer al sistema de un cerebro automatizado (FastAPI) capaz de procesar enlaces desde Telegram/n8n sin intervención manual en la UI.

### Módulos implementados

| Módulo | Función | Tab en la app |
|--------|---------|---------------|
| `youtube_analyzer.py` | Indexa canal, descarga transcripciones, analiza con Gemini | 📺 YouTube Analysis |
| `github_analyzer.py` | Trees API, archivos ADN, genera Wiki técnica | 💻 GitHub Deep Audit |
| `web_analyzer.py` | Scraping con BS4, análisis Zettelkasten | 🌐 Web Ingestion |
| `cooking_analyzer.py` | Extracción de recetas + lista del súper | 🍳 Digital Chef |
| `rss_manager.py` + `rss_db.py` | RSS Monitor con persistencia SQLite | 📰 RSS Monitor |
| `knowledge_sync.py` | Lee DBs de agentes externos, exporta a Obsidian | 🧠 Obsidian Sync |
| `notebooklm_pack.py` | Source Pack de URLs + nota de contexto | 📚 NotebookLM Pack |
| `core/db.py` | Historial central, dedup, stats, tokens y RAG | 📊 Analytics / 🔍 Buscador |
| `api.py` | **NUEVO:** Endpoints REST para orquestación con n8n | 🤖 (Backend sin UI) |

### Infraestructura

| Módulo | Función |
|--------|---------|
| `config.py` | Singleton Gemini, `generate_with_retry()`, y tracking de Tokens |
| `core/db.py` | Persistencia central — Supabase (RAG, Tokens, Historial) |
| `core/prompt_loader.py` | Renderizador de prompts Jinja2 desde `prompts/*.md` |
| `prompts/*.md` | 6 templates de prompts editables sin tocar código |
| `Dockerfile` | Contenedor Python + ffmpeg + Node.js (para yt-dlp) |
| `docker-compose.yml` | App (Streamlit), API (FastAPI) + Cloudflare Tunnel |

### Módulos planeados

| Módulo | Sprint | Función |
|--------|--------|---------|
| `n8n_workflows/` | Sprint 9 | Importación de flujos de n8n (Telegram, RSS Auto) |
| `Notificaciones` | Sprint 10 | Intelligence Briefings diarios |

---

## Arquitectura clave

```text
┌─── Docker (Proxmox LXC) ───────────────────────────────────┐
│                                                             │
│  app.py (Puerto 8501)      api.py (Puerto 8000)             │
│    UI (Streamlit)            REST Endpoints (FastAPI)       │
│           │                           │                     │
│           └───────────┬───────────────┘                     │
│                       ↓ importa                             │
│  config.py              ← Gemini singleton + Tokens         │
│  core/db.py             ← Supabase client + RAG pgvector    │
│  core/prompt_loader.py  ← Jinja2 renderer                   │
│    ↓ usados por                                             │
│  *_analyzer.py          ← Lógica pura                       │
│    ↓ resultados                                             │
│  save_note()            ← Escribe en vault (Volumen)        │
│  record_ingestion()     ← Registra en Supabase              │
│                                                             │
│  cloudflared (sidecar)  ← HTTPS tunnel                      │
│                                                             │
└──────────────┬──────────────────────────────────────────────┘
               │
               ├──→ Supabase (ingestions, analytics, embeddings)
               ├──→ Gemini 2.0 Flash API
               └──→ Webhooks hacia n8n
```

**Regla de oro**: ningún `_analyzer.py` importa `streamlit`. Toda la UI vive en `app.py`, toda la API en `api.py`.

---

## Deduplicación

Antes de procesar cualquier URL, `app.py` llama a `has_been_processed(url)`.
Si la URL ya tiene un registro con `status='success'` en Supabase, se muestra "⏭️ Ya procesado" y se salta.
Esto aplica a **todos** los tabs: YouTube, GitHub, Web, RSS, Chef.

---

## Prompt Templates

Los prompts están en `prompts/*.md` como archivos Jinja2. Para cambiar el formato, tono, o secciones de las notas generadas:

1. Editar el archivo `.md` correspondiente (ej: `prompts/youtube_analysis.md`)
2. Reiniciar Streamlit
3. Procesar contenido — el nuevo prompt se aplica automáticamente

Variables disponibles en cada template están documentadas como `{{ variable }}` dentro del archivo.

---

## Carpetas de Obsidian generadas

| Carpeta | Contenido |
|---------|-----------|
| `10_YouTube/` | Auditorías técnicas de videos |
| `20_GitHub/` | Wikis de repositorios |
| `30_Web/` | Artículos web |
| `30_Web/RSS/` | Artículos procesados de feeds RSS |
| `40_NotebookLM/` | Notas de contexto del Source Pack |
| `40_Agente_Sync/` | Reportes de AuctionBot, DexScreener |
| `50_Recetas/` | Recetas y listas del súper |

---

## Decisiones importantes

Ver `docs/ADR.md` para el razonamiento completo (13 ADRs). Resumen:

- **config.py centraliza todo lo de Gemini** — no tocar la inicialización del modelo en otro lado
- **Supabase para ingestions** — datos consultables cross-proyecto, compatible con n8n (ADR-012, reemplaza ADR-010 SQLite local)
- **Docker + Cloudflare Tunnel** — deploy reproducible sin port forwarding (ADR-013)
- **Prompts externalizados en Jinja2** — iterar calidad sin tocar código Python
- **SQLite local solo para RSS feeds** — es configuración, no data operativa (ADR-007)
- **NotebookLM sin API** — el Source Pack es el workaround hasta que Google publique API

---

## Cuotas y límites

| Servicio | Límite free tier | Manejo actual |
|----------|-----------------|---------------|
| Gemini 2.0 Flash | 15 req/min, 1500 req/día | `tenacity` backoff exponencial en `config.py` |
| GitHub API sin auth | 60 req/hora | `GITHUB_TOKEN` en `.env` → 5000 req/hora |
| YouTube Transcript API | Sin límite conocido | Caché en `session_state.transcript_cache` |
| Supabase | 500 MB DB, 50K rows | Más que suficiente para uso personal |

---

## Tests

```bash
# Requiere que Playwright esté instalado
playwright install chromium

# Ejecutar tests E2E
pytest test_app_ui.py -v
```

Los tests levantan una instancia de Streamlit en el puerto 8502 y verifican la existencia de los 8 tabs y elementos UI clave.

---

## Despliegue

### Producción (Docker — Recomendado)

```bash
docker-compose up -d
# Acceso: https://knowledge.tudominio.com
```

### Legacy (Proxmox directo — Deprecado, ver ADR-013)

```bash
# setup_proxmox.sh y youtube_service.service están deprecados
# Mantenidos solo como referencia histórica
```
