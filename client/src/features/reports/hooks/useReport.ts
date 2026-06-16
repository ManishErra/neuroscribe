import { useQuery } from '@tanstack/react-query';
import { fetchReportDetail } from '../services/reports.service';
import { QUERY_KEYS } from '@/utils/constants';

export function useReport(reportId: string | undefined) {
  return useQuery({
    queryKey: QUERY_KEYS.report(reportId || ''),
    queryFn: () => fetchReportDetail(reportId || ''),
    enabled: !!reportId,
  });
}
