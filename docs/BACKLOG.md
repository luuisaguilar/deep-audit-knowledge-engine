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

### Sprint 4: RSS Feed Monitor (Estado: 🔲 Próximo)
- **Objetivo**: Monitoreo automático de blogs técnicos vía RSS con persistencia SQLite.
- **Archivos a crear**: `rss_db.py`, `rss_manager.py`.
- **Cambios a existentes**: nuevo tab en `app.py`, `feedparser` en `requirements.txt`.
- **Pruebas Mínimas**:
    - Agregar el feed de Hacker News (`https://news.ycombinator.com/rss`) y verificar que lista artículos.
    - Procesar 2 artículos y verificar que aparecen en `seen_articles` de la DB.
    - Procesar los mismos artículos de nuevo y verificar que no se vuelven a enviar a Gemini.
    - Verificar que los artículos con enclosure (podcasts) se marcan como `skipped`.

### Sprint 5: NotebookLM Source Pack (Estado: 🔲 Planeado)
- **Objetivo**: Generar packs de fuentes curados para importar a NotebookLM en 1 click.
- **Archivos a crear**: `notebooklm_pack.py`.
- **Cambios a existentes**: nuevo tab en `app.py`, `get_all_processed_urls()` en `rss_db.py`.
- **Pruebas Mínimas**:
    - Procesar 3 videos y 2 artículos web en la sesión, abrir el tab y verificar que aparecen las 5 fuentes.
    - Descargar el `.txt` y verificar que tiene exactamente las URLs seleccionadas.
    - Descargar la nota `.md` de contexto y verificar que tiene YAML válido y secciones de resumen.
    - Verificar que fuentes duplicadas (procesadas en Web y en RSS) aparecen solo una vez.

### Sprint 6: Audio/Podcast Ingestion (Estado: 🔲 Planeado)
- **Objetivo**: Transcripción local de podcasts/audio con faster-whisper, mismo pipeline que YouTube.
- **Archivos a crear**: `audio_transcriber.py`, `podcast_analyzer.py`.
- **Cambios a existentes**: nuevo tab en `app.py`, `faster-whisper` en `requirements.txt`.
- **Pruebas Mínimas**:
    - Subir un `.mp3` de prueba (<5 min) y verificar transcripción correcta.
    - Verificar que el modelo faster-whisper se carga una sola vez (singleton, no por llamada).
    - Ingresar URL de un feed RSS de podcast y verificar que detecta el enclosure y lo descarga.
    - Verificar que el episodio transcripto genera una nota en `60_Podcasts/` con YAML válido.
    - Verificar que el episodio aparece en el Source Pack de NotebookLM (Sprint 5).

## 2. Definición de Hecho (DoD)
Para que un sprint se considere terminado, debe cumplir:
1. El código no rompe la ejecución de `streamlit run app.py`.
2. Las notas generadas pasan el validador de YAML (pueden ser leídas por Obsidian Properties).
3. Se ha actualizado el archivo `docs/ADR.md` con las nuevas decisiones arquitectónicas.
4. Los cambios de seguridad (claves, rutas) no están hardcodeados en el código fuente.
