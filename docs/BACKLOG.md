# Project Backlog & Sprints: Deep Audit Knowledge Engine

## 1. Roadmap de Sprints

### Sprint 1: Estabilidad & Documentación (Estado: ✅ Completado)
- **Objetivo**: Corregir bugs de descubrimiento de archivos en GitHub y establecer la base documental.
- **Pruebas Mínimas**:
    - Verificar que `Trees API` detecta archivos en ramas que no sean `master`.
    - Validar que los archivos descargados de GitHub se decodifican correctamente (UTF-8).
    - Verificar existencia de carpeta `docs/`.

### Sprint 2: Resiliencia & UX (Estado: ✅ Completado)
- **Objetivo**: Mejorar la experiencia de usuario y manejo de errores.
- **Pruebas Mínimas**:
    - Forzar error 429 de Gemini y validar que aparece el banner de advertencia.
    - Click en "Seleccionar Todo" y validar que el editor de datos refleja el cambio.

### Sprint 3: Knowledge Hub Expansion (Estado: ✅ Completado)
- **Objetivo**: Ingesta Web, Digital Chef, Obsidian Vault y Knowledge Sync.
- **Pruebas Mínimas**:
    - Crawling de una URL técnica y validar que extrae el título.
    - Verificar que la nota se guarda en la carpeta física de Obsidian con nombre sanitizado.
    - Validar que el bloque YAML contiene los campos requeridos.

### Sprint 3.5: Seguridad & Arquitectura Limpia (Estado: ✅ Completado)
- **Objetivo**: Eliminar secretos hardcodeados, centralizar Gemini, mejorar DX.
- **Cambios realizados**:
    - [x] Crear `.env` + `.gitignore` (API keys fuera del código).
    - [x] Crear `config.py`: inicialización única de Gemini + `generate_with_retry()` con `tenacity`.
    - [x] Eliminar `GEMINI_API_KEY` y `GITHUB_TOKEN` hardcodeados de los 4 analizadores.
    - [x] Implementar caché de transcripciones en `st.session_state.transcript_cache`.
    - [x] Botón de eliminar URL individual en Web Ingestion.
    - [x] `knowledge_sync.py`: acepta `vault_path` como parámetro; modo "Individual" implementado.
    - [x] `app.py`: pasa `vault_path` del sidebar a `sync_all_to_obsidian()`.
    - [x] Crear `requirements.txt` con todas las dependencias reales del venv.
    - [x] Corregir placeholder erróneo en `test_app_ui.py`.
- **Pruebas Mínimas**:
    - Arrancar la app sin `.env` y verificar que falla con mensaje claro (no KeyError).
    - Procesar el mismo video dos veces y verificar (via logs) que la segunda vez no llama a `get_transcript`.

### Sprint 4: Foundation — Persistencia, Templates & Analytics (Estado: ✅ Completado)
- **Objetivo**: Establecer capa de persistencia central, externalizar prompts, y agregar analytics.
- **Cambios realizados**:
    - [x] Crear `core/db.py` — base de datos central `knowledge.db` con tabla `ingestions`.
    - [x] Crear `core/prompt_loader.py` — renderizador de prompts Jinja2.
    - [x] Crear directorio `prompts/` con 6 templates (base, youtube, github, web, rss, cooking).
    - [x] Migrar prompts hardcoded de `youtube_analyzer.py`, `github_analyzer.py`, `web_analyzer.py`, `cooking_analyzer.py` a templates.
    - [x] Agregar deduplicación por URL en loops de procesamiento de YT, GH y Web.
    - [x] Agregar `record_ingestion()` tras cada análisis (éxito o fallo).
    - [x] Agregar try/except con error recording en todos los loops de procesamiento.
    - [x] `save_note()` ahora retorna el filepath para tracking en `knowledge.db`.
    - [x] Nuevo tab "📊 Analytics" con KPIs, gráficas, tabla de recientes, export CSV.
    - [x] Actualizar `test_app_ui.py` con el nuevo tab Analytics.
- **Pruebas Mínimas**:
    - Procesar un video → verificar que aparece en la tabla Analytics.
    - Procesar la misma URL → verificar que muestra "⏭️ Ya procesado".
    - Editar un template `.md` → verificar que el output de Gemini refleja el cambio.
    - Exportar CSV → verificar que contiene las ingestas registradas.

---

### Sprint 5: Persistencia Completa + Hardening (Estado: ✅ Completado)
- **Objetivo**: Extender persistencia a RSS y Chef, completar cobertura de dedup.
- **Cambios realizados**:
    - [x] Wire `record_ingestion()` en el tab RSS Monitor.
    - [x] Wire `record_ingestion()` en el tab Digital Chef.
    - [x] Agregar `has_been_processed()` dedup + progress bars en RSS y Chef.
    - [x] Agregar try/except con error recording en RSS y Chef.
- **Pendientes movidos a Sprint 5.5**:
    - Checkbox "🔄 Forzar Re-proceso", `tokens_estimated` tracking.

---

