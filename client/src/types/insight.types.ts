// Shared Insight types — API response shape from /patient-insights/.
// Architecture ref: frontend_architecture.md §3.4

export interface PatientInsights {
  patient_id: string;
  summary: string;
  findings: string[];
  abnormalities: string[];
  recommendations: string[];
  clinical_flags: string[];
  report_date: string | null;
  trend_summary: string | null;
}
