// useSession hook — fetches full single session details
// Architecture ref: frontend_architecture.md §5.3, §6.3

import { useQuery } from '@tanstack/react-query';
import { fetchSession } from '../services/sessions.service';
import { QUERY_KEYS } from '@/utils/constants';
import type { SessionDetail } from '../services/sessions.service';

export function useSession(sessionId: string | undefined) {
  return useQuery<SessionDetail, Error>({
    queryKey: QUERY_KEYS.session(sessionId || ''),
    queryFn: () => fetchSession(sessionId || ''),
    enabled: !!sessionId,
  });
}
