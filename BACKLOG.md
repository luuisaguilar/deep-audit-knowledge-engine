# 📋 BACKLOG: Deep Audit Knowledge Engine

## 🟢 SPRINT 9 & 10: Multi-User Architecture & UI Polish (COMPLETO)
- [x] Integrar Supabase Auth en Streamlit.
- [x] Refactorizar `db.py` para filtrado por `user_id`.
- [x] Implementar Aislamiento de Archivos en `/vault/users/{user_id}/`.
- [x] Rediseño Visual "Emerald Midnight" (Modo Oscuro Premium).
- [x] Sistema de Registro, Login y Recuperación de Contraseña.
- [x] Rate Limiting en la capa de Auth.
- [x] Función de Exportación ZIP de conocimiento por usuario.
- [x] API Multi-user support para n8n/Telegram.

## 🟡 SPRINT 11: DocGrab Intelligence & Deep Crawling (COMPLETO)
- [x] Integrar motor `docgrab` mediante procesos en segundo plano.
- [x] Añadir soporte para Playwright y Chromium en entorno Docker.
- [x] Lógica de **Descubrimiento Estructural** (Sitemap + Sidebar scraping).
- [x] Selector iterativo en UI para Extracción Selectiva.
- [x] Aislamiento de almacenamiento multi-usuario (`/40_Docs/`).
- [x] Fallback automático de `lxml` a `html.parser` para resiliencia.

## 🔵 SPRINT 12: Intelligence Briefings & Sync (EN PROGRESO)
- [ ] **Daily Briefings:** Reporte matutino vía n8n con lo más relevante procesado el día anterior.
- [ ] **Deep Sync:** Implementar Syncthing en el contenedor para sincronización automática bidireccional.
- [ ] **User Profile:** Editar nombre de usuario, avatar y preferencias de modelos LLM.

## 🔴 SPRINT 13: Knowledge Synthesis & Ollama
- [ ] **Cross-Source Search:** Búsqueda semántica que combine YouTube + GitHub + Web.
- [ ] **Ollama Integration:** Soporte para modelos locales (Llama 3, Mistral) para reducir costos de API.
- [ ] **Auto-Wiki Synthesis:** Generar un índice maestro (MOC) automático en Obsidian cada semana.

---
*Estado Actual: Versión 2.1.0 (DocGrab Intelligence & Multi-user Ready)*
