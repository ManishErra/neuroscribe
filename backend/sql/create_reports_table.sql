-- Day 12: patient-scoped clinical reports + OCR text store.
-- Apply manually against the same database as DATABASE_URL (pgvector DB).
--
-- gen_random_uuid() lives in pgcrypto; Supabase enables it by default. If you
-- see "function gen_random_uuid() does not exist", run this once (requires rights):
--   CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients (id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    original_filename TEXT,
    mime_type VARCHAR(128),
    title VARCHAR(200),
    report_date DATE,
    ocr_text TEXT,
    ocr_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    ocr_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_reports_patient_id ON reports (patient_id);
CREATE INDEX IF NOT EXISTS ix_reports_ocr_status ON reports (ocr_status);
