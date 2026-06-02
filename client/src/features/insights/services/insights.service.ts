// Insights & Overview API service — endpoints from backend patient_insights router
// Architecture ref: frontend_architecture.md §2, §14

import client from '@/api/axiosClient';
import type { PatientOverview } from '@/types/patient.types';

/**
 * Fetch a high-level patient overview for the dashboard cards.
 * Returns clinical status, clinical flags, latest extracted labs, and activity.
 */
export async function fetchPatientOverview(patientId: string): Promise<PatientOverview> {
  return client.get(`/patient-overview/${patientId}`);
}
