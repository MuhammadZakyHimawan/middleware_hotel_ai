-- Migration: tabel cache log_pertanyaan untuk middleware Text-to-SQL
-- Skema: public

CREATE TABLE IF NOT EXISTS public.log_pertanyaan (
    id              BIGSERIAL PRIMARY KEY,
    question        TEXT NOT NULL UNIQUE,
    intent_detected VARCHAR(50),
    sql_query       TEXT,
    sql_result      JSONB,
    created_at      TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_log_pertanyaan_question
    ON public.log_pertanyaan (question);

CREATE INDEX IF NOT EXISTS idx_log_pertanyaan_created_at
    ON public.log_pertanyaan (created_at DESC);