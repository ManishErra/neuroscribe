// Clinical Notes API service — backend notes router endpoints
// Architecture ref: frontend_architecture.md §2, §5.4, §14

import client from '@/api/axiosClient';
import type { ClinicalNote } from '@/features/sessions/services/sessions.service';

export interface GenerateNoteResponse {
  note_id: string;
  ai_draft: ClinicalNote;
  flagged_phrases: string[];
}

export interface SaveNoteResponse {
  status: string;
  note_id: string;
}

/**
 * Generate AI clinical notes draft from an uploaded transcript.
 */
export async function generateNote(
  transcriptId: string,
  patientName: string,
  patientAge: number
): Promise<GenerateNoteResponse> {
  return client.post('/generate-note', {
    transcript_id: transcriptId,
    patient_name: patientName,
    patient_age: patientAge,
  });
}

/**
 * Save and finalize doctor-edited SOAP clinical notes, triggering vector embeddings.
 */
export async function saveNote(noteId: string, doctorEdited: ClinicalNote): Promise<SaveNoteResponse> {
  return client.post('/save-note', {
    note_id: noteId,
    doctor_edited: doctorEdited,
  });
}
