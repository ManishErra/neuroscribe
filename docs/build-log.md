## Build Log

### Day 2
- MVP Scope doc written and locked
- DB Schema doc written
- All 6 tables created in Supabase
- Backend connected to Supabase DB
- Groq API key obtained
- Known: no audio pipeline yet — starts Day 3

### Next session goal
Build audio upload endpoint (POST /upload-audio)
### Day 3
- Installed Groq SDK and audio libraries
- Created /upload-audio endpoint
- Added audio validation and size limits
- Connected Groq Whisper transcription
- Successfully transcribed real audio
- Saved transcripts to Supabase DB
- Built frontend upload UI
- Fixed CORS issue between frontend and backend
- End-to-end upload → transcription → DB save working

### Next session goal
Generate AI SOAP notes from transcripts
### Day 4
- Built AI clinical note generation workflow
- Added editable AI draft review UI
- Added finalized note protection logic
- Preserved AI draft separately from doctor-edited version
- Added save-note endpoint
- Completed full upload → transcript → note → finalize pipeline

### Day 5
- Built patient management backend APIs
- Added patient CRUD endpoints
- Built patient list page
- Built add patient form
- Added reusable navbar navigation
- Connected frontend with patient APIs

### Day 6
- Built patient detail page using dynamic routing
- Added session management backend
- Added create session functionality
- Added patient session timeline UI
- Added note status indicators
- Connected sessions to patients
### Day 7

- Built AI clinical note generation pipeline
- Integrated Groq Whisper transcription
- Added structured SOAP-style note generation
- Added doctor review + finalize workflow
- Added session detail viewer
- Connected frontend + backend session history
- Added safety filtering for psychiatric outputs

### Current Status

End-to-end AI documentation workflow operational
## Day 8 — Embeddings + Vector Search Foundation

### Completed

- Installed sentence-transformers
- Added local embedding generation
- Implemented transcript/note chunking
- Enabled pgvector extension in PostgreSQL
- Created embeddings table
- Built embedding utility pipeline
- Added finalized-note embedding endpoint
- Stored semantic vectors in pgvector
- Added structured schema validation for clinical notes
- Improved backend validation and serialization safety

### Architecture Upgrade

NeuroScribe now supports:

- semantic memory
- vector storage
- AI retrieval foundations
- chunk-based embedding pipelines
- future RAG capabilities

### Technical Notes

- Embedding model:
  all-MiniLM-L6-v2

- Vector dimensions:
  384

- Embeddings generated locally
  (no paid API required)

- pgvector used for semantic storage
# Day 9 — Semantic Search + pgvector Retrieval

## Goals Completed

* Added SentenceTransformer embeddings
* Added text chunking pipeline
* Enabled pgvector in Supabase
* Built embeddings table
* Implemented semantic vector search
* Added `/search` endpoint
* Connected embeddings with notes + sessions
* Tested semantic retrieval using patient queries

---

## Retrieval Test Results

| Query                  | Similarity Score | Result Quality | Notes                          |
| ---------------------- | ---------------- | -------------- | ------------------------------ |
| sleep problems         | 0.115            | Poor           | Dataset too small              |
| patient goals          | 0.456            | Good           | Retrieved English fluency goal |
| medications mentioned  | 0.393            | Moderate       | Retrieved dolo/paracetamol     |
| emotional state        | 0.280            | Weak           | Sparse emotional context       |
| summarize last session | 0.220            | Weak           | Need multiple sessions         |

---

## Problems Faced

### 1. pgvector insertion errors

Issue:

* invalid vector syntax errors

Fix:

* converted embeddings using `str(vec)`

---

### 2. Similarity scores too low

Issue:

* retrieval returning weak matches

Fix:

* lowered similarity threshold from `0.45` to `0.25` temporarily for development dataset

---

### 3. No retrieval results

Issue:

* patient IDs mismatched between Swagger and Supabase

Fix:

* verified IDs directly from patients table in Supabase

---

## Key Learnings

* Learned how vector embeddings work
* Understood cosine similarity search
* Learned pgvector operators (`<=>`)
* Built first semantic retrieval pipeline
* Understood importance of chunk quality and dataset richness

---

# Day 10 — Full RAG Pipeline

## Goals Completed

* Added RAG system prompt
* Built `build_rag_prompt()`
* Added `/search/ask` endpoint
* Connected vector retrieval to Groq LLM
* Added citation verification
* Added hallucination prevention logic
* Added source excerpt return
* Added similarity filtering
* Tested grounded answer generation

---

## RAG Evaluation

| Query                              | Accuracy | Notes                                      |
| ---------------------------------- | -------- | ------------------------------------------ |
| what medications were mentioned    | 4/5      | Correctly retrieved dolo + paracetamol     |
| what goals did the patient discuss | 4/5      | Retrieved English fluency goals            |
| summarize last session             | 2/5      | Dataset too small for strong summarization |
| emotional state discussed          | 2/5      | Weak emotional context in records          |
| what did patient say about family  | 5/5      | Correctly returned "Not found"             |

---

## Important Safety Observation

The RAG system correctly refused to hallucinate information when data was unavailable.

Example:

* family history queries returned:
  `Not found in available records.`

This behavior is preferred over generating fabricated psychiatric information.

---

## Technical Improvements

* Added chunk filtering
* Added reusable validation helpers
* Added safer fallback responses
* Added citation verification
* Improved retrieval debugging
* Added retrieval metadata (`retrieved_chunks`)

---

## Key Learnings

* Learned full Retrieval-Augmented Generation (RAG)
* Understood grounding vs hallucination
* Learned retrieval threshold tuning
* Learned importance of dataset quality
* Built end-to-end AI memory retrieval system

---

## Next Steps

* Add multiple sessions per patient
* Improve semantic richness of notes
* Build frontend RAG search UI
* Improve retrieval quality
* Prepare OCR ingestion pipeline
# Day 10 — RAG Evaluation Log

## Test 1
Query: when did sleep problems start
Score: 4/5
Notes:
Retrieved relevant session correctly.

---

## Test 2
Query: what medications were mentioned
Score: 5/5
Notes:
Correctly retrieved dolo and paracetamol with citations.

---

## Test 3
Query: how has mood changed over sessions
Score: 3/5
Notes:
Limited because only few sessions exist.

---

## Test 4
Query: what did patient say about family
Score: 1/5
Notes:
No family-related data found.

---

## Test 5
Query: summarize last session
Score: 4/5
Notes:
Summary generated correctly from latest records.