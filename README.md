AI-Powered Clinical Report Intelligence System

NeuroScribe is an experimental clinical AI orchestration system that combines:

OCR pipelines
Semantic medical retrieval
Clinical entity extraction
Hybrid RAG architecture
Deterministic medical parsing
Hallucination-safe LLM workflows

The project is designed as a portfolio-scale AI systems engineering project focused on real-world healthcare document intelligence.

Features
Current Features
PDF medical report upload
OCR extraction
Report preprocessing
Semantic chunking
Embedding generation
FAISS vector database
Semantic medical search
Hybrid clinical RAG
Structured medical extraction
Hallucination prevention
Swagger API interface
Tech Stack
Backend
Python
FastAPI
SQLite
AI / NLP
Sentence Transformers
FAISS
Ollama
TinyLlama
OCR
Tesseract OCR
pdf2image
Architecture
PDF Report
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
Safe LLM Generation
Current AI Capabilities
Semantic Retrieval

Uses vector embeddings and cosine similarity search for medical context retrieval.

Structured Clinical Extraction

Supports deterministic extraction for:

Hemoglobin
Glucose
WBC
Platelets
Hallucination Prevention

Structured medical queries avoid unsupported LLM-generated answers.

API Endpoints
Reports
Upload reports
OCR extraction
Report retrieval
Search
Ask clinical questions
Semantic retrieval
Hybrid RAG answers
Example Queries
What is the hemoglobin level?
Does the patient show signs of anemia?
What is the glucose value?
Future Roadmap
Structured medical timelines
Multi-report patient memory
pgvector migration
Clinical dashboards
Medical risk scoring
Doctor copilot workflows
Multi-agent orchestration
RAG evaluation pipelines
Disclaimer

This project is experimental and not intended for real clinical diagnosis or medical decision-making.

Author

Manish Erra

AI Systems Engineering / Clinical AI Experimentation