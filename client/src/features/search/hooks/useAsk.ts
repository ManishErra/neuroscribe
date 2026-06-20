// useAsk hook — mutation wrapper for semantic RAG search queries.
// Architecture ref: frontend_architecture.md §14

import { useMutation } from '@tanstack/react-query';
import { postAsk } from '../services/search.service';
import { useSettings } from '@/store/SettingsContext';
import type { AskResponse } from '../types/search.types';

export function useAsk() {
  const { settings } = useSettings();

  return useMutation<AskResponse, Error, { question: string; patientId: string }>({
    mutationFn: async ({ question, patientId }) => {
      if (!settings.aiRagEnabled) {
        throw new Error('Clinical Intelligence Engine is disabled. Enable RAG under Settings.');
      }
      
      const cleanQuestion = question.trim();
      if (!cleanQuestion) {
        throw new Error('Please enter a clinical question.');
      }

      return postAsk(cleanQuestion, patientId);
    },
  });
}
