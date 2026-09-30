import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { runOcr } from '../services/reports.service';
import { QUERY_KEYS } from '@/utils/constants';

export function useRunOcr(patientId: string | undefined) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
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

  // OCR now runs as a background job. Poll the report until the backend
  // transitions it from pending -> ready/failed.
  useEffect(() => {
    const reportId = mutation.data?.id;
    if (!reportId) return;

    const interval = window.setInterval(() => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.report(reportId) });
      if (patientId) {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.reports(patientId) });
      }
    }, 2000);

    return () => window.clearInterval(interval);
  }, [mutation.data?.id, patientId, queryClient]);

  return mutation;
}
