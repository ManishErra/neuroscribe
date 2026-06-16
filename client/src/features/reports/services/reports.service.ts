// Reports API service — backend reports router endpoints
// Architecture ref: frontend_architecture.md §2, §5.3, §14

import client from '@/api/axiosClient';

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

export interface ReportDetail {
  id: string;
  patient_id: string;
  file_path: string;
  original_filename: string | null;
  mime_type: string | null;
  title: string | null;
  report_date: string | null;
  ocr_status: 'pending' | 'ready' | 'failed';
  ocr_text: string | null;
  ocr_error: string | null;
  created_at: string | null;
}

export interface ReportOcrResponse {
  id: string;
  patient_id: string;
  file_path: string;
  mime_type: string | null;
  ocr_status: 'pending' | 'ready' | 'failed';
  ocr_error: string | null;
  text_preview: string;
  extracted_char_count: number;
}

/**
 * Fetch all reports for a specific patient.
 */
export async function fetchPatientReports(patientId: string): Promise<ReportSummary[]> {
  return client.get(`/reports/patient/${patientId}`);
}

/**
 * Fetch detailed report metadata and parsed OCR text.
 */
export async function fetchReportDetail(reportId: string): Promise<ReportDetail> {
  return client.get(`/reports/${reportId}`);
}

/**
 * Upload a dynamic report file (PDF, PNG, JPG, JPEG) to the backend.
 */
export async function uploadReport(patientId: string, file: File): Promise<ReportDetail> {
  const formData = new FormData();
  formData.append('patient_id', patientId);
  formData.append('file', file);

  return client.post('/reports/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
}

/**
 * Run OCR extraction and local SentenceTransformer embeddings indexing.
 */
export async function runOcr(reportId: string): Promise<ReportOcrResponse> {
  return client.post(`/reports/${reportId}/ocr`);
}

/**
 * Delete a report metadata and its associated file on disk.
 */
export async function deleteReport(reportId: string): Promise<void> {
  return client.delete(`/reports/${reportId}`);
}
