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
# NeuroScribe Development Progress Log

---

# Day 11 — Semantic Embedding Pipeline

## Objective
Build the semantic embedding foundation for medical report retrieval.

## Implemented
- SentenceTransformer embedding generation
- all-MiniLM-L6-v2 embedding model
- Embedding preprocessing pipeline
- Chunk-level embedding creation
- Metadata-linked embeddings

## Files Added
- embeddings.py
- report_embeddings.py

## Key Learnings
- Semantic embeddings
- Vector representation
- Chunk-level retrieval design
- Embedding dimensionality handling

---

# Day 12 — FAISS Vector Database Integration

## Objective
Implement semantic vector search using FAISS.

## Implemented
- FAISS IndexFlatIP vector index
- Cosine similarity retrieval
- Vector normalization
- Metadata persistence
- On-disk FAISS storage
- Retrieval ranking pipeline

## Features
- Top-K semantic retrieval
- Persistent vector storage
- Retrieval debugging logs
- Similarity score ranking

## Files Added
- report_vector_store.py

## Key Learnings
- Approximate nearest neighbor retrieval
- Cosine similarity search
- FAISS indexing
- Retrieval architecture

---

# Day 13 — Hybrid Clinical RAG Pipeline

## Objective
Connect semantic retrieval with LLM-based medical QA.

## Implemented
- Retrieval-Augmented Generation (RAG)
- Context-aware prompting
- Medical-safe prompting
- Semantic search endpoint
- LLM orchestration pipeline

## Features
- Ask endpoint
- Semantic chunk retrieval
- Context injection into prompts
- Controlled clinical responses

## Files Updated
- llm_service.py
- routers/search.py

## Key Learnings
- RAG system architecture
- Prompt engineering
- Context grounding
- AI orchestration patterns

---

# Day 14 — Retrieval Optimization & Query Expansion

## Objective
Improve retrieval quality and semantic matching.

## Implemented
- Medical synonym expansion
- Query preprocessing improvements
- Oversampled retrieval
- Similarity threshold tuning
- Retrieval debugging tools
- Keyword boosting experiments

## Features
- Expanded medical query support
- Improved retrieval recall
- Better semantic matching
- Threshold-controlled filtering

## Examples
- hemoglobin → hb, hgb
- glucose → sugar, blood glucose

## Key Learnings
- Retrieval tuning
- Hybrid search strategies
- Semantic recall vs precision tradeoffs
- Clinical query normalization

---

# Day 15 — Structured Clinical Extraction + Hallucination Prevention

## Objective
Reduce hallucinations using deterministic medical extraction before LLM generation.

## Implemented
- Structured clinical extraction layer
- Regex-based lab value extraction
- Deterministic answer routing
- Hybrid extraction + LLM pipeline
- Clinical safety-first architecture

## Features
- Hemoglobin extraction
- Glucose extraction
- Structured extraction fallback
- Hallucination prevention
- Safe answer routing

## Files Added
- clinical_extractors.py

## Files Updated
- llm_service.py

## System Improvements
- Reduced hallucinated responses
- More deterministic medical answers
- Better clinical reliability
- Safer AI behavior

## Key Learnings
- Clinical AI safety
- Deterministic extraction systems
- Hybrid symbolic + neural AI
- Hallucination mitigation techniques

---

# Overall System Status After Day 15

## Completed Core Systems

### OCR Pipeline
- PDF ingestion
- OCR extraction
- Text cleaning

### Semantic Retrieval
- Embedding generation
- FAISS vector storage
- Similarity retrieval

### Hybrid Clinical AI
- RAG pipeline
- Structured extraction
- Safe LLM orchestration

### API Layer
- FastAPI backend
- Swagger UI testing
- Search endpoints

---

# Current Architecture

