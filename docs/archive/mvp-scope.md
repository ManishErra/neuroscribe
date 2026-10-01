## NeuroScribe — MVP Scope

### V1 INCLUDES (build these, nothing else)

- Audio file upload (MP3/WAV/M4A, max 100MB)
- Whisper transcription via Groq API
- Structured SOAP note generation via LLM
- Editable note UI — doctor must review before saving
- Patient list + session history view
- Vector search: "when did sleep worsen?" returns answer + session date
- PDF/image report upload + OCR text extraction
- AI output badge on every AI-generated element

### V1 DOES NOT INCLUDE (write this to resist temptation)

- Real-time ambient recording
- GraphRAG
- WhatsApp integration
- ABDM/FHIR export
- Multi-user auth (demo = single login)
- Diagnosis or risk classification (NEVER in any version)
- Diarization (V2 feature — document why)

### Success metrics

- Transcription accuracy > 85% on clean English audio
- RAG retrieval correct > 90% of time
- Full demo runs without errors for 10 sessions
- Note generated in under 30 seconds

### Primary goal

Portfolio project. Fake patient data only.
No real patients. No clinical deployment.