import { useMutation, useQueryClient } from '@tanstack/react-query';
import { deleteReport } from '../services/reports.service';
import { QUERY_KEYS } from '@/utils/constants';

export function useDeleteReport(patientId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ reportId }: { reportId: string }) => {
      return deleteReport(reportId);
    },
    onSuccess: () => {
      if (patientId) {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.reports(patientId) });
      }
    },
  });
}