```text
Medical Report
      ↓
OCR Extraction
      ↓
Text Cleaning
      ↓
Chunking
      ↓
Embedding Generation
      ↓
FAISS Vector Store
      ↓
Semantic Retrieval
      ↓
Structured Extraction
      ↓
LLM Reasoning
      ↓
Clinical Answer
---

# Day 16 — Clinical Entity Extraction & Hallucination Prevention

## Objective

Implement deterministic clinical entity extraction to reduce hallucinations
and improve reliability of medical question answering.

---

## Implemented

- Regex-based clinical entity extraction
- Structured medical value parsing
- Deterministic QA pipeline
- Hybrid extraction + LLM orchestration
- Hallucination prevention layer
- Clinical-safe fallback responses
- Structured JSON medical responses

---

## Features

### Clinical Entity Extraction

Implemented extraction for:

- Hemoglobin
- Glucose
- Platelets
- WBC
- RBC
- Creatinine
- Bilirubin

---

### Deterministic Medical QA

System now attempts:

1. Structured extraction first
2. Deterministic response generation
3. LLM fallback only when necessary

This greatly improves medical reliability.

---

### Hallucination Prevention

If structured clinical data is absent:

```text
"The report does not contain this information."
# Day 17 - Advanced Medical Retrieval Engine

## Objective

Enhance NeuroScribe's retrieval layer by implementing a persistent FAISS vector database with medical-aware hybrid search.

## Features Implemented

### Persistent Vector Store

* FAISS index persistence
* Metadata persistence using JSON
* Automatic index loading during application startup
* Consistency validation between vectors and metadata

### Semantic Search

* Cosine similarity retrieval using normalized embeddings
* Top-K chunk retrieval
* Configurable similarity thresholds

### Medical Query Expansion

Implemented synonym-based query enrichment for common clinical terminology.

Examples:

* Hemoglobin → Hb, Hgb
* Glucose → Sugar, Blood Glucose
* WBC → White Blood Cell
* RBC → Red Blood Cell

### Hybrid Retrieval Scoring

Combined:

* Semantic similarity score
* Keyword match boosting
* Laboratory value detection boosting

This improves retrieval quality for clinical reports and diagnostic documents.

### Clinical Data Awareness

Added automatic laboratory-value detection using regex patterns to prioritize medically relevant chunks.

### Retrieval Debugging

Implemented retrieval logging showing:

* User query
* Similarity scores
* Retrieved chunk identifiers
* Content previews

## Technical Components

* FAISS
* Sentence Transformer Embeddings
* NumPy
* FastAPI Integration

## Outcome

NeuroScribe now supports persistent, medically optimized Retrieval-Augmented Generation (RAG) capable of locating clinically relevant report sections with improved accuracy and explainability.
# NeuroScribe Development Log
## Days 18–20 Milestone
### Clinical Intelligence, Retrieval Optimization & Explainability

---

# Overview

This milestone focused on improving NeuroScribe's clinical extraction accuracy, retrieval quality, evaluation framework, and answer transparency.

The system evolved from a basic OCR → RAG pipeline into an explainable clinical AI assistant capable of deterministic extraction, retrieval validation, confidence scoring, and source attribution.

---

# Day 18 – Clinical Extraction Validation & Bug Fixing

## Objective

Improve the reliability of clinical entity extraction and eliminate extraction failures caused by OCR noise, duplicate reports, and laboratory formatting variations.

---

## Features Implemented

### Clinical Entity Extraction Enhancements

Improved extraction support for:

- Hemoglobin (Hb, HGB, Haemoglobin)
- WBC
- RBC
- Platelets
- Glucose
- Creatinine
- Bilirubin

---

### OCR Noise Tolerance

Enhanced regex patterns to handle OCR-generated artifacts:

Examples:

WBC Count ... 10570

Platelet Count ----- 150000

RBC | 4.79

Hemoglobin Colorimetric 14.5 g/dL

---

### Hemoglobin Extraction Improvements

Resolved multiple extraction issues:

