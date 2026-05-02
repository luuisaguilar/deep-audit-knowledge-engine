# 🟢 Deep Audit Knowledge Engine - Status Report

## 📍 Estado General del Proyecto
**Fase Actual:** Fase 5 (Orquestación y Automatización)
**Sprints Completados:** Sprint 1 al 8
**Próximo Objetivo:** Sprint 9 (Orquestación con n8n)

El proyecto ha transicionado con éxito de un prototipo basado en scripts a un sistema robusto, modular y listo para la nube. Se ha consolidado una arquitectura centralizada para el manejo de LLMs (Gemini), persistencia y búsqueda vectorial (Supabase pgvector), plantillas (Jinja2) y tracking financiero preciso (Gemini tokens).

---

## ✅ Lo que se ha logrado (Hasta Sprint 8)

### 1. Centralización y Seguridad
*   **Gemini 2.0 Flash Centralizado:** Todo el tráfico pasa por un único embudo en `config.py` con políticas de reintento (`tenacity`) para evitar bloqueos por cuotas.
*   **Variables de Entorno:** Se eliminaron las credenciales hardcodeadas. Se usa un `.env` estricto (`GEMINI_API_KEY`, `GITHUB_TOKEN`, `SUPABASE_*`, `CLOUDFLARE_*`).

### 2. Motores de Ingesta Funcionales
Se han completado y estandarizado 5 motores de ingesta, todos con barras de progreso y manejo de errores:
*   📺 **YouTube Analyzer:** Descarga de transcripciones, análisis de contenido y resúmenes.
*   💻 **GitHub Deep Audit:** Exploración de repositorios vía API y generación de wikis técnicas.
*   🌐 **Web Analyzer:** Scraping de artículos técnicos limpios.
*   🍳 **Digital Chef:** Extracción de recetas estructuradas y listas de compra.
*   📰 **RSS Monitor:** Procesamiento automático de feeds de noticias tecnológicas.

### 3. Sistema de Prompts Dinámicos
*   **Jinja2 Templates:** Los prompts ya no están en el código fuente. Se almacenan en `prompts/*.md`, permitiendo modificar el tono y la estructura de salida sin programar.

### 4. Persistencia e Infraestructura de Producción (Sprint 5.5)
*   **Migración a Supabase:** Se reemplazó SQLite (`knowledge.db`) por PostgreSQL en la nube para registrar cada ingesta (URL, tipo, status, tokens). Esto permite analítica global y deduplicación en todos los motores.
*   **Contenedores (Docker):** El sistema fue empacado en una imagen ligera (`python:3.11-slim` + `ffmpeg`).
*   **Cloudflare Tunnel:** Se configuró un sidecar en `docker-compose.yml` para exponer la aplicación de forma segura mediante HTTPS sin necesidad de abrir puertos (port-forwarding).
*   **Deduplicación Robusta:** Si se detecta una URL previamente procesada con éxito, el sistema la omite. Se añadió un botón "🔄 Forzar Re-proceso" para anular esto si es necesario.

### 5. Ingesta de Audio y Podcasts (Sprint 6)
*   **Soporte Nativo Gemini 2.0:** Se eliminó la dependencia local de Whisper, usando la API nativa de archivos de Gemini para transcribir y analizar archivos de audio y podcast subidos desde la UI (`mp3`, `wav`, `m4a`, `ogg`).

### 6. Buscador Semántico (RAG) (Sprint 7)
*   **Vectorización Automática:** Se implementó `core/search_engine.py` para generar fragmentos y vectores matemáticos (embeddings) automáticamente de todas las notas generadas.
*   **Búsqueda Vectorial (pgvector):** Se migró a usar `pgvector` directamente en Supabase para evitar añadir bases de datos locales como ChromaDB, manteniendo la arquitectura centralizada en la nube.
*   **Respuestas en Lenguaje Natural:** El nuevo Tab "Buscador" genera respuestas consultando la base de conocimiento utilizando Gemini y citas directas de las notas originales.

### 7. Tracking de Tokens y Costos (Sprint 8)
*   **Medición en Tiempo Real:** El sistema ahora captura los `usage_metadata` de Gemini 2.0 Flash (`prompt_tokens` y `completion_tokens`) de manera invisible sin romper el flujo de trabajo.
*   **Costos Históricos:** La base de datos de Supabase registra el consumo por cada ingesta y el tab de *Analytics* refleja el costo estimado en dólares utilizando los *rates* oficiales de la API de Google.

---

## 🏗️ Estado Arquitectónico Actual

*   **Frontend:** Streamlit (`app.py` - única responsable de la UI).
*   **Lógica de Negocio:** Archivos `*_analyzer.py` (puros, sin dependencias de UI).
*   **Base de Datos (Operativa):** Supabase (PostgreSQL) para historiales y analytics.
*   **Base de Datos Vectorial:** Supabase (`pgvector` via `document_chunks`).
*   **Base de Datos (Configuración):** SQLite local (`rss_feeds.db`) para gestionar suscripciones RSS.
*   **Almacenamiento (Conocimiento):** Sistema de archivos local (Obsidian Vault) persistido vía volumen de Docker.

---

## ⏳ Lo que queda pendiente (Roadmap)

### Sprint 9: Orquestación y Automatización (En Progreso 🟢)
*   **Arquitectura Dual:** Se introdujo `api.py` (FastAPI) para operar en paralelo a `app.py` (Streamlit).
*   **Routing Inteligente:** Endpoint `/inspect-url` clasifica enlaces (YouTube, GitHub, Web, Audio) y devuelve opciones de acciones dinámicamente.
*   **Background Processing:** Endpoint `/process-url` encola tareas pesadas (evitando bloqueos HTTP) y soporta webhooks para avisar a sistemas externos.
*   **Integración n8n/Telegram:** Se generó el workflow maestro (`n8n_telegram_workflow.json`) para que un bot de Telegram actúe como interfaz móvil del Knowledge Engine.
*   **Próximo Paso Inmediato:** Importar el workflow en el n8n local del usuario y hacer pruebas end-to-end enviando un link desde Telegram.

### Sprint 10: Intelligence Briefings (Notificaciones)
*   Integración con Telegram/Slack: El sistema debe enviar un resumen matutino con lo más importante ingestrado el día anterior.

### Sprint 11: Soporte Local Confidencial (Ollama)
*   Añadir capacidad de intercambiar el LLM principal (Gemini) por un modelo local ejecutado vía Ollama (ej. Llama 3 o Phi-3) para auditar documentos altamente confidenciales sin que la data salga de tu red.
