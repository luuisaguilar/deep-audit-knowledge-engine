# Project Handoff: Deep Audit Knowledge Engine

## ¿Qué es esto?

Motor multi-agente de ingesta de conocimiento técnico. Toma contenido de YouTube, GitHub, blogs web, feeds RSS y recetas de cocina, lo analiza con Gemini 2.0 Flash usando prompts Jinja2 externalizados, y genera notas estructuradas en Markdown directamente en un vault de Obsidian. Incluye deduplicación automática, historial persistente, y dashboard de analytics.

---

## Setup desde cero

### 1. Requisitos previos
- Python 3.11+
- Git

### 2. Entorno

```bash
git clone https://github.com/luuisaguilar/deep-audit-knowledge-engine.git
cd deep-audit-knowledge-engine
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

### 3. Credenciales

Crear el archivo `.env` en la raíz del proyecto (NO commitear):

```env
GEMINI_API_KEY=tu_clave_aqui
GITHUB_TOKEN=tu_pat_aqui
```

- **Gemini API Key**: console.cloud.google.com → APIs → Generative Language API
- **GitHub PAT**: github.com → Settings → Developer Settings → Personal Access Tokens → Fine-grained → permisos: `repo:read`, `metadata:read`

### 4. Arranque

```bash
streamlit run app.py
```

---

## Estado actual del proyecto

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
| `core/db.py` | Historial central, dedup, stats | 📊 Analytics |

### Infraestructura

| Módulo | Función |
|--------|---------|
| `config.py` | Singleton Gemini + `generate_with_retry()` con tenacity |
| `core/db.py` | Persistencia central `knowledge.db` — dedup + analytics |
| `core/prompt_loader.py` | Renderizador de prompts Jinja2 desde `prompts/*.md` |
| `prompts/*.md` | 6 templates de prompts editables sin tocar código |

### Módulos planeados

| Módulo | Sprint | Función |
|--------|--------|---------|
| `audio_transcriber.py` + `podcast_analyzer.py` | Sprint 6 | Podcast/Audio ingestion |
| `core/search_engine.py` | Sprint 7 | Búsqueda semántica con ChromaDB |

---

## Arquitectura clave

```
app.py                        ← UI pura, sin lógica de negocio (8 tabs)
  ↓ importa
config.py                     ← Gemini singleton + reintentos (ÚNICO punto de IA)
core/db.py                    ← Persistencia central (knowledge.db)
core/prompt_loader.py         ← Renderiza templates Jinja2 de prompts/
  ↓ usados por todos
*_analyzer.py                 ← Lógica pura, sin imports de streamlit
  ↓ resultados
save_note()                   ← Escribe en Obsidian Vault (ruta configurable en sidebar)
record_ingestion()            ← Registra en knowledge.db (dedup + analytics)
```

**Regla de oro**: ningún `_analyzer.py` importa `streamlit`. Toda la UI vive en `app.py`.

---

## Deduplicación

Antes de procesar cualquier URL, `app.py` llama a `has_been_processed(url)`.
Si la URL ya tiene un registro con `status='success'` en `knowledge.db`, se muestra "⏭️ Ya procesado" y se salta.
Esto evita re-gastar cuota de Gemini y duplicar notas en Obsidian.

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
| `40_NotebookLM/` | Notas de contexto del Source Pack |
| `40_Agente_Sync/` | Reportes de AuctionBot, DexScreener |
| `50_Recetas/` | Recetas y listas del súper |

---

## Decisiones importantes

Ver `docs/ADR.md` para el razonamiento completo. Resumen:

- **config.py centraliza todo lo de Gemini** — no tocar la inicialización del modelo en otro lado
- **knowledge.db para dedup y analytics** — registra cada ingesta cross-module
- **Prompts externalizados en Jinja2** — iterar calidad sin tocar código Python
- **SQLite local para RSS** — no Supabase (demasiado para uso personal, sin concurrencia)
- **NotebookLM sin API** — el Source Pack es el workaround hasta que Google publique API

---

## Cuotas y límites

| Servicio | Límite free tier | Manejo actual |
|----------|-----------------|---------------|
| Gemini 2.0 Flash | 15 req/min, 1500 req/día | `tenacity` backoff exponencial en `config.py` |
| GitHub API sin auth | 60 req/hora | `GITHUB_TOKEN` en `.env` → 5000 req/hora |
| YouTube Transcript API | Sin límite conocido | Caché en `session_state.transcript_cache` |

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

## Despliegue en Proxmox (opcional)

```bash
# Dentro del contenedor LXC
chmod +x setup_proxmox.sh
./setup_proxmox.sh

# El servicio systemd se llama youtube_service
systemctl status youtube_service
```
