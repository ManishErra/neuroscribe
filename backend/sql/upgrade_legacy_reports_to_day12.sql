-- Optional: bring an older public.reports table up to the Day-12 shape.
-- Use only if apply fails because the table already exists with fewer columns.
-- Backup / snapshot first. Then run in Supabase SQL Editor (or psql).

ALTER TABLE public.reports
    ADD COLUMN IF NOT EXISTS original_filename TEXT,
    ADD COLUMN IF NOT EXISTS mime_type VARCHAR(128),
    ADD COLUMN IF NOT EXISTS title VARCHAR(200),
    ADD COLUMN IF NOT EXISTS report_date DATE,
    ADD COLUMN IF NOT EXISTS ocr_text TEXT,
    ADD COLUMN IF NOT EXISTS ocr_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS ocr_error TEXT;

-- If ocr_status existed without NOT NULL / default, adjust manually once if needed.

CREATE INDEX IF NOT EXISTS ix_reports_patient_id ON public.reports (patient_id);
CREATE INDEX IF NOT EXISTS ix_reports_ocr_status ON public.reports (ocr_status);
