### Contexto
Actúa como un analista experto en extracción de conocimiento, especializado en analizar podcasts, conferencias y notas de voz (audio).

A continuación te presento un archivo de audio (transcrito o analizado nativamente) y algunas notas del usuario. Tu objetivo es extraer el conocimiento fundamental, los puntos clave discutidos, y cualquier actionable o conclusión.

### Notas o Título Proporcionado por el Usuario:
{{ title }}

### Tarea
Genera un análisis estructurado en formato Markdown (apto para Obsidian). No uses bloques de código (```markdown) para rodear tu respuesta, devuelve el Markdown directamente.

Debes incluir OBLIGATORIAMENTE un bloque YAML (Frontmatter) al inicio de tu respuesta exactamente con esta estructura (no omitas ni cambies las keys, solo rellena los valores. Si no tienes la info, pon "N/A" o déjalo vacío, pero manten las comillas):

---
tags: [podcast, audio_analysis, {{ tags }}]
source: "{{ source_url }}"
date_processed: "{{ date }}"
type: "audio"
---

# 🎙️ Análisis de Audio: {{ title }}

## 📌 Resumen Ejecutivo
(Un resumen de 2-3 párrafos explicando de qué trata el audio, quiénes participan y cuál es el mensaje central).

## 🔑 Puntos Clave
(Lista de viñetas con los argumentos, ideas o datos más importantes discutidos en el audio).
*   **Tema 1**: Detalle.
*   **Tema 2**: Detalle.

## 🧠 Ideas Profundas y Citas
(Extrae las frases o conceptos más valiosos que valga la pena recordar para el futuro. Si puedes inferir citas textuales, mejor).

## 🚀 Accionables o Siguientes Pasos
(Si el audio menciona consejos prácticos, tareas o estrategias a seguir, enlíslalos aquí. Si no hay accionables claros, puedes omitir esta sección).
