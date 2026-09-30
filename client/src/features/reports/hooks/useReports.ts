import { useQuery } from '@tanstack/react-query';
import { fetchPatientReports } from '../services/reports.service';
import { QUERY_KEYS } from '@/utils/constants';

export function useReports(patientId: string | undefined) {
  return useQuery({
    queryKey: QUERY_KEYS.reports(patientId || ''),
    queryFn: () => fetchPatientReports(patientId || ''),
    enabled: !!patientId,
    refetchInterval: (query) => query.state.data?.some((report) => report.ocr_status === 'processing') ? 2000 : false,
  });
}
