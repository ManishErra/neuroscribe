// Patient API service — endpoints from backend patients router
// Architecture ref: frontend_architecture.md §2, §14

import client from '@/api/axiosClient';
import type { Patient } from '@/types/patient.types';

/**
 * Fetch all patients from the backend, ordered by created_at desc.
 */
export async function fetchPatients(): Promise<Patient[]> {
  return client.get('/patients/');
}

/**
 * Fetch a single patient by ID.
 */
export async function fetchPatient(patientId: string): Promise<Patient> {
  return client.get(`/patients/${patientId}`);
}

/**
 * Create a new patient.
 */
export async function createPatient(data: { name: string; age: number; gender: string }): Promise<Patient> {
  return client.post('/patients/', data);
}
