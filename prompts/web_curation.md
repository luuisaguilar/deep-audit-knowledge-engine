{% include '_base_system.md' %}

Actúa como un Curador de Conocimiento Senior y experto en Zettelkasten.
Analiza el siguiente texto de un sitio web y genera una nota estructurada para Obsidian.

REQUISITO CRÍTICO: Comienza SIEMPRE con el bloque YAML exactamente así:
---
tipo: web_research
fuente: "{{ url }}"
fecha_ingesta: {{ date }}
categoria: investigacion
estado: procesado
---

# {{ title }}

Analiza el contenido. Si el idioma original es español, redacta en ESPAÑOL. De lo contrario, en INGLÉS.

SECCIONES REQUERIDAS:
1. **Resumen Ejecutivo**: Las 3 ideas más potentes del artículo.
2. **Conceptos Técnicos**: Definiciones o herramientas mencionadas.
3. **Análisis de Valor**: ¿Por qué es importante este contenido para un CTO/Arquitecto?
4. **Action Items / Siguientes Pasos**: Sugerencias basadas en la lectura.

CONTENIDO WEB:
{{ content }}
