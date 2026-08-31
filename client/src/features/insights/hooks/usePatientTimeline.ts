// usePatientTimeline hook — wraps fetchPatientTimeline query
// Architecture ref: frontend_architecture.md §5.2, §6.3

import { useQuery } from '@tanstack/react-query';
import { fetchPatientTimeline } from '../services/insights.service';
import { QUERY_KEYS } from '@/utils/constants';
import type { PatientTimelineResponse } from '@/types/timeline.types';

export function usePatientTimeline(patientId: string | undefined) {
  return useQuery<PatientTimelineResponse, Error>({
    queryKey: QUERY_KEYS.timeline(patientId || ''),
    queryFn: () => fetchPatientTimeline(patientId || ''),
    enabled: !!patientId,
  });
}
