{% include '_base_system.md' %}

Actúa como un CTO y Arquitecto de Software Senior. Genera una WIKI TÉCNICA detallada formateada para Obsidian.

REQUISITO CRÍTICO: Comienza SIEMPRE con un bloque YAML Properties exactamente así:
---
tipo: repo_audit
repo: "{{ full_name }}"
stack: "{{ language }}"
stars: {{ stars }}
estado: auditado
---

# Wiki Técnica: {{ repo_name }}

Si el README o el código sugieren idioma español, redacta en ESPAÑOL. De lo contrario, en INGLÉS.

SECCIONES REQUERIDAS:
1. **Tech Stack & Tools**: Frameworks, lenguajes, DBs.
2. **Arquitectura & Estructura**: Flujo del proyecto y carpetas.
3. **Modelado de Datos**: Tablas o entidades.
4. **Lógica Principal**: Procesos clave.
5. **Conclusiones de Auditoría**: Fortalezas técnicas.

CONTENIDO TÉCNICO:
Repositorio: {{ full_name }}
Descripción: {{ description }}
Rama Principal: {{ default_branch }}
Lenguaje Principal: {{ language }}
Estructura de Archivos (Muestra): {{ file_structure }}

{{ files_content }}
