# NeuroScribe Architecture

## System boundaries

NeuroScribe is split into an independently deployable API and browser client.

### Frontend — client/

- React 19 + TypeScript
- Vite
- React Router
- TanStack Query
- Axios
- Tailwind CSS and shared UI primitives
- Feature-oriented modules under src/features/
- Page-level composition under src/pages/
- Authentication under src/auth/

The browser never accesses the database directly. It communicates with FastAPI over HTTP and sends the authenticated bearer token.

### Backend — backend/

- FastAPI HTTP API
- SQLAlchemy persistence
- JWT authentication
- Report OCR using Tesseract/Poppler
- Sentence-transformer embeddings
- FAISS semantic retrieval
- Clinical-memory orchestration
- Groq transcription and LLM generation
- Evidence validation and safe fallback behavior

### Data flow

#### Report workflow

~~~text
PDF upload
   ↓
Report record
   ↓
OCR / text extraction
   ↓
Text cleaning + preprocessing
   ↓
Clinical extraction
   ↓
Chunking + embeddings
   ↓
FAISS metadata
   ↓
Patient-scoped retrieval
~~~

#### Consultation workflow

~~~text
Audio upload
   ↓
Groq transcription
   ↓
Transcript/session record
   ↓
Clinical note generation/editing
   ↓
Patient clinical memory
~~~

#### Ask NeuroScribe

~~~text
Question + patient_id
        ↓
Authenticate current user
        ↓
Verify patient ownership
        ↓
Detect query intent
        ↓
Retrieve only that patient's context
        ↓
Evidence validation / deterministic extraction
        ↓
LLM generation when supported
        ↓
Answer + source chunks
~~~

### Retrieval safety

Patient isolation is enforced before generation. The retrieval layer receives both the authenticated owner identity and the requested patient identity. FAISS results are filtered using stored ownership/patient metadata, with database-backed fallback retrieval where required.

The LLM is not treated as the source of truth. When the requested information is absent or unsupported, the system returns a safe not-found response instead of asking the model to guess.

### Ask query intents

The current intent router covers:

- last consultation
- patient statements
- active medications
- medication history
- patient overview
- recent history
- lab results
- medication recommendation requests
- general clinical questions

Medication recommendation requests are explicitly safety-gated. Active-medication answers require medication evidence or an explicit documented statement that no medication is active.

### Deployment

The backend is containerized with backend/Dockerfile and is suitable for Railway-style container deployment. The active frontend is the Vite SPA in client/ and is configured for static deployment with client/vercel.json.

Keep deployment secrets in the platform environment, never in Git.
