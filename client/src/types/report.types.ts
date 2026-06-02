// Shared Report types — API response shapes from /reports/.
// Architecture ref: frontend_architecture.md §3.3

export interface ReportSummary {
  id: string;
  patient_id: string;
  file_path: string;
  original_filename: string | null;
  mime_type: string | null;
  title: string | null;
  report_date: string | null;
  ocr_status: 'pending' | 'ready' | 'failed';
  created_at: string | null;
}

export interface ReportDetail extends ReportSummary {
  ocr_text: string | null;
  ocr_error: string | null;
}
