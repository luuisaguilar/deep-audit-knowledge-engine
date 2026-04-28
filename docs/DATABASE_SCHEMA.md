# Database Schema: Deep Audit Knowledge Engine

---

## 1. SQLite Local — `rss_feeds.db` (Sprint 4)

Base de datos local para el RSS Monitor. Archivo en el directorio raíz del proyecto.
Manejada por `rss_db.py`. Se crea automáticamente en el primer arranque via `init_db()`.

### Tabla `feeds`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER PK AUTOINCREMENT | Identificador único |
| `name` | TEXT NOT NULL | Nombre legible del feed (ej: "The Pragmatic Engineer") |
| `url` | TEXT NOT NULL UNIQUE | URL del feed RSS |
| `created_at` | TEXT NOT NULL | ISO 8601 — fecha de alta |
| `active` | INTEGER NOT NULL DEFAULT 1 | Flag booleano: 1=activo, 0=pausado |

### Tabla `seen_articles`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER PK AUTOINCREMENT | Identificador único |
| `feed_id` | INTEGER NOT NULL | FK → `feeds.id` ON DELETE CASCADE |
| `article_url` | TEXT NOT NULL | URL canónica del artículo o episodio |
| `article_title` | TEXT | Título en el momento del parsing |
| `processed_at` | TEXT NOT NULL | ISO 8601 — fecha de procesamiento |
| `obsidian_filename` | TEXT | Nombre del `.md` generado en Obsidian |
| `status` | TEXT NOT NULL DEFAULT 'processed' | `processed`, `error`, `skipped` (podcasts), `podcast_processed` |

**Constraint**: `UNIQUE(feed_id, article_url)` — evita duplicados.

**Índice recomendado**: sobre `article_url` para lookups O(1) en `is_seen()`.

### DDL de inicialización

```sql
CREATE TABLE IF NOT EXISTS feeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS seen_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    article_url TEXT NOT NULL,
    article_title TEXT,
    processed_at TEXT NOT NULL,
    obsidian_filename TEXT,
    status TEXT NOT NULL DEFAULT 'processed',
    UNIQUE(feed_id, article_url)
);

CREATE INDEX IF NOT EXISTS idx_seen_url ON seen_articles(article_url);
```

---

## 2. Supabase (Planeado — Sprint futuro)

Para caché de análisis de Gemini. Evita re-gastar cuota procesando el mismo contenido dos veces.

### Tabla `audit_records`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | uuid PK | Identificador único |
| `source_url` | text UNIQUE | URL fuente (YT, GH, Web, Podcast) |
| `source_type` | text | Enum: `youtube`, `github`, `web`, `podcast` |
| `content_hash` | text | SHA256 del contenido original para detectar cambios |
| `generated_markdown` | text | Reporte completo generado por Gemini |
| `metadata` | jsonb | Metadatos extra: título, canal, estrellas, vistas, idioma |
| `created_at` | timestamp | Fecha del primer análisis |
| `updated_at` | timestamp | Fecha de la última actualización |

### Tabla `source_tracking`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | uuid PK | |
| `identifier` | text | @usuario, ID de canal, o URL de feed RSS |
| `type` | text | `channel`, `github_user`, `rss_feed` |
| `last_indexed` | timestamp | Última vez que se listaron sus elementos |

### Estrategia de Caché

```
Antes de analizar → SELECT * FROM audit_records WHERE source_url = :url
  Si existe y content_hash coincide → retornar generated_markdown (sin llamar a Gemini)
  Si no existe → analizar → UPSERT en audit_records
```

### Índices

```sql
CREATE INDEX idx_source_url ON audit_records(source_url);
```

---

## 3. SQLite Externos (Solo Lectura)

El módulo `knowledge_sync.py` lee en modo lectura las bases de datos de agentes externos.
El proyecto no escribe en estas DBs.

| DB | Ruta | Agente |
|----|------|--------|
| `auctionbot.db` | `../auctionbot/data/auctionbot.db` | AuctionBot |
| `dexscreener_data.db` | `../dexscreener_bot/dexscreener_data.db` | DexScreener |
