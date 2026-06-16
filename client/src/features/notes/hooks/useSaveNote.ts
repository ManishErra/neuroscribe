// useSaveNote hook — doctor note finalization & saving
// Architecture ref: frontend_architecture.md §5.4, §6.4

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { saveNote } from '../services/notes.service';
import { QUERY_KEYS } from '@/utils/constants';
import type { ClinicalNote } from '@/features/sessions/services/sessions.service';

interface SaveNoteParams {
  noteId: string;
  doctorEdited: ClinicalNote;
  sessionId: string;
  patientId: string;
}

export function useSaveNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ noteId, doctorEdited }: SaveNoteParams) => saveNote(noteId, doctorEdited),
    onSuccess: (_, { sessionId, patientId }) => {
      // Invalidate target session and lists on success
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.session(sessionId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sessions(patientId) });
      
      // Overview might change as well
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patientOverview(patientId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patientInsights(patientId) });
    },
  });
}
