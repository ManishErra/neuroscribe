// Shared Timeline types — API response shape from /timeline/.
// Architecture ref: frontend_architecture.md §3.5

export interface TimelineEntry {
  date: string;
  report_id: string;
  labs: Record<string, string>;  // e.g. { hemoglobin: "9.2", wbc: "14.5" }
}

export interface PatientTimeline {
  patient_id: string;
  patient_name: string;
  timeline: TimelineEntry[];
}