- HbA1c interference
- HbA2 false positives
- Electrophoresis report contamination
- Percentage value misclassification

Implemented:

- Context-aware filtering
- Physiological range validation
- Same-line extraction safeguards
- Local context blocking

---

### Clinical Reference Range Classification

Added deterministic interpretation logic:

| Test | Normal Range |
|--------|--------|
| Hemoglobin | 12–17 g/dL |
| WBC | 4000–11000 /cmm |
| RBC | 4.5–5.9 million/cmm |
| Platelets | 150000–450000 /cmm |
| Glucose | 70–110 mg/dL |

---

### Automated Validation Suite

Implemented and validated:

- Hemoglobin extraction
- HbA1c prevention
- WBC extraction
- RBC extraction
- Platelet extraction
- OCR noise handling
- End-to-end clinical QA validation

Result:

ALL TESTS PASSED SUCCESSFULLY

---

## Outcome

NeuroScribe achieved stable and deterministic clinical entity extraction with robust OCR tolerance and accurate laboratory value classification.

---

# Day 19 – Query Rewriting & Retrieval Evaluation

## Objective

Improve retrieval accuracy and establish measurable evaluation metrics for the RAG pipeline.

---

## Features Implemented

### Clinical Query Rewriter

Created:

backend/clinical_query_rewriter.py

Expanded medical abbreviations and synonyms automatically.

Examples:

Hb → Hemoglobin, HGB

WBC → White Blood Cell

RBC → Red Blood Cell

Platelet → PLT

---

### Retrieval Evaluation Framework

Created:

backend/evaluation_cases.json

backend/evaluate_retrieval.py

Implemented automated retrieval benchmarking.

---

### Retrieval Metrics

Measured:

- Top-1 Accuracy
- Top-5 Accuracy
- Retrieval Accuracy

---

### Retrieval Improvements

#### Duplicate Chunk Suppression

Implemented text-based de-duplication to prevent duplicate report uploads from saturating retrieval results.

---

#### Medical Keyword Boosting

Added domain-specific keyword relevance scoring.

---

#### Hemoglobin Retrieval Optimization

Added laboratory unit prioritization:

g/dL

This ensured CBC Hemoglobin values ranked above HbA1c analytical content.

---

### Evaluation Results

Total Test Cases : 6

Passed : 6

Failed : 0

Top-1 Accuracy : 66.67%

Top-5 Accuracy : 100.00%

Retrieval Accuracy : 100.00%

---

## Outcome

NeuroScribe now retrieves clinically relevant chunks consistently and can quantitatively evaluate retrieval quality.

---

# Day 20 – Confidence & Explainability Layer

## Objective

Make NeuroScribe responses transparent, explainable, and auditable.

---

## Features Implemented

### Confidence Scoring Engine

Created:

backend/confidence_scoring.py

Implemented weighted confidence calculation:

Confidence =
(Retrieval Score × 0.40)
+
(Extraction Certainty × 0.50)
+
(Direct Match Bonus × 0.10)

Where:

- Retrieval Score = FAISS similarity score
- Extraction Certainty = 0.95 for deterministic extraction
- Extraction Certainty = 0.75 for LLM fallback
- Direct Match Bonus = 0.10 when the entity appears explicitly in the source chunk

---

### Confidence Labels

Added human-readable confidence categories:

| Score | Label |
|---------|---------|
| ≥ 0.85 | HIGH |
| 0.60–0.84 | MEDIUM |
| < 0.60 | LOW |

Implemented confidence rounding before classification to prevent floating-point precision issues.

---

### Confidence Reasons

Added explainability support:

Example:

{
  "confidence_reason": [
    "Deterministic regex extraction",
    "High similarity score",
    "Top 3 retrieval result",
    "Direct entity name match"
  ]
}

---

### Confidence Breakdown

Added visibility into confidence components:

