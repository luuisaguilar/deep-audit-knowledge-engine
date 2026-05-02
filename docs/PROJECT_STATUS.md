# Deep Audit Knowledge Engine — Status Report

## Estado General
**Fase Actual:** Producción — v2.1.2  
**Sprints Completados:** 1–11  
**URL Pública:** https://knowledge.luisaguilaraguila.com  
**Infraestructura:** Proxmox LXC 126 — 5 contenedores Docker

---

## Stack en Producción

| Capa | Tecnología | Acceso |
|------|-----------|--------|
| Landing + Dashboard | Next.js 15 | `/` |
| Admin / Power User | Streamlit | `/admin/` |
| Backend API | FastAPI + Uvicorn | `/api/` `/analyze/` |
| Reverse Proxy | Nginx | Puerto 80 |
| Tunnel HTTPS | Cloudflare (dashboard-managed) | `knowledge.luisaguilaraguila.com` |
| Auth | Supabase Auth + `@supabase/ssr` | Cookies (SSR-compatible) |
| BD Operativa | Supabase PostgreSQL | Ingestas, auth, analítica |
| BD Vectorial | Supabase pgvector | RAG / búsqueda semántica |
| BD RSS | SQLite (`rss_feeds.db`) | Named volume Docker |
| LLM | Gemini 2.0 Flash | `config.py` + tenacity |

---

## Sprints Completados (1–11)

| Sprint | Módulo | Estado |
|--------|--------|--------|
| 1-3 | YouTube, GitHub, Web, Chef, RSS | ✅ |
| 3.5 | Seguridad, `.env`, config.py | ✅ |
| 4 | Persistencia Supabase, Analytics, Jinja2 prompts | ✅ |
| 5 | Hardening, dedup global | ✅ |
| 5.5 | Docker, Cloudflare Tunnel, deploy | ✅ |
| 6 | Audio/Podcast (Gemini nativo) | ✅ |
| 7 | RAG + pgvector + Buscador semántico | ✅ |
| 8 | Token tracking + cost analytics | ✅ |
| 9 | FastAPI, n8n webhook, background tasks | ✅ |
| 10 | Multi-user Auth (Supabase), DocGrab (Playwright) | ✅ |
| 11 | Next.js landing, Nginx reverse proxy, 5-container deploy | ✅ |

---

## Arquitectura de Contenedores

```
knowledge.luisaguilaraguila.com
        │
        ▼
[Cloudflare Tunnel]
        │
        ▼
[knowledge-nginx :80]
   ├── /           → [knowledge-landing :3000]  (Next.js)
   ├── /admin/     → [knowledge-engine-app :8501] (Streamlit)
   ├── /api/       → [knowledge-engine-api :8000] (FastAPI)
   └── /analyze/   → [knowledge-engine-api :8000] (FastAPI)
```

---

## Próximos Sprints (Backlog)

### Sprint 12 (Siguiente)
- [ ] Daily Briefings — reporte matutino vía n8n/Telegram con ingestas del día anterior
- [ ] Deep Sync — Syncthing en Docker para sincronizar vault
- [ ] User Profile — avatar, preferencias de LLM
- [ ] Auto-deploy CI/CD — GitHub Actions → SSH → git pull + rebuild en LXC 126

### Sprint 13
- [ ] Cross-Source semantic search (búsqueda across YouTube + GitHub + Web)
- [ ] Ollama integration — LLM local para documentos confidenciales
- [ ] Auto-Wiki MOC — generación automática de Maps of Content en Obsidian

### Pendientes menores
- [ ] Forgot password — página `/auth/reset` (endpoint implementado, página falta)
- [ ] Auth en móvil — validar submit en Safari iOS
- [ ] Loki — integrar logs de Docker en Grafana (LXC 115)