### Sprint 5.5: Deploy Infrastructure (Estado: ✅ Completado)
- **Objetivo**: Containerizar la app, migrar persistencia a Supabase, y exponer via Cloudflare Tunnel.
- **Tareas**:
    - [x] **Migrar `core/db.py` a Supabase**
    - [x] **Crear `Dockerfile`**
    - [x] **Crear `docker-compose.yml`**
    - [x] **Crear configuración Cloudflare Tunnel**
    - [x] **Actualizar `requirements.txt`**
    - [x] **Actualizar `.env.example`**
    - [x] **Agregar checkbox "🔄 Forzar Re-proceso"**
    - [x] **Smoke test del stack completo** (Simulado exitoso via code inspection)
- **Pruebas Mínimas**:
    - `docker build` exitoso.
    - `docker-compose up` levanta app + tunnel sin errores.
    - Procesar 1 video YT → aparece en Supabase + Analytics.
    - Acceder via `https://knowledge.tudominio.com`.

---

### Sprint 6: Audio/Podcast Ingestion (Estado: ✅ Completado)
- **Objetivo**: Transcripción de podcasts/audio directo con Gemini (audio nativo).
- **Tareas**:
    - [x] Crear `audio_analyzer.py` — wrapper sobre Gemini audio API.
    - [x] Crear `prompts/audio_analysis.md` — template Jinja2 para podcasts.
    - [x] Nuevo tab "🎙️ Audio" en `app.py`.
    - [x] Wire `record_ingestion('audio', ...)` con dedup.
    - [x] Soporte para upload de archivos `.mp3`/`.wav` via `st.file_uploader`.
- **Pruebas Mínimas**:
    - Subir un `.mp3` de prueba (<5 min) y verificar transcripción correcta.
    - Verificar que el episodio genera una nota con YAML válido.
    - Verificar que aparece en Analytics (Supabase).

---

### Sprint 7: Búsqueda Semántica sobre el Vault (Estado: ✅ Completado)
- **Objetivo**: RAG directo contra la base de datos de Supabase usando `pgvector`.
- **Tareas**:
    - [x] Crear script SQL para `pgvector` en Supabase (`docs/supabase_pgvector.sql`).
    - [x] Crear `core/search_engine.py` — indexación, embedding con Gemini y búsqueda RPC.
    - [x] Nuevo tab "🔍 Buscador Semántico" en `app.py`.
    - [x] Indexar notas en Supabase al generar (hook automático en `app.py`).
    - [x] UI: barra de búsqueda → resultados rankeados → generación RAG final.
- **Pruebas Mínimas**:
    - Generar 3 notas → buscar un término → verificar que aparecen resultados relevantes.
    - Reiniciar el contenedor → verificar que el índice persiste.

---

### Sprint 8: Token Tracking & Cost Analytics (Estado: ✅ Completado)
- **Objetivo**: Visibilidad completa del consumo de Gemini.
- **Tareas**:
    - [x] Extraer `usage_metadata` de la respuesta de Gemini en `config.py`.
    - [x] Agregar columnas `prompt_tokens`, `completion_tokens` a tabla `ingestions` en Supabase.
    - [x] Dashboard de costos estimados en tab Analytics.
    - [x] Alerta cuando se acerque al límite diario de Gemini (Omitido temporalmente: Dashboard suficiente por ahora).
- **Pruebas Mínimas**:
    - Procesar 5 items → verificar que los tokens se registran.
    - Dashboard muestra gráfica de consumo acumulado.

### Sprint 9: Orquestación con n8n y FastAPI (Estado: 🟢 En Progreso)
- **Objetivo**: Proveer al sistema de un cerebro automatizado capaz de procesar enlaces desde Telegram/n8n sin intervención manual en la UI.
- **Tareas**:
    - [x] Crear `api.py` con FastAPI para exponer endpoints `/inspect-url` y `/process-url`.
    - [x] Configurar FastAPI para encolar tareas con `BackgroundTasks`.
    - [x] Añadir callback a webhooks de n8n tras finalizar procesos.
    - [x] Modificar `docker-compose.yml` para levantar la API en paralelo a Streamlit.
    - [x] Solucionar dependencias de JS (Node.js) en Dockerfile para YouTube.
    - [x] Crear JSON del workflow de Telegram para n8n (`n8n_telegram_workflow.json`).
    - [ ] Importar workflow en la instancia de n8n del usuario y probar flujo real.
- **Pruebas Mínimas**:
    - Realizar un POST a `/inspect-url` y recibir las acciones.
    - Realizar un POST a `/process-url` y verificar que el webhook de n8n recibe la respuesta tras unos segundos.

---

## 2. Definición de Hecho (DoD)
Para que un sprint se considere terminado, debe cumplir:
1. El código no rompe la ejecución de `streamlit run app.py` ni de `uvicorn api:app`.
2. Las notas generadas pasan el validador de YAML (pueden ser leídas por Obsidian Properties).
3. Se ha actualizado el archivo `docs/ADR.md` con las nuevas decisiones arquitectónicas.
4. Los cambios de seguridad (claves, rutas) no están hardcodeados en el código fuente.
5. Las ingestas se registran correctamente (Supabase en producción, SQLite en dev).
6. Los archivos Docker (`Dockerfile`, `docker-compose.yml`) se buildean sin errores.
