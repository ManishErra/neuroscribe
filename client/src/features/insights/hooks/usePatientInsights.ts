// usePatientInsights hook — wraps fetchPatientInsights query
// Architecture ref: frontend_architecture.md §5.2, §6.3

import { useQuery } from '@tanstack/react-query';
import { fetchPatientInsights } from '../services/insights.service';
import { QUERY_KEYS } from '@/utils/constants';
import type { PatientInsights } from '@/types/insight.types';

export function usePatientInsights(patientId: string | undefined) {
  return useQuery<PatientInsights, Error>({
    queryKey: QUERY_KEYS.patientInsights(patientId || ''),
    queryFn: () => fetchPatientInsights(patientId || ''),
    enabled: !!patientId,
  });
}
