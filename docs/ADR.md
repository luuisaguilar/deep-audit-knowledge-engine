# Architecture Decision Records (ADR)

---

## ADR-001: Streamlit como Dashboard

- **Estado:** ✅ Aceptado
- **Contexto:** Necesidad de una interfaz rápida para listar cientos de videos y permitir selección granular.
- **Decisión:** Usar Streamlit por su soporte nativo de `st.data_editor` y facilidad de despliegue en contenedores.
- **Consecuencia:** Desarrollo rápido, pero limitaciones en control fino de eventos de red y JavaScript.

---

## ADR-002: Gemini 2.0 Flash como modelo de IA

- **Estado:** ✅ Aceptado
- **Contexto:** Latencia de análisis masivo y costos en free tier.
- **Decisión:** Gemini Flash es ~10x más rápido que Pro y tiene ventana de contexto suficiente para transcripciones largas y código.
- **Consecuencia:** Bajo costo y alta velocidad, pero requiere manejo activo de cuotas (rate limits).

---

## ADR-003: GitHub vía Trees API (sin clonar)

- **Estado:** ✅ Aceptado
- **Contexto:** Clonar repositorios completos es lento y consume disco innecesariamente.
- **Decisión:** Usar la API recursiva de `trees` para mapear la estructura y descargar solo archivos "ADN" (hasta 12 archivos críticos).
- **Consecuencia:** Auditorías en segundos, pero dependiente de conectividad y tokens de GitHub.

---

## ADR-004: Obsidian-First como persistencia primaria

- **Estado:** ✅ Aceptado
- **Contexto:** Las auditorías deben ser persistentes y útiles para el sistema de notas personal (Zettelkasten).
- **Decisión:** Priorizar Markdown con YAML Properties e ingesta directa en el Vault de Obsidian sobre bases de datos relacionales.
- **Consecuencia:** Local-first, altamente indexable por Obsidian y NotebookLM, pero requiere configuración manual de rutas.

---

## ADR-005: config.py como punto único de acceso a Gemini

- **Estado:** ✅ Aceptado — Sprint 3.5
- **Contexto:** La clave `GEMINI_API_KEY` estaba hardcodeada en 4 archivos distintos. La lógica de reintentos también estaba duplicada.
- **Decisión:** Crear `config.py` que carga `.env` con `python-dotenv`, inicializa el modelo Gemini una sola vez, y expone `generate_with_retry(prompt)` decorada con `tenacity` (backoff exponencial: 30s, 60s, 90s).
- **Consecuencia:** Un único punto de control para cuotas, modelo y reintentos. Ningún módulo configura Gemini por su cuenta. Cambiar de modelo o proveedor requiere editar un solo archivo.

---

## ADR-006: .env para secretos — nunca en código fuente

- **Estado:** ✅ Aceptado — Sprint 3.5
- **Contexto:** `GEMINI_API_KEY` y `GITHUB_TOKEN` estaban en texto plano en el código fuente. Riesgo de exposición si el código llega a un repositorio.
- **Decisión:** Mover todos los secretos a `.env` con `python-dotenv`. Agregar `.env` al `.gitignore`. El código solo lee variables de entorno con `os.getenv()`.
- **Consecuencia:** Las credenciales no viajan con el código. Onboarding requiere crear `.env` manualmente (documentado en HANDOFF.md).

---

## ADR-007: SQLite local para RSS (no Supabase)

- **Estado:** 🔲 Propuesto — Sprint 4
- **Contexto:** El RSS Monitor necesita persistencia para recordar artículos ya procesados entre sesiones. La opción alternativa era Supabase (ya planeado en Sprint 4 original).
- **Decisión:** Usar SQLite local (`rss_feeds.db`) en lugar de Supabase para la persistencia de RSS. SQLite no requiere cuenta externa, funciona offline, y es suficiente para uso personal.
- **Consecuencia:** Sin dependencias externas ni costos adicionales. La DB vive en el directorio del proyecto. No es apta para múltiples usuarios concurrentes (no es el caso de uso).
- **Nota:** Supabase sigue siendo válido para la caché de análisis de Gemini (ADR futuro).

---

## ADR-008: faster-whisper para transcripción de audio

- **Estado:** 🔲 Propuesto — Sprint 6
- **Contexto:** Para ingestar podcasts y audio se necesita transcripción. Opciones evaluadas: OpenAI Whisper API (costo por minuto), Whisper original (lento en CPU), faster-whisper (optimizado con CTranslate2).
- **Decisión:** Usar `faster-whisper` con modelo `base` (74MB). Local, gratuito, y procesa 1 hora de audio en ~3-5 minutos en CPU moderno. Retorna `(texto, idioma)` — mismo contrato que `get_transcript()` de YouTube.
- **Consecuencia:** Sin costo por token de audio. Primera ejecución descarga el modelo (~74MB). En Windows requiere que Visual C++ Redistributable esté instalado.

---

## ADR-009: NotebookLM como destino complementario (sin API)

- **Estado:** 🔲 Propuesto — Sprint 5
- **Contexto:** NotebookLM no tiene API pública. Se evaluó si era posible automatizar la creación de cuadernos.
- **Decisión:** No automatizar la creación del cuaderno. En su lugar, generar un "Source Pack" (`.txt` de URLs + `.md` de contexto) que el usuario importa manualmente en NotebookLM en menos de 1 minuto.
- **Consecuencia:** El flujo no es 100% automático, pero es el máximo posible sin API. El valor está en la curación y el enriquecimiento del contexto, no en la automatización del click.
- **Revisión:** Si NotebookLM publica una API, este ADR debe revisarse para automatizar la creación del cuaderno via `notebooklm_pack.py`.
