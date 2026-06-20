import { useMutation, useQueryClient } from '@tanstack/react-query';
import { createPatient } from '../services/patients.service';
import { QUERY_KEYS } from '@/utils/constants';

export function useCreatePatient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createPatient,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patients() });
    },
  });
}
