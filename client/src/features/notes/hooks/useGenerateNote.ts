// useGenerateNote hook — Whisper transcript SOAP note drafting
// Architecture ref: frontend_architecture.md §5.4, §6.4

import { useMutation } from '@tanstack/react-query';
import { generateNote } from '../services/notes.service';

interface GenerateNoteParams {
  transcriptId: string;
  patientName: string;
  patientAge: number;
}

export function useGenerateNote() {
  return useMutation({
    mutationFn: ({ transcriptId, patientName, patientAge }: GenerateNoteParams) =>
      generateNote(transcriptId, patientName, patientAge),
  });
}
