// Shared Patient types — API response shapes from /patients/ and /patient-overview/.
// Architecture ref: frontend_architecture.md §3.1

export interface Patient {
  id: string;
  name: string;
  age: number;
  gender: string;
  created_at: string;
}

export interface PatientOverview {
  patient_id: string;
  status: 'STABLE' | 'WARNING' | 'CRITICAL';
  clinical_flags: string[];
  latest_labs: Record<string, string>;  // e.g. { hemoglobin: "9.2 g/dL" }
  last_activity: {
    type: string;
    date: string;
    id: string;
  };
}
