// useSessions hook — fetches patient session summaries
// Architecture ref: frontend_architecture.md §5.3, §6.3

import { useQuery } from '@tanstack/react-query';
import { fetchPatientSessions } from '../services/sessions.service';
import { QUERY_KEYS } from '@/utils/constants';
import type { SessionSummary } from '../services/sessions.service';

export function useSessions(patientId: string | undefined) {
  return useQuery<SessionSummary[], Error>({
    queryKey: QUERY_KEYS.sessions(patientId || ''),
    queryFn: () => fetchPatientSessions(patientId || ''),
    enabled: !!patientId,
  });
}
