-- 1. Habilitar la extensión pgvector
create extension if not exists vector
with
  schema extensions;

-- 2. Crear la tabla para almacenar los fragmentos de documentos y sus vectores
create table if not exists document_chunks (
  id bigint primary key generated always as identity,
  source_path text not null,          -- Ruta del archivo en el Vault (o URL)
  source_title text not null,         -- Título del documento
  content text not null,              -- El fragmento de texto (chunk)
  embedding vector(768) not null,     -- Vector generado por Gemini (text-embedding-004 usa 768 dimensiones)
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Crear un índice HNSW para hacer búsquedas de similitud súper rápidas
create index on document_chunks
using hnsw (embedding vector_cosine_ops);

-- 4. Crear una función (RPC) en Postgres para hacer la búsqueda de similitud.
-- Supabase llama a esto cuando usamos el cliente supabase.rpc('match_document_chunks', ...)
create or replace function match_document_chunks (
  query_embedding vector(768),
  match_threshold float,
  match_count int
)
returns table (
  id bigint,
  source_path text,
  source_title text,
  content text,
  similarity float
)
language sql stable
as $$
  select
    document_chunks.id,
    document_chunks.source_path,
    document_chunks.source_title,
    document_chunks.content,
    1 - (document_chunks.embedding <=> query_embedding) as similarity
  from document_chunks
  where 1 - (document_chunks.embedding <=> query_embedding) > match_threshold
  order by similarity descending
  limit match_count;
$$;
