// useCreateSession hook — database session allocation
// Architecture ref: frontend_architecture.md §5.3, §6.4

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createSession } from '../services/sessions.service';
import { QUERY_KEYS } from '@/utils/constants';

export function useCreateSession(patientId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => createSession(patientId || ''),
    onSuccess: () => {
      // Invalidate target sessions lists on success
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.sessions(patientId || '') });
    },
  });
}
