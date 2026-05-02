-- Script SQL para Sprint 8: Token Tracking & Analytics
-- Ejecuta este script en el SQL Editor de tu proyecto en Supabase.

-- Agregar columnas de tokens a la tabla de ingestions
ALTER TABLE public.ingestions
ADD COLUMN IF NOT EXISTS prompt_tokens integer DEFAULT 0,
ADD COLUMN IF NOT EXISTS completion_tokens integer DEFAULT 0;

-- Opcional: Agregar un índice si eventualmente quieres filtrar por consultas muy pesadas
CREATE INDEX IF NOT EXISTS idx_ingestions_prompt_tokens ON public.ingestions(prompt_tokens);
