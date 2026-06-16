import { useMutation, useQueryClient } from '@tanstack/react-query';
import { uploadReport } from '../services/reports.service';
import { QUERY_KEYS } from '@/utils/constants';

export function useUploadReport(patientId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file }: { file: File }) => {
      if (!patientId) {
        return Promise.reject(new Error('Patient ID is required for report upload.'));
      }
      return uploadReport(patientId, file);
    },
    onSuccess: () => {
      if (patientId) {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.reports(patientId) });
      }
    },
  });
}
