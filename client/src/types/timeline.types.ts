// Shared Timeline types — API response shape from /timeline/.
// Architecture ref: frontend_architecture.md §3.5

export interface LabHistoryItem {
  report_id: string;
  report_date: string | null;
  value: string;
  numeric_value: number | null;
  unit: string;
  status: string;
}

export interface LabTimelineDetails {
  report_count: number;
  latest_value: string | null;
  latest_date: string | null;
  trend: 'IMPROVING' | 'DECLINING' | 'STABLE' | 'INSUFFICIENT_DATA';
  history: LabHistoryItem[];
}

export interface PatientTimelineResponse {
  patient_id: string;
  patient_name: string;
  timeline: Record<string, LabTimelineDetails>;
}