{
  "confidence_breakdown": {
    "retrieval_component": 0.34,
    "extraction_component": 0.47,
    "direct_match_component": 0.10
  }
}

---

### Source Attribution

Added answer provenance metadata:

- retrieval_score
- source_chunk_rank
- source_report_id
- source_preview

Example:

{
  "retrieval_score": 0.847,
  "source_chunk_rank": 3,
  "source_report_id": "report-id",
  "source_preview": "Hemoglobin Colorimetric 14.5 g/dL..."
}

---

### API Response Enrichment

Clinical responses now include:

{
  "test": "hemoglobin",
  "value": "14.5 g/dL",
  "status": "NORMAL",
  "confidence": 0.91,
  "confidence_label": "HIGH",
  "confidence_reason": [...],
  "confidence_breakdown": {...},
  "retrieval_score": 0.847,
  "source_chunk_rank": 3,
  "source_preview": "...",
  "source_report_id": "..."
}

---

### Query Preservation Verification

Verified:

- Original user query remains unchanged.
- Query rewriting is used internally only.
- User-facing responses preserve the original question.

---

### Validation

Created:

backend/validate_api_responses.py

Validated:

- Hemoglobin
- WBC
- RBC
- Platelets

All enriched responses generated successfully.

---

### Regression Testing

#### Day 18 Clinical Extraction Suite

Status: PASSED

Verified:

- Hemoglobin extraction
- HbA1c prevention
- WBC extraction
- RBC extraction
- Platelet extraction
- OCR noise handling
- End-to-end clinical QA

---

#### Day 19 Retrieval Evaluation

Status: PASSED

Results:

Total Test Cases : 6

Passed : 6

Failed : 0

Top-1 Accuracy : 66.67%

Top-5 Accuracy : 100.00%

Retrieval Accuracy : 100.00%

---

## Outcome

NeuroScribe now provides:

- Explainable clinical answers
- Confidence scoring
- Confidence labels
- Confidence reasons
- Confidence breakdown diagnostics
- Retrieval transparency
- Source attribution
- Auditability of responses

---

# Milestone Outcome (Days 18–20)

By the end of Day 20, NeuroScribe evolved into an explainable clinical AI pipeline with:

### Clinical Intelligence

- Deterministic clinical extraction
- Clinical range interpretation
- OCR-tolerant parsing

### Retrieval Intelligence

- Clinical query rewriting
- Retrieval evaluation framework
- Retrieval accuracy metrics
- Duplicate suppression
- Medical keyword boosting

### Explainability

- Confidence scoring
- Confidence labels
- Confidence reasons
- Confidence breakdown
- Source attribution
- Retrieval transparency

---

# Current Architecture

PDF Upload
↓
OCR Extraction
↓
Clinical Text Preprocessing
↓
Chunking
↓
Embedding Generation
↓
FAISS Vector Search
↓
Clinical Query Rewriting
↓
Retrieval Evaluation
↓
Clinical Entity Extraction
↓
Confidence Scoring
↓
Explainability Layer
↓
Clinical Answer Generation

---

# Project Status

Day 18 ✅ Complete

Day 19 ✅ Complete

Day 20 ✅ Complete

Day 21 ✅ Complete

---

# Next Milestone

Day 22 – Advanced Multi-Patient Cohort Analytics

Goal:
Support multi-patient dashboard analytics, clinical cohorts grouping, and semantic patient cohorts query retrieval.

# Day 22 – Clinical Comparison & Change Detection

## Goal

Enable NeuroScribe to compare a patient's most recent clinical reports and identify meaningful laboratory changes over time.

The objective was to move beyond simple timeline visualization and provide automated change detection, percentage calculations, and clinical interpretation between consecutive reports.

---

## Features Implemented

### Clinical Comparison Engine

Created a dedicated comparison layer that analyzes the two most recent chronological reports for a patient and calculates:

