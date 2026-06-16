// Shared Comparison types — API response shape from /compare/.
// Architecture ref: frontend_architecture.md §3.6

export interface ComparisonItem {
  test: string;
  previous: string | null;
  current: string | null;
  delta: string | null;
  trend: 'improving' | 'worsening' | 'stable' | 'new';
}

export interface PatientComparison {
  patient_id: string;
  patient_name: string;
  comparison: ComparisonItem[];
}
