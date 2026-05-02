-- =============================================================
-- Deep Audit Knowledge Engine — Supabase Migration v1
-- Ejecutar completo en: Supabase Dashboard → SQL Editor → Run
-- =============================================================

-- ─── 1. TABLA DE INGESTAS ────────────────────────────────────

CREATE TABLE IF NOT EXISTS ingestions (
    id                  BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id             TEXT,                                    -- Supabase Auth UID
    source_type         TEXT        NOT NULL,                    -- youtube, github, web, rss, chef, audio, docgrab
    source_url          TEXT        NOT NULL,
    title               TEXT,
    processed_at        TIMESTAMPTZ DEFAULT NOW(),
    model_used          TEXT        DEFAULT 'gemini-2.0-flash',
    tokens_estimated    INTEGER,
    prompt_tokens       INTEGER     DEFAULT 0,
    completion_tokens   INTEGER     DEFAULT 0,
    vault_path          TEXT,
    status              TEXT        DEFAULT 'success',           -- success | failed
    error_message       TEXT,
    metadata_json       JSONB
);

-- Deduplicación por usuario: misma URL puede ser procesada por distintos usuarios
CREATE UNIQUE INDEX IF NOT EXISTS idx_ingestions_url_user
    ON ingestions (source_url, user_id);

-- Índice para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_ingestions_user_id   ON ingestions (user_id);
CREATE INDEX IF NOT EXISTS idx_ingestions_status    ON ingestions (status);
CREATE INDEX IF NOT EXISTS idx_ingestions_processed ON ingestions (processed_at DESC);

-- RLS
ALTER TABLE ingestions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own ingestions" ON ingestions
    FOR ALL
    USING (user_id = auth.uid()::text OR user_id IS NULL)
    WITH CHECK (user_id = auth.uid()::text OR user_id IS NULL);


-- ─── 2. PGVECTOR + BÚSQUEDA SEMÁNTICA (RAG) ──────────────────

CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

CREATE TABLE IF NOT EXISTS document_chunks (
    id              BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    user_id         TEXT,                                        -- Supabase Auth UID
    source_path     TEXT        NOT NULL,                        -- Ruta del .md en Obsidian o URL
    source_title    TEXT        NOT NULL,
    content         TEXT        NOT NULL,                        -- Fragmento de texto (chunk)
    embedding       vector(768) NOT NULL,                        -- Gemini text-embedding-004 (768 dims)
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Índice HNSW para búsqueda de similitud coseno
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding
    ON document_chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_document_chunks_user_id
    ON document_chunks (user_id);

-- RLS
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own chunks" ON document_chunks
    FOR ALL
    USING (user_id = auth.uid()::text OR user_id IS NULL)
    WITH CHECK (user_id = auth.uid()::text OR user_id IS NULL);

-- Función RPC para búsqueda semántica
CREATE OR REPLACE FUNCTION match_document_chunks (
    query_embedding vector(768),
    match_threshold float,
    match_count     int,
    filter_user_id  text DEFAULT NULL
)
RETURNS TABLE (
    id              bigint,
    source_path     text,
    source_title    text,
    content         text,
    similarity      float
)
LANGUAGE sql STABLE
AS $$
    SELECT
        dc.id,
        dc.source_path,
        dc.source_title,
        dc.content,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    WHERE
        (1 - (dc.embedding <=> query_embedding)) > match_threshold
        AND (filter_user_id IS NULL OR dc.user_id = filter_user_id)
    ORDER BY similarity DESC
    LIMIT match_count;
$$;
