// TypeScript types & contract definitions for Semantic Search feature.
// Architecture ref: frontend_architecture.md §14

export interface SourceChunk {
  report_id: string;
  chunk_index: number;
  chunk_text: string;
  similarity_score: number;
  chunk_length?: number;
  report_source?: string;
  chunk_position?: number;
}

export interface StructuredAnswer {
  test: string;
  value: string;
  unit?: string;
  status?: string;
  confidence?: number;
  confidence_label?: 'HIGH' | 'MEDIUM' | 'LOW';
  confidence_reason?: string[];
  confidence_breakdown?: {
    retrieval_component: number;
    extraction_component: number;
    direct_match_component: number;
  };
  retrieval_score?: number;
  source_chunk_rank?: number;
  source_preview?: string;
  source_report_id?: string;
}

export interface AskResponse {
  question: string;
  answer: string | StructuredAnswer | StructuredAnswer[];
  chunks_used: SourceChunk[];
}

/**
 * Type guard for checking if an object matches the StructuredAnswer interface.
 */
export function isStructuredAnswer(answer: unknown): answer is StructuredAnswer {
  if (!answer || typeof answer !== 'object' || Array.isArray(answer)) {
    return false;
  }
  const obj = answer as Record<string, unknown>;
  return typeof obj.test === 'string' && typeof obj.value === 'string';
}

/**
 * Type guard for checking if an array contains exclusively StructuredAnswer elements.
 */
export function isStructuredAnswerArray(answer: unknown): answer is StructuredAnswer[] {
  if (!Array.isArray(answer)) {
    return false;
  }
  return answer.every((item) => isStructuredAnswer(item));
}
