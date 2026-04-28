{% include '_base_system.md' %}

Actúa como un experto en gestión del conocimiento técnico. Genera una nota para Obsidian.

REQUISITO CRÍTICO: Comienza SIEMPRE con un bloque YAML Properties exactamente así:
---
tipo: video_research
fuente: "{{ url }}"
canal: "{{ channel }}"
fecha_video: {{ date }}
estado: procesado
idioma_original: {{ language }}
---

# {{ title }}

{{ instruction }}
SECCIONES REQUERIDAS:
1. **Resumen Ejecutivo**: 3 puntos clave.
2. **Stack Tecnológico**: Si se mencionan lenguajes/herramientas.
3. **Decisiones de Arquitectura / Lógica**: Por qué y cómo funciona lo explicado.
4. **Action Items / Hallazgos**: Ideas accionables sacadas del video.

CONTENIDO:
Título: {{ title }}
{% if transcript %}
Transcripción (fragmento): {{ transcript }}
{% else %}
Descripción: {{ description }}
{% endif %}
