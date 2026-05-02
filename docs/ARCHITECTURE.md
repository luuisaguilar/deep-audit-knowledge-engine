# System Architecture: Deep Audit Knowledge Engine v2.1.2

## 1. Visión General

El **Deep Audit Knowledge Engine** es un centro de operaciones de IA diseñado para la ingesta, análisis y archivo de conocimiento técnico de alta densidad. Transforma fuentes no estructuradas (video, código, blogs, podcasts, RSS) en activos de conocimiento atómicos para Obsidian.

**URL Pública:** https://knowledge.luisaguilaraguila.com  
**Infraestructura:** Proxmox LXC 126 (`app-knowledge`, IP `192.168.1.126`)

---

## 2. Diagrama del Sistema

```
Internet
    │
    ▼
Cloudflare Tunnel (dashboard-managed)
    │
    ▼
knowledge-nginx [:80]
    ├── /           → knowledge-landing [:3000]     Next.js 15
    ├── /admin/     → knowledge-engine-app [:8501]  Streamlit
    ├── /api/       → knowledge-engine-api [:8000]  FastAPI
    └── /analyze/   → knowledge-engine-api [:8000]  FastAPI
    
knowledge-engine-tunnel              Cloudflare sidecar

Supabase (nube)
    ├── PostgreSQL   ingestas, auth, analítica
    └── pgvector     embeddings RAG

Obsidian Vault
    └── /mnt/obsidian-vault  Docker volume bind
```

---

## 3. Contenedores Docker (5)

| Contenedor | Imagen | Puerto | Función |
|-----------|--------|--------|---------|
| `knowledge-landing` | node:20-alpine (build) | 3000 | Next.js landing + dashboard usuario |
| `knowledge-engine-app` | python:3.11-slim | 8501 | Streamlit UI admin/power user |
| `knowledge-engine-api` | python:3.11-slim | 8000 | FastAPI — webhooks n8n/Telegram |
| `knowledge-nginx` | nginx:alpine | **80** | Reverse proxy unificado |
| `knowledge-engine-tunnel` | cloudflare/cloudflared | — | Tunnel HTTPS sidecar |

Orquestados con **docker-compose v2** en `/usr/local/bin/docker-compose`.

---

## 4. Estructura de Repos

### `deep-audit-knowledge-engine` (engine)
```
├── app.py                    # Streamlit UI — 10 tabs
├── api.py                    # FastAPI — /api/v1/process-url, /analyze/*
├── config.py                 # Gemini singleton + generate_with_retry()
├── core/
│   ├── db.py                 # Supabase client — ingestas, auth, analytics
│   ├── search_engine.py      # RAG con pgvector
│   └── prompt_loader.py      # Jinja2 template renderer
├── prompts/                  # Templates editables sin tocar código
├── *_analyzer.py             # Motores de ingesta (YouTube, GitHub, Web...)
├── rss_db.py                 # SQLite CRUD feeds RSS
├── Dockerfile                # python:3.11-slim + ffmpeg + Chromium
├── docker-compose.yml        # 5 servicios
├── nginx.conf                # Routing rules
└── docs/                     # Este directorio
```

### `deep-audit-landing` (frontend)
```
├── src/app/
│   ├── page.tsx              # Landing page pública
│   ├── auth/page.tsx         # Login / Registro con Supabase Auth
│   └── dashboard/            # Dashboard usuario autenticado
│       ├── page.tsx          # Overview con stats
│       ├── youtube/page.tsx  # Análisis YouTube
│       └── docgrab/page.tsx  # DocGrab
├── src/components/dashboard/ # Componentes UI del dashboard
├── src/lib/supabase.ts       # createBrowserClient (@supabase/ssr)
├── src/middleware.ts         # Auth guard SSR — lee sesión desde cookies
└── Dockerfile                # node:20-alpine multi-stage standalone
```

---

## 5. Nginx Routing

```nginx
location /analyze/ { proxy_pass http://fastapi; }
location /api/     { proxy_pass http://fastapi; }
location /health   { proxy_pass http://fastapi; }
location /admin/   { proxy_pass http://streamlit/; + WebSocket }
location /         { proxy_pass http://nextjs;   + WebSocket }
```

---

## 6. Supabase Auth — Flujo SSR

El middleware de Next.js (`src/middleware.ts`) protege `/dashboard/*` y lee la sesión desde **cookies** usando `@supabase/ssr`. El cliente browser (`src/lib/supabase.ts`) usa `createBrowserClient` que también escribe en cookies — esto mantiene la sesión sincronizada entre cliente y servidor.

```
Login (browser) → supabase.auth.signIn → cookie set
Redirect → /dashboard
Middleware SSR → lee cookie → usuario válido → deja pasar
```

---

## 7. Variables de Entorno

| Variable | Dónde se usa | Cómo se pasa |
|----------|-------------|--------------|
| `GEMINI_API_KEY` | Engine (Python) | `.env` → `env_file` |
| `GITHUB_TOKEN` | Engine (Python) | `.env` → `env_file` |
| `SUPABASE_URL` | Engine + Landing | `.env` → engine runtime; Landing **build arg** |
| `SUPABASE_KEY` | Engine + Landing | `.env` → engine runtime; Landing **build arg** |
| `CLOUDFLARE_TUNNEL_TOKEN` | Tunnel | `.env` → `TUNNEL_TOKEN` env var |
| `VAULT_PATH` | Engine | `.env` → volume mount |

> ⚠️ `NEXT_PUBLIC_*` se bakean en el build de Next.js. Cambios en Supabase requieren `build --no-cache landing`.

---

## 8. Patrones de Diseño

- **Singleton:** Gemini se inicializa una vez en `config.py`
- **Retry con backoff exponencial:** `tenacity` en `generate_with_retry()`
- **Template Method:** Prompts en `prompts/*.md` con Jinja2 — iterar calidad sin tocar Python
- **Deduplicación global:** `core/db.has_been_processed(url)` antes de cada ingesta
- **Separación UI/lógica:** `*_analyzer.py` no importan `streamlit`
- **SSR Auth:** Sesión en cookies para que el middleware Next.js la lea server-side
