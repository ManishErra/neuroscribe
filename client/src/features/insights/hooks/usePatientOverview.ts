// usePatientOverview hook — wraps fetchPatientOverview query
// Architecture ref: frontend_architecture.md §5.2, §6.3

import { useQuery } from '@tanstack/react-query';
import { fetchPatientOverview } from '../services/insights.service';
import { QUERY_KEYS } from '@/utils/constants';
import type { PatientOverview } from '@/types/patient.types';

export function usePatientOverview(patientId: string | undefined) {
  return useQuery<PatientOverview, Error>({
    queryKey: QUERY_KEYS.patientOverview(patientId || ''),
    queryFn: () => fetchPatientOverview(patientId || ''),
    enabled: !!patientId,
  });
}
