// Shared Session types — API response shapes from /sessions/.
// Architecture ref: frontend_architecture.md §3.2

export interface SessionSummary {
  id: string;
  session_date: string;
  has_note: boolean;
  note_finalized: boolean;
}

export interface ClinicalNote {
  presenting_complaint: string;
  symptoms_mentioned: string[];
  medications_mentioned: string[];
  sleep: string;
  mood_in_patient_words: string;
  social_context: string;
  plan_discussed: string;
  flags_for_review: string;
  confidence: string;
}

export interface SessionDetail {
  id: string;
  session_date: string;
  transcript: string | null;
  note: ClinicalNote | null;
  note_finalized: boolean;
}
