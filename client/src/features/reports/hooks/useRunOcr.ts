import { useMutation, useQueryClient } from '@tanstack/react-query';
import { runOcr } from '../services/reports.service';
import { QUERY_KEYS } from '@/utils/constants';

export function useRunOcr(patientId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ reportId }: { reportId: string }) => {
      return runOcr(reportId);
    },
    onSuccess: (data) => {
      // Invalidate the single report query
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.report(data.id) });
      
      // Invalidate the list of reports for the patient
      if (patientId) {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.reports(patientId) });
      }
    },
  });
}
