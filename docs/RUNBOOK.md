# RUNBOOK: Operaciones y Despliegue

Este documento sirve como manual operativo para el despliegue, mantenimiento y recuperación del **Deep Audit Knowledge Engine**.

---

## 1. Procedimiento de Despliegue (Producción)

La infraestructura de producción utiliza **Docker Compose** en un contenedor LXC dentro de Proxmox. Todo el tráfico se enruta a través de un **Cloudflare Tunnel** para acceso HTTPS seguro sin exponer puertos locales.

### 1.1 Preparación Inicial
1. Clona el repositorio en el servidor destino.
2. Crea una copia de `.env.example` como `.env`.
3. Completa todas las credenciales:
   *   `GEMINI_API_KEY`: Clave de Google AI Studio.
   *   `GITHUB_TOKEN`: Personal Access Token (PAT) clásico o fine-grained.
   *   `SUPABASE_URL` y `SUPABASE_KEY`: Credenciales del proyecto en Supabase (para `knowledge.db`).
   *   `CLOUDFLARE_TUNNEL_TOKEN`: Token obtenido al crear el túnel en el Zero Trust Dashboard.
   *   `VAULT_PATH`: Ruta absoluta en el host (ej. `/mnt/obsidian-vault/20_CONOCIMIENTO`) que se montará en Docker.

### 1.2 Arranque de Servicios
```bash
# Construir la imagen de Streamlit y levantar todo en segundo plano
docker-compose up -d --build

# Verificar que los contenedores estén 'Up'
docker-compose ps
```

---

## 2. Operaciones Mantenimiento

### 2.1 Ver Registros (Logs)
Para diagnosticar fallos en la ingesta o errores de red:
```bash
# Ver logs de la app de Streamlit
docker-compose logs -f app

# Ver logs del túnel de Cloudflare
docker-compose logs -f cloudflared
```

### 2.2 Actualización de Código (Nuevos Sprints)
Cuando se hace un git pull con nuevas funcionalidades o dependencias:
```bash
git pull origin master
docker-compose build app  # Reconstruir si cambiaron requirements.txt o el Dockerfile
docker-compose up -d app  # Reiniciar el servicio con la nueva imagen
```

---

## 3. Resolución de Problemas Comunes (Troubleshooting)

### Problema: Error 429 de Gemini (Resource Exhausted)
**Síntoma:** El sistema procesa URLs pero arroja "⚠️ ERROR: Cuota de Gemini agotada".
**Causa:** Se ha excedido el límite gratuito de Gemini (15 RPM o 1500 RPD).
**Solución:** El módulo `tenacity` en `config.py` intentará automáticamente con retardo exponencial. Si falla repetidamente, el sistema registrará el status como `failed` en Supabase. Esperar unas horas y usar el checkbox "🔄 Forzar Re-proceso" en la UI.

### Problema: "No se encontró el ejecutable de ffmpeg"
**Síntoma:** Los videos de YouTube fallan al intentar procesarse.
**Causa:** `yt-dlp` requiere `ffmpeg` instalado.
**Solución:** Si se ejecuta fuera de Docker, instalar vía `apt install ffmpeg`. En Docker, la imagen `python:3.11-slim` configurada en el `Dockerfile` ya lo instala automáticamente.

### Problema: El Dashboard no es accesible desde internet
**Síntoma:** `https://knowledge.tudominio.com` da error 502 o Timeout.
**Causa:** El contenedor `cloudflared` está caído o el token es inválido.
**Solución:**
1. Revisa `docker-compose logs cloudflared`.
2. Verifica que el contenedor `app` esté en estado 'Up' y respondiendo en el puerto 8501.
3. Asegúrate de que el dashboard de Cloudflare Zero Trust muestre el túnel como "Healthy".

### Problema: Deduplicación excesiva (No procesa URL nueva)
**Síntoma:** Streamlit muestra instantáneamente "⏭️ Ya procesado" pero necesitas re-evaluar la nota.
**Causa:** La URL ya tiene un registro de éxito en Supabase.
**Solución:** En el panel lateral de Streamlit, activa la casilla **"🔄 Forzar Re-proceso (Ignorar Dedup)"**.

---

## 4. Backups y Restauración

*   **Obsidian Vault:** El Vault está mapeado a una carpeta física en el host. El backup del Vault debe gestionarse externamente (ej: rsync, Syncthing, Proxmox Backup Server).
*   **Ingestas y Analíticas:** Estos datos están seguros en la nube (Supabase). No se requiere backup local.
*   **RSS Feeds (`rss_feeds.db`):** Esta base de datos SQLite se mapea como volumen. Si se pierde, solo se pierden las configuraciones de los feeds suscritos, no los datos analizados. Se recomienda respaldar este archivo `.db` mensualmente.
