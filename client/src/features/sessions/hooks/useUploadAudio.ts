// useUploadAudio hook — Whisper audio transport pipeline
// Architecture ref: frontend_architecture.md §5.3, §6.4

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadAudio } from '../services/sessions.service';
import { QUERY_KEYS } from '@/utils/constants';

interface UploadAudioParams {
  sessionId: string;
  audioFile: File;
}

export function useUploadAudio(patientId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sessionId, audioFile }: UploadAudioParams) => uploadAudio(sessionId, audioFile),
    onSuccess: (_, { sessionId }) => {
      // Invalidate both single session and the general listing
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.session(sessionId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sessions(patientId || '') });
    },
  });
}
