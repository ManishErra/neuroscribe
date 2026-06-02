// Insights & Overview API service — endpoints from backend patient_insights router
// Architecture ref: frontend_architecture.md §2, §14

import client from '@/api/axiosClient';
import type { PatientOverview } from '@/types/patient.types';
import type { PatientInsights } from '@/types/insight.types';

/**
 * Fetch a high-level patient overview for the dashboard cards.
 * Returns clinical status, clinical flags, latest extracted labs, and activity.
 */
export async function fetchPatientOverview(patientId: string): Promise<PatientOverview> {
  return client.get(`/patient-overview/${patientId}`);
}

/**
 * Fetch detailed clinical insights (summary, findings, recommendations).
 */
export async function fetchPatientInsights(patientId: string): Promise<PatientInsights> {
  return client.get(`/patient-insights/${patientId}`);
}

