// usePatient hook — wraps fetchPatient by ID query
// Architecture ref: frontend_architecture.md §6.3

import { useQuery } from '@tanstack/react-query';
import { fetchPatient } from '../services/patients.service';
import { QUERY_KEYS } from '@/utils/constants';
import type { Patient } from '@/types/patient.types';

export function usePatient(patientId: string | undefined) {
  return useQuery<Patient, Error>({
    queryKey: QUERY_KEYS.patient(patientId || ''),
    queryFn: () => fetchPatient(patientId || ''),
    enabled: !!patientId,
  });
}
