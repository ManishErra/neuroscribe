# Development Guide

## Prerequisites

- Python 3.11+
- Node.js 20+
- npm
- Git
- Tesseract OCR and Poppler for non-container local OCR development

## Environment

### Backend — backend/.env

Start from backend/.env.example.

Required in normal production operation:

- DATABASE_URL
- JWT_SECRET
- GROQ_API_KEY

Optional configuration:

- APP_ENV — development or production
- JWT_ALGORITHM — currently restricted to HS256
- JWT_EXPIRE_MINUTES — default 480
- CORS_ALLOWED_ORIGINS — comma-separated additional browser origins
- GROQ_LLM_MODEL — default openai/gpt-oss-20b
- GROQ_STT_MODEL — default whisper-large-v3
- GROQ_MAX_COMPLETION_TOKENS — default 1024
- OCR_DPI — default 160
- OCR_TESSERACT_TIMEOUT — default 45

For local development, the database code supports SQLite when DATABASE_URL is omitted. Production should use the configured PostgreSQL/Supabase database.

### Frontend — client/.env

Start from client/.env.example.

- VITE_API_URL — FastAPI base URL
- VITE_AUTH_ENABLED — authentication feature flag used by the client

## Running locally

Backend:

~~~bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
~~~

Frontend:

~~~bash
cd client
npm ci
npm run dev
~~~

## Testing

Fast local structural checks:

~~~bash
cd backend
python -m compileall -q .
~~~

Clinical-memory regression suite:

~~~bash
python -m pytest test_clinical_memory.py
~~~

Frontend:

~~~bash
cd client
npm run build
npm run lint
~~~

Some scripts under backend/scripts/ are environment-dependent operational or migration checks. Read the script before running one against a real database.

## Deployment checklist

1. Configure backend secrets in the hosting platform.
2. Confirm APP_ENV=production.
3. Confirm the production database URL.
4. Confirm the frontend API URL points to the deployed API.
5. Run backend preflight checks where applicable.
6. Verify /health.
7. Test login and a non-sensitive patient workflow.
8. Verify Ask NeuroScribe with a known test patient.
9. Check application logs for errors without exposing PHI.

## Repository hygiene

Do not commit:

- .env files
- generated vector indexes
- local databases
- uploads
- logs
- real patient documents
- build output
- dependency directories
