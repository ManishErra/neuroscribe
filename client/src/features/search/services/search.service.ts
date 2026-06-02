// Search API Service — handles backend communication for semantic search.
// Architecture ref: frontend_architecture.md §14

import client from '@/api/axiosClient';
import type { AskResponse } from '../types/search.types';

/**
 * Sends a search query to the backend '/ask' endpoint.
 * Retrieval parameter top_k is hardcoded to 5 per requirements.
 */
export async function postAsk(question: string): Promise<AskResponse> {
  return client.post('/ask/', {
    question,
    top_k: 5,
  });
}
