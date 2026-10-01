# NeuroScribe

NeuroScribe is an AI-assisted clinical workflow application for psychiatric documentation, medical-report intelligence, patient-scoped retrieval, and clinician-facing question answering.

> Safety boundary: NeuroScribe is a workflow and information-retrieval assistant. It is not a diagnostic system, does not assess suicide risk, and does not recommend or change medication. AI responses must be grounded in the patient's available records.

## What it does

- Patient and session management
- Consultation audio upload and transcription
- SOAP/clinical note generation and editing
- Medical report upload, OCR, cleaning, and structured extraction
- Patient-scoped semantic retrieval using FAISS + sentence-transformer embeddings
- Patient clinical memory assembled from reports, transcripts, notes, and profile data
- Ask NeuroScribe with intent-aware retrieval and evidence validation
- Source citations for retrieved clinical context
- Authentication and owner/patient isolation
- Production-safe error handling and audit logging

## Architecture

~~~text
                         ┌──────────────────────┐
                         │   React + Vite client │
                         │      client/          │
                         └──────────┬───────────┘
                                    │ HTTP / JWT
                                    ▼
                         ┌──────────────────────┐
                         │   FastAPI backend    │
                         │      backend/         │
                         └───────┬───────┬──────┘
                                 │       │
                  ┌──────────────┘       └───────────────┐
                  ▼                                      ▼
          ┌────────────────┐                    ┌────────────────┐
          │ SQL database   │                    │ FAISS + MiniLM │
          │ patients,      │                    │ clinical memory│
          │ sessions,      │                    │ retrieval      │
          │ reports, notes │                    └───────┬────────┘
          └────────────────┘                            │
                                                        ▼
                                                ┌───────────────┐
                                                │ Groq LLM/STT  │
                                                │ only when     │
                                                │ appropriate   │
                                                └───────────────┘
~~~

See docs/architecture.md for the detailed system design.

## Repository layout

~~~text
neuroscribe/
├── backend/              # FastAPI application and clinical AI services
│   ├── routers/           # HTTP API routes
│   ├── scripts/           # Operational/audit/migration utilities
│   ├── sql/               # Database SQL utilities
│   └── test_*.py          # Backend regression suites
├── client/               # Active React + Vite + TypeScript frontend
├── docs/                 # Product, architecture, security and development docs
│   └── archive/           # Historical implementation/audit records
├── demo_data/             # Non-production demonstration fixtures
├── start_demo.ps1         # Windows local development helper
├── start_demo.sh          # Linux/macOS local development helper
└── .github/workflows/     # Repository CI
~~~

The previous Next.js frontend and old UI design workspace have been removed from the active source tree because the Vite client application is the maintained frontend.

## Local development

### Backend

~~~bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
~~~

### Frontend

~~~bash
cd client
npm ci
cp .env.example .env
npm run dev
~~~

The frontend normally runs on http://localhost:5173 and the API on http://localhost:8000.

See docs/development.md for environment configuration, testing, and deployment notes.

## Verification

The repository keeps deterministic clinical-memory and LLM error-handling tests in the backend. CI also performs frontend compilation/build validation and Python syntax compilation.

Before opening a PR:

~~~bash
cd client && npm ci && npm run build
cd ../backend && python -m compileall -q .
~~~

For production deployment, run the backend preflight checks and validate the deployed health endpoint before promoting a release.

## Security and privacy

NeuroScribe handles clinical information, so repository hygiene and patient isolation are core requirements.

- Never commit .env files, API keys, JWT secrets, database credentials, or real patient data.
- Retrieval is scoped to the authenticated owner and selected patient.
- LLM output is not allowed to invent missing clinical facts.
- Medication questions are evidence-gated; recommendation requests are refused.
- Internal model/runtime diagnostics are logged server-side and sanitized from API errors.

See SECURITY.md and docs/security/ for the security model and historical verification records.

## Status

The current production baseline includes authenticated patient workflows, report OCR, clinical-memory retrieval, Ask NeuroScribe intent routing, patient isolation, and safe LLM error handling.

## License

No open-source license is currently declared. All rights are reserved unless a license is added to this repository.
