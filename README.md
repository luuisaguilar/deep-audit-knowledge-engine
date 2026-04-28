# 🧠 Deep Audit Knowledge Engine

Ecosistema multi-agente para la ingesta inteligente de conocimiento desde YouTube, GitHub, Web y RSS hacia Obsidian. Impulsado por **Gemini 2.0 Flash**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B.svg)](https://streamlit.io/)

## 🚀 Inicio Rápido

```bash
# 1. Clonar y entrar al directorio
git clone https://github.com/luuisaguilar/deep-audit-knowledge-engine.git
cd deep-audit-knowledge-engine

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt

# 3. Configurar credenciales
cp .env.example .env
# Editar .env con tus claves de Gemini y GitHub

# 4. Ejecutar
streamlit run app.py
```

## 🏗️ Arquitectura

```
app.py                        ← UI pura (Streamlit), sin lógica de negocio
  ↓ importa
config.py                     ← Gemini singleton + generate_with_retry (tenacity)
core/db.py                    ← Persistencia central (knowledge.db — SQLite)
core/prompt_loader.py         ← Renderizador de prompts Jinja2
  ↓ usados por
*_analyzer.py                 ← Lógica pura, sin imports de Streamlit
prompts/*.md                  ← Templates de prompts editables sin tocar código
```

**Regla de oro**: ningún `_analyzer.py` importa `streamlit`. Toda la UI vive en `app.py`.

## 📑 Módulos (8 Tabs)

| Tab | Módulo | Función |
|-----|--------|---------|
| 📺 YouTube Analysis | `youtube_analyzer.py` | Indexa canales, descarga transcripciones, genera auditorías técnicas |
| 💻 GitHub Deep Audit | `github_analyzer.py` | Trees API recursiva, archivos ADN (hasta 12), genera Wiki técnica |
| 🌐 Web Ingestion | `web_analyzer.py` | Scraping con BS4, análisis Zettelkasten |
| 🍳 Digital Chef | `cooking_analyzer.py` | Recetas de cocina + lista del súper consolidada |
| 📰 RSS Monitor | `rss_manager.py` + `rss_db.py` | Monitoreo de feeds RSS con persistencia SQLite |
| 🧠 Obsidian Sync | `knowledge_sync.py` | Puente con agentes externos (AuctionBot, DexScreener) |
| 📚 NotebookLM Pack | `notebooklm_pack.py` | Source Pack de URLs + nota de contexto para NotebookLM |
| 📊 Analytics | `core/db.py` | KPIs, ingestas por tipo, timeline, historial, export CSV |

## 🛡️ Persistencia y Deduplicación

Todas las ingestas (YouTube, GitHub, Web) se registran en `knowledge.db`. Si un URL ya fue procesado exitosamente, se muestra **⏭️ Ya procesado** y se salta automáticamente. Esto evita re-gastar cuota de Gemini y duplicar notas.

## ✏️ Sistema de Prompt Templates

Los prompts de IA están externalizados en archivos Markdown editables en `prompts/`:

| Template | Utilizado por |
|----------|---------------|
| `_base_system.md` | Prompt base compartido (Zettelkasten persona) |
| `youtube_analysis.md` | YouTube analyzer |
| `github_wiki.md` | GitHub analyzer |
| `web_curation.md` | Web analyzer |
| `rss_digest.md` | RSS analyzer |
| `cooking_recipe.md` | Digital Chef |

Para iterar la calidad de las notas generadas, solo edita los archivos `.md` — sin tocar código Python.

## 📁 Carpetas en Obsidian

| Carpeta | Contenido |
|---------|-----------|
| `10_YouTube/` | Auditorías técnicas de videos |
| `20_GitHub/` | Wikis de repositorios |
| `30_Web/` | Artículos web |
| `40_NotebookLM/` | Notas de contexto del Source Pack |
| `40_Agente_Sync/` | Reportes de bots externos |
| `50_Recetas/` | Recetas y listas del súper |

## ⚠️ Cuotas de Gemini

| Servicio | Límite free tier | Manejo |
|----------|-----------------|--------|
| Gemini 2.0 Flash | 15 req/min, 1500 req/día | `tenacity` backoff exponencial en `config.py` |
| GitHub API con token | 5000 req/hora | `GITHUB_TOKEN` en `.env` |
| YouTube Transcript API | Sin límite conocido | Caché en `session_state.transcript_cache` |

## 📖 Documentación

| Documento | Descripción |
|-----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Diagrama del sistema, capas, y patrones de diseño |
| [BACKLOG.md](docs/BACKLOG.md) | Sprints, tareas, y definición de hecho |
| [ROADMAP.md](docs/ROADMAP.md) | Visión evolutiva del proyecto |
| [ADR.md](docs/ADR.md) | Architecture Decision Records |
| [DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) | Esquemas SQLite |
| [FLOWS.md](docs/FLOWS.md) | Diagramas de flujo de datos (Mermaid) |
| [HANDOFF.md](docs/HANDOFF.md) | Guía de onboarding para nuevos contribuidores |

## 📝 License

[MIT](LICENSE)
