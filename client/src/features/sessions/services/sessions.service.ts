// Sessions API service — backend sessions router endpoints
// Architecture ref: frontend_architecture.md §2, §5.3, §14

import client from '@/api/axiosClient';

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

/**
 * Fetch all sessions for a specific patient.
 */
export async function fetchPatientSessions(patientId: string): Promise<SessionSummary[]> {
  return client.get(`/sessions/patient/${patientId}`);
}

/**
 * Fetch detailed session log by ID (raw transcript + clinical note).
 */
export async function fetchSession(sessionId: string): Promise<SessionDetail> {
  return client.get(`/sessions/${sessionId}`);
}

/**
 * Allocate a new session row in the database.
 */
export async function createSession(patientId: string): Promise<{ id: string }> {
  return client.post('/sessions/', { patient_id: patientId });
}

/**
 * Ingest consultation audio blob and transcription.
 */
export async function uploadAudio(sessionId: string, audioFile: File): Promise<{
  success: boolean;
  transcript: string;
  transcript_id: string;
  session_id: string;
}> {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  formData.append('file', audioFile);

  return client.post('/upload-audio', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}
