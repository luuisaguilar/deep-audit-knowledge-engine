# RUNBOOK: Operaciones y Despliegue

## 1. Infraestructura de Producción

**LXC:** Proxmox LXC 126 — `app-knowledge` — IP `192.168.1.126`  
**URL pública:** https://knowledge.luisaguilaraguila.com  
**Repos:** `deep-audit-knowledge-engine` (engine) + `deep-audit-landing` (landing)

### Contenedores Docker (5)

| Contenedor | Puerto | Descripción |
|-----------|--------|-------------|
| `knowledge-landing` | 3000 | Next.js landing + dashboard |
| `knowledge-engine-app` | 8501 | Streamlit admin en `/admin/` |
| `knowledge-engine-api` | 8000 | FastAPI en `/api/` y `/analyze/` |
| `knowledge-nginx` | **80** (expuesto) | Reverse proxy |
| `knowledge-engine-tunnel` | — | Cloudflare Tunnel sidecar |

---

## 2. Comandos de Operación

> Todos los comandos se corren desde el **host Proxmox**. El binario es `/usr/local/bin/docker-compose` (v2 — NO usar `docker-compose` de apt).

```bash
# Ver estado
pct exec 126 -- /usr/local/bin/docker-compose \
  -f /opt/deep-audit-knowledge-engine/docker-compose.yml ps

# Logs en vivo (cambiar nombre de servicio según necesidad)
pct exec 126 -- /usr/local/bin/docker-compose \
  -f /opt/deep-audit-knowledge-engine/docker-compose.yml logs -f cloudflared

# Reiniciar un servicio
pct exec 126 -- /usr/local/bin/docker-compose \
  -f /opt/deep-audit-knowledge-engine/docker-compose.yml restart app

# Levantar todo
pct exec 126 -- /usr/local/bin/docker-compose \
  -f /opt/deep-audit-knowledge-engine/docker-compose.yml up -d
```

---

## 3. Actualización de Código

### Engine (Streamlit + FastAPI)
```bash
pct exec 126 -- bash -c "cd /opt/deep-audit-knowledge-engine && git pull origin main"
pct exec 126 -- /usr/local/bin/docker-compose \
  -f /opt/deep-audit-knowledge-engine/docker-compose.yml up -d --build app api
```

### Landing (Next.js) — IMPORTANTE: requiere rebuild forzado
Las variables `NEXT_PUBLIC_*` de Supabase se bakean en tiempo de build. Siempre usar `--no-cache`:
```bash
pct exec 126 -- bash -c "cd /opt/deep-audit-landing && git pull origin main"
pct exec 126 -- /usr/local/bin/docker-compose \
  -f /opt/deep-audit-knowledge-engine/docker-compose.yml build --no-cache landing
pct exec 126 -- /usr/local/bin/docker-compose \
  -f /opt/deep-audit-knowledge-engine/docker-compose.yml up -d landing
```

---

## 4. Deploy Inicial (desde cero)

```bash
# 1. Crear LXC en Proxmox
pct create 126 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname app-knowledge --cores 2 --memory 4096 --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.126/24,gw=192.168.1.254 \
  --nameserver 1.1.1.1 --unprivileged 1 --features keyctl=1,nesting=1
pct start 126

# 2. Instalar Docker y docker-compose v2
pct exec 126 -- bash -c "apt update && apt install -y docker.io git curl && \
  systemctl enable docker --now && \
  curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose"

# 3. Clonar repos
pct exec 126 -- bash -c "cd /opt && \
  git clone https://github.com/luuisaguilar/deep-audit-knowledge-engine.git && \
  git clone https://github.com/luuisaguilar/deep-audit-landing.git"

# 4. Configurar .env
pct exec 126 -- nano /opt/deep-audit-knowledge-engine/.env

# 5. Levantar
pct exec 126 -- /usr/local/bin/docker-compose \
  -f /opt/deep-audit-knowledge-engine/docker-compose.yml up -d --build
```

---

## 5. Cloudflare Tunnel

**Tunnel:** `knowledge-engine` (dashboard-managed en Zero Trust)  
**Token:** en `.env` como `CLOUDFLARE_TUNNEL_TOKEN`  
**Public Hostname:** `knowledge.luisaguilaraguila.com` → `http://192.168.1.126:80`

Si el token se pierde o hay que recrear:
```powershell
# En Windows (cloudflared.exe en %USERPROFILE%)
& "$env:USERPROFILE\cloudflared.exe" tunnel login
& "$env:USERPROFILE\cloudflared.exe" tunnel create knowledge-engine
& "$env:USERPROFILE\cloudflared.exe" tunnel token knowledge-engine
# Pegar token en .env del LXC
```

---

## 6. Resolución de Problemas

### docker-compose no encontrado
```bash
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64" \
  -o /usr/local/bin/docker-compose && chmod +x /usr/local/bin/docker-compose
```

### Tunnel "Provided Tunnel token is not valid"
El contenedor arrancó con el token viejo. Usar `up -d` (no `restart`) para recrearlo:
```bash
pct exec 126 -- /usr/local/bin/docker-compose \
  -f /opt/deep-audit-knowledge-engine/docker-compose.yml up -d cloudflared
```

### Dashboard Next.js redirige en loop a /auth
El middleware SSR no detecta la sesión. Verificar que `src/lib/supabase.ts` use `createBrowserClient` de `@supabase/ssr` (no `createClient` de `@supabase/supabase-js`). Luego rebuild de landing.

### Next.js muestra placeholder de Supabase
Las variables `NEXT_PUBLIC_*` no se bakearon. Hacer rebuild `--no-cache` del contenedor `landing`.

### Error 429 de Gemini
`tenacity` reintenta automáticamente. Si persiste, usar checkbox **"🔄 Forzar Re-proceso"** en Streamlit.

### DocGrab no extrae páginas
```bash
pct exec 126 -- /usr/local/bin/docker-compose \
  -f /opt/deep-audit-knowledge-engine/docker-compose.yml build --no-cache app
```

### Disco lleno
```bash
pct exec 126 -- docker system prune -af
```

---

## 7. Backups

- **Obsidian Vault:** Volumen Docker mapeado a `/mnt/obsidian-vault`. Respaldado por Proxmox Backup Server (diario 2:00 AM, 7 días retención).
- **Ingestas / Analytics:** En Supabase (nube) — no requiere backup local.
- **RSS Feeds (`rss_feeds.db`):** Named volume Docker. Respaldar mensualmente si hay feeds configurados.
- **`.env`:** Guardar en gestor de contraseñas — nunca en git.
