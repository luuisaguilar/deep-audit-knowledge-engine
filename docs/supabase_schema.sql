-- SQL para crear la tabla de ingestas en Supabase (PostgreSQL)

CREATE TABLE IF NOT EXISTS ingestions (
    id              BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    source_type     TEXT NOT NULL,
    source_url      TEXT UNIQUE NOT NULL,
    title           TEXT,
    processed_at    TIMESTAMPTZ DEFAULT NOW(),
    model_used      TEXT DEFAULT 'gemini-2.0-flash',
    tokens_estimated INTEGER,
    vault_path      TEXT,
    status          TEXT DEFAULT 'success',
    error_message   TEXT,
    metadata_json   JSONB
);

-- Habilitar RLS (opcional, pero recomendado)
ALTER TABLE ingestions ENABLE ROW LEVEL SECURITY;

-- Crear política para permitir todo (ya que es para uso personal/anon key con acceso controlado)
-- Si vas a usar la anon key sin auth en un entorno seguro (LXC privado):
CREATE POLICY "Allow all for anon" ON ingestions
    FOR ALL
    USING (true)
    WITH CHECK (true);
