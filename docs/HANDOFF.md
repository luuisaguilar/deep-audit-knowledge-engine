# Project Handoff: Deep Audit Knowledge Engine

## ¿Qué es esto?

Motor de ingesta de conocimiento técnico. Toma contenido de YouTube, GitHub, blogs web, podcasts y feeds RSS, lo analiza con Gemini 2.0 Flash, y genera notas estructuradas en Markdown directamente en un vault de Obsidian. También exporta packs de fuentes curadas para NotebookLM.

---

## Setup desde cero

### 1. Requisitos previos
- Python 3.11+
- Visual C++ Redistributable (Windows) — necesario para `faster-whisper` en Sprint 6

### 2. Entorno

```powershell
cd "Agentes Youtube"
python -m venv venv
.\venv\Scripts\activate
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

```powershell
streamlit run app.py
```

---

## Estado actual del proyecto

### Módulos implementados

| Módulo | Función | Tab en la app |
|--------|---------|---------------|
| `youtube_analyzer.py` | Indexa canal, descarga transcripciones, analiza con Gemini | YouTube Analysis |
| `github_analyzer.py` | Trees API, archivos ADN, genera Wiki técnica | GitHub Deep Audit |
| `web_analyzer.py` | Scraping con BS4, análisis Zettelkasten | Web Ingestion |
| `cooking_analyzer.py` | Extracción de recetas + lista del súper | Digital Chef |
| `knowledge_sync.py` | Lee DBs de agentes externos, exporta a Obsidian | Obsidian Sync |
| `config.py` | Singleton Gemini + `generate_with_retry()` con tenacity | (interno) |

### Módulos planeados

| Módulo | Sprint | Función |
|--------|--------|---------|
| `rss_db.py` + `rss_manager.py` | Sprint 4 | RSS Monitor con SQLite |
| `notebooklm_pack.py` | Sprint 5 | Source Pack para NotebookLM |
| `audio_transcriber.py` + `podcast_analyzer.py` | Sprint 6 | Podcast/Audio con faster-whisper |

---

## Arquitectura clave

```
app.py                    ← UI pura, sin lógica de negocio
  ↓ importa
config.py                 ← Gemini singleton + reintentos (ÚNICO punto de IA)
  ↓ usado por todos
*_analyzer.py             ← Lógica pura, sin imports de streamlit
  ↓ resultados
save_note()               ← Escribe en Obsidian Vault (ruta configurable en sidebar)
```

**Regla de oro**: ningún `_analyzer.py` importa `streamlit`. Toda la UI vive en `app.py`.

---

## Carpetas de Obsidian generadas

| Carpeta | Contenido |
|---------|-----------|
| `10_YouTube/` | Auditorías técnicas de videos |
| `20_GitHub/` | Wikis de repositorios |
| `30_Web/` | Artículos web + subdirectorio `RSS/` (Sprint 4) |
| `40_NotebookLM/` | Notas de contexto del Source Pack (Sprint 5) |
| `40_Agente_Sync/` | Reportes de AuctionBot, DexScreener |
| `50_Recetas/` | Recetas y listas del súper |
| `60_Podcasts/` | Episodios transcritos (Sprint 6) |

---

## Decisiones importantes

Ver `docs/ADR.md` para el razonamiento completo. Resumen:

- **config.py centraliza todo lo de Gemini** — no tocar la inicialización del modelo en otro lado
- **SQLite local para RSS** — no Supabase (demasiado para uso personal, sin concurrencia)
- **faster-whisper modelo `base`** — 74MB, buena precisión, corre en CPU
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

```powershell
# Requiere que Playwright esté instalado
playwright install chromium

# Ejecutar tests E2E
pytest test_app_ui.py -v
```

Los tests levantan una instancia de Streamlit en el puerto 8502 y verifican la existencia de tabs y elementos UI clave.

---

## Despliegue en Proxmox (opcional)

```bash
# Dentro del contenedor LXC
chmod +x setup_proxmox.sh
./setup_proxmox.sh

# El servicio systemd se llama youtube_service
systemctl status youtube_service
```
