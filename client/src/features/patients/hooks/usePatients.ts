// usePatients hook — wraps fetchPatients query
// Architecture ref: frontend_architecture.md §6.3

import { useQuery } from '@tanstack/react-query';
import { fetchPatients } from '../services/patients.service';
import { QUERY_KEYS } from '@/utils/constants';
import type { Patient } from '@/types/patient.types';

export function usePatients() {
  return useQuery<Patient[], Error>({
    queryKey: QUERY_KEYS.patients(),
    queryFn: fetchPatients,
  });
}
