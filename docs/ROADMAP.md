# Vision Roadmap: Deep Audit Knowledge Engine

Este documento marca el camino evolutivo del motor para convertirse en un sistema de inteligencia personal de grado profesional.

---

## Fase 1: Knowledge Hub Base (Estado: ✅ Completado)

- YouTube, GitHub y Web como fuentes primarias de ingesta.
- Integración directa con Obsidian Vault (auto-save con YAML frontmatter).
- UX de selección masiva con `st.data_editor`.
- Digital Chef: extracción especializada de recetas de cocina.
- Knowledge Sync: puente con otros agentes (AuctionBot, DexScreener).

## Fase 2: Arquitectura Limpia & Nuevas Fuentes (Estado: ✅ En curso — Sprint 3.5 → 6)

- **Sprint 3.5** ✅: Seguridad (`.env`), `config.py` centralizado, caché de transcripciones, modo Individual en Knowledge Sync.
- **Sprint 4** 🔲: RSS Feed Monitor — monitoreo automático de blogs con SQLite local.
- **Sprint 5** 🔲: NotebookLM Source Pack — exportar fuentes curadas para importar a NotebookLM en 1 click.
- **Sprint 6** 🔲: Audio/Podcast Ingestion — transcripción local con `faster-whisper`.

## Fase 3: Inteligencia sobre el Vault (Q3 2026)

- **RAG local**: Gemini puede consultar el Obsidian Vault antes de generar nuevas notas. Evita duplicados y enriquece el contexto.
- **Knowledge Graph automático**: Generar `[[wikilinks]]` entre notas relacionadas en el momento del análisis.
- **Análisis Multi-Repo GitHub**: Comparar arquitecturas de dos repositorios lado a lado.
- **Persistencia híbrida**: SQLite local como caché de análisis para no re-gastar cuota de Gemini.

## Fase 4: Automatización (Q4 2026)

- **n8n Orchestrator**: Webhook que dispara auditorías cuando un canal de YouTube sube un nuevo video.
- **Daily Intelligence Brief**: Resumen diario de todo lo ingerido, enviado a Telegram o Slack.
- **Ingesta programada**: Scheduler que ejecuta RSS + canales favoritos sin intervención manual.

## Fase 5: Ecosistema Local (Q1 2027)

- **Local LLM**: Soporte para Llama 3 / Mistral vía Ollama para auditorías offline de código privado.
- **Vision Audit**: Análisis visual de screenshots de sitios web con modelos multimodales.
- **Voice Interface**: Comandos de voz para solicitar auditorías desde dispositivos móviles.

---

## Estrategia de Crecimiento

El sistema se mantiene modular. Cada nueva fuente de ingesta sigue el mismo patrón:

```
{fuente}_analyzer.py   — lógica pura sin UI
{fuente}_db.py         — acceso a datos si necesita persistencia
app.py (tab nuevo)     — solo UI y orquestación
```

Toda la IA pasa por `config.generate_with_retry()` — un único punto de control para cuotas, reintentos y cambios de modelo.
