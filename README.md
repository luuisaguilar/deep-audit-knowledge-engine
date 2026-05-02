# 🧠 Deep Audit Knowledge Engine

Ecosistema de Inteligencia Semántica y Auditoría Autónoma diseñado para transformar contenido multimedia (YouTube, GitHub, Web, Audio) en bases de conocimiento estructuradas para Obsidian.

## 🚀 Versión 2.0: Multi-User Platform (Emerald Edition)

Esta versión marca la transición de una herramienta personal a una plataforma SaaS multi-usuario con aislamiento completo de datos y diseño premium.

### 🛡️ Nueva Capa de Seguridad (Auth) y Modo Dev
*   **Supabase Auth:** Gestión de identidades mediante JWT y sesiones seguras.
*   **Modo Dev (Auth Bypass):** Si no se proveen llaves de Supabase, el sistema permite acceso local inmediato (User: `dev-user-local`).
*   **Multi-tenancy:** Los registros de ingesta, analíticas y archivos están aislados por `user_id`.
*   **Rate Limiting:** Protección activa contra ataques de fuerza bruta en Login, Registro y Recuperación.

### 🎨 Diseño Visual "Midnight Emerald"
*   **Paleta de Colores:** Fondo `#0e1117` con acentos en **Verde Esmeralda** (`#10b981`).
*   **Glassmorphism:** Tarjetas de métricas y contenedores con efectos de desenfoque y profundidad.
*   **No Streamlit Header:** Interfaz inmersiva sin menús nativos visibles.

## 🛠️ Arquitectura de Usuario (Aislamiento)
Las notas ahora se organizan dinámicamente para facilitar la sincronización personal:
```text
/vault
  /users
    /{user_id_1}
      /10_YouTube
      /20_GitHub
      /30_Web
    /{user_id_2}
      ...
```

## 📥 Funcionalidades Clave
1.  **🕷️ DocGrab Engine:** Rastreo recursivo inteligente de sitios de documentación (Sitemaps y Playwright Rendering). Permite *Descubrimiento Estructural* y clonación selectiva a Markdown.
2.  **Tablero de Analíticas:** Estadísticas de tokens, costos y procesamientos exitosos por usuario.
3.  **Buscador Inteligente:** Filtra ingestas pasadas vinculadas a tu cuenta.
4.  **Exportación ZIP:** Descarga tu base de conocimientos personal en un clic desde la pestaña "Obsidian Sync".
5.  **API Multi-user:** Backend FastAPI preparado para recibir peticiones de n8n/Telegram identificando al usuario.

## 📦 Instalación y Despliegue
Para aplicar los últimos cambios de seguridad y rutas:
```powershell
docker-compose up -d --build
```

## 🔐 Variables de Entorno (.env)
Asegúrate de tener configuradas las siguientes llaves:
*   `SUPABASE_URL` / `SUPABASE_KEY`: Para la base de datos y Auth.
*   `GEMINI_API_KEY`: Motor de inteligencia.
*   `VAULT_PATH`: Directorio raíz de almacenamiento (Obsidian).

---
*Desarrollado por el equipo de Advanced Agentic Coding - Google DeepMind*
