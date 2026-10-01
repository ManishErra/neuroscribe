# NeuroScribe Backend

FastAPI service for authentication, patient workflows, consultation processing, report OCR, clinical retrieval, and Ask NeuroScribe.

## Entry point

main.py exposes the FastAPI application as app.

Run locally:

~~~bash
uvicorn main:app --reload --port 8000
~~~

## Important modules

- routers/ — HTTP endpoints
- clinical_memory.py — patient-scoped retrieval orchestration
- query_intents.py — Ask query intent routing
- llm_service.py — Groq LLM integration and safe generation handling
- report_ocr_extract.py — OCR pipeline
- report_vector_store.py — FAISS retrieval and metadata filtering
- embeddings.py — sentence-transformer embeddings
- auth_utils.py — JWT/authentication helpers
- models.py — SQLAlchemy models
- scripts/ — migrations, audits and operational verification tools

See docs/architecture.md for the system-level design.
