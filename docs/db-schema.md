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
# Database Schema

## patients
Stores patient demographic information.

| Column | Type |
|---|---|
| id | UUID |
| name | String |
| age | Integer |
| gender | String |
| created_at | Timestamp |

---

## sessions
Stores therapy/psychiatric sessions.

| Column | Type |
|---|---|
| id | UUID |
| patient_id | UUID |
| session_date | Date |
| created_at | Timestamp |

Relationship:
- One patient → many sessions

---

## transcripts
Stores raw AI-generated transcripts.

| Column | Type |
|---|---|
| id | UUID |
| session_id | UUID |
| raw_text | Text |
| created_at | Timestamp |

Relationship:
- One session → one transcript

---

## notes
Stores AI draft notes and doctor-reviewed notes.

| Column | Type |
|---|---|
| id | UUID |
| session_id | UUID |
| ai_draft | JSON/Text |
| doctor_edited | JSON/Text |
| is_finalized | Boolean |
| created_at | Timestamp |

Relationship:
- One session → one note

---

# Important Safety Architecture

NeuroScribe preserves:

- Original AI-generated note
- Doctor-reviewed final note

Separately.

This ensures:
- auditability
- traceability
- medico-legal safety
- AI transparency