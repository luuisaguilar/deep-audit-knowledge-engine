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

### Sprint 5: RSS/Chef Persistence + Hardening (Estado: 🔲 Próximo)
- **Objetivo**: Extender persistencia a RSS y Chef, agregar control de dedup granular.
- **Tareas**:
    - [ ] Wire `record_ingestion()` en el tab RSS Monitor.
    - [ ] Wire `record_ingestion()` en el tab Digital Chef.
    - [ ] Agregar checkbox "🔄 Forzar Re-proceso" para overridear dedup cuando necesario.
    - [ ] Agregar `tokens_estimated` tracking via metadata de respuesta de Gemini.
    - [ ] Agregar columna `tokens_estimated` al dashboard Analytics.

### Sprint 6: Audio/Podcast Ingestion (Estado: 🔲 Planeado)
- **Objetivo**: Transcripción de podcasts/audio directo con Gemini (audio nativo) o faster-whisper.
- **Archivos a crear**: `audio_transcriber.py`, `podcast_analyzer.py`, `prompts/podcast_analysis.md`.
- **Cambios a existentes**: nuevo tab en `app.py`, dependencia de audio en `requirements.txt`.
- **Pruebas Mínimas**:
    - Subir un `.mp3` de prueba (<5 min) y verificar transcripción correcta.
    - Verificar que el episodio genera una nota con YAML válido.
    - Verificar que aparece en Analytics.

### Sprint 7: Búsqueda Semántica sobre el Vault (Estado: 🔲 Planeado)
- **Objetivo**: RAG local con ChromaDB para consultar el conocimiento acumulado.
- **Archivos a crear**: `core/search_engine.py`.
- **Cambios a existentes**: nuevo tab "🔍 Vault Search" en `app.py`, `chromadb` en `requirements.txt`.

## 2. Definición de Hecho (DoD)
Para que un sprint se considere terminado, debe cumplir:
1. El código no rompe la ejecución de `streamlit run app.py`.
2. Las notas generadas pasan el validador de YAML (pueden ser leídas por Obsidian Properties).
3. Se ha actualizado el archivo `docs/ADR.md` con las nuevas decisiones arquitectónicas.
4. Los cambios de seguridad (claves, rutas) no están hardcodeados en el código fuente.
5. Las ingestas se registran en `knowledge.db` con status correcto.
