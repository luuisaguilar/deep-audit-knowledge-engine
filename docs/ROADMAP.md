# Vision Roadmap: Deep Audit Knowledge Engine

Este documento marca el camino evolutivo del motor para convertirse en un sistema de inteligencia personal de grado profesional.

---

## Fase 1: Knowledge Hub Base (Estado: ✅ Completado)

- YouTube, GitHub y Web como fuentes primarias de ingesta.
- Integración directa con Obsidian Vault (auto-save con YAML frontmatter).
- UX de selección masiva con `st.data_editor`.
- Digital Chef: extracción especializada de recetas de cocina.
- Knowledge Sync: puente con otros agentes (AuctionBot, DexScreener).

## Fase 2: Arquitectura Limpia & Foundation (Estado: ✅ Completado)

- **Sprint 3.5** ✅: Seguridad (`.env`), `config.py` centralizado, caché de transcripciones, modo Individual en Knowledge Sync.
- **Sprint 4** ✅: Foundation Sprint:
  - `core/db.py` — persistencia central `knowledge.db` con dedup por URL.
  - `core/prompt_loader.py` + `prompts/` — prompts externalizados como templates Jinja2.
  - Tab **📊 Analytics** — KPIs, gráficas por tipo, timeline, tabla de recientes, export CSV.
  - Deduplicación automática en YT, GH, Web.
  - Error handling con status `failed` + `error_message` persistidos.

## Fase 3: Nuevas Fuentes & Persistencia Completa (En curso → Sprint 5-6)

- **Sprint 5** 🔲: Extender `record_ingestion()` a RSS y Chef. Agregar "Forzar Re-proceso". Token tracking.
- **Sprint 6** 🔲: Audio/Podcast Ingestion — transcripción con Gemini audio nativo o `faster-whisper`.

## Fase 4: Inteligencia sobre el Vault (Q3 2026)

- **RAG local**: ChromaDB para búsqueda semántica sobre notas generadas. Tab "🔍 Vault Search".
- **Knowledge Graph automático**: Extraer entidades y relaciones, generar `[[wikilinks]]` entre notas.
- **Análisis Multi-Repo GitHub**: Comparar arquitecturas de dos repositorios lado a lado.

## Fase 5: Automatización (Q4 2026)

- **n8n Orchestrator**: Webhook que dispara auditorías cuando un canal de YouTube sube un nuevo video.
- **Daily Intelligence Brief**: Resumen diario de todo lo ingerido, enviado a Telegram o Slack.
- **Ingesta programada**: Scheduler que ejecuta RSS + canales favoritos sin intervención manual.
- **Integración DocGrab**: DocGrab crawlea documentación completa, Knowledge Engine la analiza.

## Fase 6: Ecosistema Local (Q1 2027)

- **Local LLM**: Soporte para Llama 3 / Mistral vía Ollama para auditorías offline de código privado.
- **Vision Audit**: Análisis visual de screenshots de sitios web con modelos multimodales.
- **Voice Interface**: Comandos de voz para solicitar auditorías desde dispositivos móviles.
- **Supabase Migration**: Migrar `knowledge.db` a Supabase + pgvector para multi-dispositivo y búsqueda semántica nativa.

---

## Estrategia de Crecimiento

El sistema se mantiene modular. Cada nueva fuente de ingesta sigue el mismo patrón:

```
prompts/{fuente}_{tipo}.md    — template de prompt editable
{fuente}_analyzer.py          — lógica pura sin UI
core/db.py                    — record_ingestion() al completar
app.py (tab nuevo)            — solo UI y orquestación
```

Toda la IA pasa por `config.generate_with_retry()` — un único punto de control para cuotas, reintentos y cambios de modelo.
Los prompts se editan sin tocar código via `core/prompt_loader.py` + `prompts/*.md`.
