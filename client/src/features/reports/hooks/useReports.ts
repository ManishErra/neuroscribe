import { useQuery } from '@tanstack/react-query';
import { fetchPatientReports } from '../services/reports.service';
import { QUERY_KEYS } from '@/utils/constants';

export function useReports(patientId: string | undefined) {
  return useQuery({
    queryKey: QUERY_KEYS.reports(patientId || ''),
    queryFn: () => fetchPatientReports(patientId || ''),
    enabled: !!patientId,
  });
}
