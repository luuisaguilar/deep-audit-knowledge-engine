# Database Schema: Deep Audit Knowledge Engine

---

## 1. SQLite Central — `knowledge.db`

Base de datos central de historial de ingestas. Habilita deduplicación global y analytics.
Archivo en el directorio raíz del proyecto. Manejada por `core/db.py`. Se crea automáticamente al importar el módulo via `init_db()`.

### Tabla `ingestions`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER PK AUTOINCREMENT | Identificador único |
| `source_type` | TEXT NOT NULL | Tipo de fuente: `youtube`, `github`, `web`, `rss`, `chef` |
| `source_url` | TEXT UNIQUE NOT NULL | URL fuente — clave de deduplicación |
| `title` | TEXT | Título del contenido procesado |
| `processed_at` | DATETIME DEFAULT CURRENT_TIMESTAMP | Fecha/hora del procesamiento |
| `model_used` | TEXT DEFAULT 'gemini-2.0-flash' | Modelo de IA utilizado |
| `tokens_estimated` | INTEGER | Tokens estimados consumidos (futuro) |
| `vault_path` | TEXT | Ruta del archivo `.md` guardado en Obsidian |
| `status` | TEXT DEFAULT 'success' | `success` o `failed` |
| `error_message` | TEXT | Mensaje de error si `status = 'failed'` |
| `metadata_json` | TEXT | JSON con metadatos adicionales (canal, estrellas, etc.) |

### DDL de inicialización

```sql
CREATE TABLE IF NOT EXISTS ingestions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type     TEXT    NOT NULL,
    source_url      TEXT    UNIQUE NOT NULL,
    title           TEXT,
    processed_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    model_used      TEXT    DEFAULT 'gemini-2.0-flash',
    tokens_estimated INTEGER,
    vault_path      TEXT,
    status          TEXT    DEFAULT 'success',
    error_message   TEXT,
    metadata_json   TEXT
);
```

### Funciones disponibles (`core/db.py`)

| Función | Descripción |
|---------|-------------|
| `init_db()` | Crea la tabla si no existe (idempotente) |
| `record_ingestion(source_type, source_url, title, ...)` | Inserta un registro. Retorna `row_id` o `None` si ya existe |
| `has_been_processed(source_url)` | Retorna `True` si la URL ya fue procesada con status `success` |
| `get_ingestion_by_url(source_url)` | Retorna el registro completo o `None` |
| `list_recent_ingestions(limit=50)` | Últimas N ingestas, más reciente primero |
| `get_ingestion_stats()` | Agregaciones para el dashboard (total, success, failed, by_type, by_date, recent) |

---

## 2. SQLite Local — `rss_feeds.db`

Base de datos local para el RSS Monitor. Archivo en el directorio raíz del proyecto.
Manejada por `rss_db.py`. Se crea automáticamente en el primer arranque via `init_db()`.

### Tabla `feeds`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER PK AUTOINCREMENT | Identificador único |
| `url` | TEXT UNIQUE NOT NULL | URL del feed RSS |
| `nombre` | TEXT NOT NULL | Nombre legible del feed |
| `categoria` | TEXT DEFAULT 'General' | Categoría temática |

### Tabla `articles`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER PK AUTOINCREMENT | Identificador único |
| `feed_id` | INTEGER | FK → `feeds.id` |
| `link` | TEXT UNIQUE NOT NULL | URL del artículo |
| `title` | TEXT | Título del artículo |
| `published` | TEXT | Fecha de publicación |
| `status` | TEXT DEFAULT 'new' | `new`, `processed` |

---

## 3. SQLite Externos (Solo Lectura)

El módulo `knowledge_sync.py` lee en modo lectura las bases de datos de agentes externos.
El proyecto no escribe en estas DBs.

| DB | Ruta | Agente |
|----|------|--------|
| `auctionbot.db` | `../auctionbot/data/auctionbot.db` | AuctionBot |
| `dexscreener_data.db` | `../dexscreener_bot/dexscreener_data.db` | DexScreener |

---

## 4. Supabase (Planeado — Sprint futuro)

Considerado para migración cuando se necesite:
- Acceso multi-dispositivo
- pgvector para búsqueda semántica
- Dashboard de analytics en tiempo real

Por ahora, SQLite local es suficiente para uso personal (ver ADR-007 y ADR-010).
