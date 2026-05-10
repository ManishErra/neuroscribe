## NeuroScribe — Database Schema

### patients

id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
name        VARCHAR(100)
age         INTEGER
gender      VARCHAR(20)
created_at  TIMESTAMP DEFAULT NOW()

### sessions

id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
patient_id    UUID REFERENCES patients(id)
session_date  DATE
audio_path    TEXT
created_at    TIMESTAMP DEFAULT NOW()

### transcripts

id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
session_id  UUID REFERENCES sessions(id)
raw_text    TEXT
created_at  TIMESTAMP DEFAULT NOW()

### notes

id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
session_id      UUID REFERENCES sessions(id)
ai_draft        TEXT      -- never shown as final
doctor_edited   TEXT      -- only saved after review
is_finalized    BOOLEAN DEFAULT FALSE
created_at      TIMESTAMP DEFAULT NOW()

### reports

id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
patient_id  UUID REFERENCES patients(id)
file_path   TEXT
ocr_text    TEXT
created_at  TIMESTAMP DEFAULT NOW()

### embeddings

id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
source_id   UUID
source_type VARCHAR(20)   -- 'session' or 'report'
chunk_text  TEXT
embedding   VECTOR(384)   -- pgvector column
created_at  TIMESTAMP DEFAULT NOW()