* Previous laboratory value
* Current laboratory value
* Absolute change
* Percentage change
* Clinical change classification

Supported laboratory markers:

* Hemoglobin
* WBC
* RBC
* Platelets
* Glucose

---

### Clinical Significance Thresholds

Implemented medical significance thresholds to prevent meaningless fluctuations from being classified as real clinical changes.

Thresholds:

| Test       | Threshold       |
| ---------- | --------------- |
| Hemoglobin | 0.5 g/dL        |
| WBC        | 500 /cmm        |
| RBC        | 0.1 million/cmm |
| Platelets  | 10,000 /cmm     |
| Glucose    | 5 mg/dL         |

Changes below threshold are classified as:

```text
STABLE
```

---

### Boundary-Aware Clinical Classification

Integrated comparison logic with the reference ranges already used throughout NeuroScribe.

Classification outcomes:

```text
IMPROVED
WORSENED
STABLE
INSUFFICIENT_DATA
```

Decision logic:

* Movement toward healthy reference range → IMPROVED
* Movement away from healthy reference range → WORSENED
* Clinically insignificant change → STABLE
* Missing historical data → INSUFFICIENT_DATA

---

### FastAPI Endpoint

Added a dedicated comparison endpoint:

```http
GET /compare/{patient_id}
```

The endpoint returns:

* Patient information
* Previous value
* Current value
* Absolute difference
* Percentage difference
* Clinical interpretation

---

## Example Response

```json
{
  "patient_id": "51773efc-479b-469d-931d-cd483786c20e",
  "patient_name": "Radhika Erra",
  "comparison": {
    "hemoglobin": {
      "previous_value": "14.5 g/dL",
      "current_value": "14.5 g/dL",
      "absolute_change": 0.0,
      "percentage_change": 0.0,
      "change_classification": "STABLE"
    }
  }
}
```

---

## Files Created

```text
backend/clinical_comparison.py
backend/routers/comparison.py
backend/comparison_tests.py
```

---

## Files Modified

```text
backend/main.py
docs/build-log.md
```

---

## Validation Performed

### Day 22 Tests

```text
comparison_tests.py
PASS
```

Validated:

* Threshold calculations
* Percentage calculations
* Stable classifications
* Improved classifications
* Worsened classifications
* Insufficient-data scenarios
* Router endpoint behavior

---

### Real Database Verification

Patient Tested:

```text
Radhika Erra
51773efc-479b-469d-931d-cd483786c20e
```

Result:

```text
Hemoglobin  : STABLE
WBC         : STABLE
RBC         : STABLE
Platelets   : STABLE
Glucose     : INSUFFICIENT_DATA
```

The comparison endpoint successfully processed real database records and returned valid clinical interpretations.

---

## Regression Verification

All previous milestones remain operational.

### Day 18

```text
run_tests.py
PASS
```

Clinical extraction remains functional.

### Day 19

```text
evaluate_retrieval.py
PASS
```

Retrieval quality remains unchanged.

### Day 20

```text
validate_api_responses.py
PASS
```

Confidence scoring and explainability remain functional.

### Day 21

```text
timeline_tests.py
PASS
```

Clinical timeline generation remains functional.

---

## Architecture Status

Completed Components:

```text
OCR Processing                     ✅
Report Chunking                    ✅
Embedding Generation               ✅
FAISS Vector Search                ✅
Clinical Entity Extraction         ✅
Clinical Confidence Scoring        ✅
Clinical Timeline Generation       ✅
Clinical Comparison Engine         ✅
```

---

## Outcome

Day 22 successfully introduced longitudinal clinical comparison and change detection capabilities to NeuroScribe.

The platform can now:

* Track laboratory values across reports
* Quantify changes over time
* Detect clinically meaningful movement
* Provide structured comparison responses through the API
* Support future trend analytics and cohort-level analysis

Status:

✅ Day 22 Complete
✅ Production Verified
✅ Regression Safe
