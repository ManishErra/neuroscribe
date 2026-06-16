// ReportsTab — dynamic workspace for laboratory and clinical diagnostic uploads
// Architecture ref: frontend_architecture.md §4, §5.4, §8, §16.1

import { useParams } from 'react-router-dom';
import { useState, useRef } from 'react';
import { useReports } from '@/features/reports/hooks/useReports';
import { useReport } from '@/features/reports/hooks/useReport';
import { useUploadReport } from '@/features/reports/hooks/useUploadReport';
import { useRunOcr } from '@/features/reports/hooks/useRunOcr';
import { useDeleteReport } from '@/features/reports/hooks/useDeleteReport';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import EmptyState from '@/components/common/EmptyState';
import { formatDate as displayDate } from '@/utils/formatters';
import { useSettings } from '@/store/SettingsContext';
import { 
  FileText, 
  UploadCloud, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Search, 
  Copy, 
  Download, 
  Sparkles, 
  Database,
  SearchCode,
  Trash2
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function ReportsTab() {
  const { patientId } = useParams<{ patientId: string }>();
  const { settings } = useSettings();
  const isCompact = settings.density === 'compact';
  
  // Queries
  const { data: reports, isLoading: isReportsLoading, isError: isReportsError } = useReports(patientId);
  
  // Local state for active detail view
  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);
  const { data: selectedReport, isLoading: isDetailLoading } = useReport(selectedReportId || undefined);
  
  // Local state for sub-tabs on detailed reports view
  const [detailTab, setDetailTab] = useState<'text' | 'labs' | 'pipeline'>('text');
  
  // Mutations
  const uploadReportMutation = useUploadReport(patientId);
  const runOcrMutation = useRunOcr(patientId);
  const deleteMutation = useDeleteReport(patientId);

  // File Ingestion Reference
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  // Helper trigger for click-to-pick uploads
  const triggerFileBrowser = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      uploadFile(file);
    }
  };

  // Drag and drop event handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      uploadFile(file);
    }
  };

  // Upload Core Function
  const uploadFile = (file: File) => {
    // Basic frontend validations
    const allowedExtensions = ['pdf', 'png', 'jpg', 'jpeg'];
    const fileExt = file.name.split('.').pop()?.toLowerCase();
    
    if (!fileExt || !allowedExtensions.includes(fileExt)) {
      alert('Unsupported file type. Please upload a PDF, PNG, JPEG, or JPG document.');
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      alert('File too large. Maximum supported document size is 50MB.');
      return;
    }

    uploadReportMutation.mutate({ file }, {
      onSuccess: (data) => {
        setSelectedReportId(data.id);
      }
    });
  };

  // Invoke backend OCR
  const handleRunOcr = (reportId: string) => {
    runOcrMutation.mutate({ reportId });
  };

  // Clipboard copy control
  const handleCopyText = () => {
    if (selectedReport?.ocr_text) {
      navigator.clipboard.writeText(selectedReport.ocr_text);
    }
  };

  // Static download link helper
  const handleDownload = () => {
    if (selectedReport?.file_path) {
      const base = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const absoluteUrl = `${base}/${selectedReport.file_path}`;
      window.open(absoluteUrl, '_blank');
    }
  };

  // Delete report helper
  const handleDelete = () => {
    if (selectedReportId && window.confirm('Are you sure you want to delete this report? This action cannot be undone.')) {
      deleteMutation.mutate({ reportId: selectedReportId }, {
        onSuccess: () => {
          setSelectedReportId(null);
        }
      });
    }
  };

  return (
    <div className={cn('grid grid-cols-1 xl:grid-cols-12 select-none animate-in fade-in duration-300 transition-all duration-200', isCompact ? 'gap-4' : 'gap-6')}>
      
      {/* ── Left Sidebar: Upload Ingest & History List ───────────── */}
      <div className={cn('xl:col-span-5 flex flex-col', isCompact ? 'gap-4' : 'gap-6')}>
        
        {/* Drag and Drop Ingest Zone */}
        <Card 
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "border border-dashed transition-all duration-200 cursor-pointer rounded-2xl relative overflow-hidden select-none",
            isDragOver 
              ? "border-[#508a7b] bg-[#508a7b]/5 shadow-lg shadow-[#508a7b]/5 scale-[1.01]" 
              : "border-white/[0.08] bg-slate-900/40 hover:border-white/[0.15] hover:bg-slate-900/60"
          )}
          onClick={triggerFileBrowser}
        >
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            className="hidden" 
            accept=".pdf,.png,.jpg,.jpeg"
          />
          <CardContent className={cn('flex flex-col items-center justify-center text-center transition-all duration-200', isCompact ? 'p-4 gap-2.5 min-h-[100px]' : 'p-6 gap-3 min-h-[140px]')}>
            <div className={cn(
              "h-10 w-10 rounded-xl flex items-center justify-center border transition-colors shrink-0",
              isDragOver 
                ? "bg-[#508a7b]/20 border-[#508a7b]/30 text-[#508a7b]" 
                : "bg-white/[0.02] border-white/[0.06] text-muted-foreground"
            )}>
              <UploadCloud className="h-5 w-5" />
            </div>
            
            <div className="flex flex-col gap-1">
              <span className="text-xs font-bold text-foreground">
                {uploadReportMutation.isPending ? 'Uploading Ingestion File...' : 'Upload Laboratory Document'}
              </span>
              <span className="text-[10px] text-muted-foreground max-w-[240px]">
                Drag and drop your file here, or click to browse. Supports PDF or Images up to 50MB.
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Diagnostic Reports Listing */}
        <Card className={cn('border border-white/[0.06] bg-slate-900/40 shadow-lg rounded-2xl flex-1 flex flex-col overflow-hidden transition-all duration-200', isCompact ? 'min-h-[260px]' : 'min-h-[360px]')}>
          <CardHeader className={cn('border-b border-white/[0.06]', isCompact ? 'py-2.5 px-4' : 'py-4 px-6')}>
            <CardTitle className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
              Clinical Report Archive
            </CardTitle>
          </CardHeader>
          <CardContent className={cn('p-0 flex-1 overflow-y-auto transition-all duration-200', isCompact ? 'max-h-[360px]' : 'max-h-[500px]')}>
            
            {isReportsLoading ? (
              <div className="p-4 space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex items-center gap-3 p-3 border border-white/[0.04] bg-white/[0.01] rounded-xl animate-pulse">
                    <Skeleton className="h-8 w-8 rounded-lg animate-pulse" />
                    <div className="flex-1 space-y-2">
                      <Skeleton className="h-4 w-2/3 animate-pulse" />
                      <Skeleton className="h-3 w-1/3 animate-pulse" />
                    </div>
                  </div>
                ))}
              </div>
            ) : isReportsError ? (
              <div className="p-6 text-center text-xs text-rose-400 font-semibold flex flex-col gap-2">
                <AlertTriangle className="h-5 w-5 mx-auto text-rose-400" />
                <span>Failed to load clinical report archive.</span>
              </div>
            ) : !reports || reports.length === 0 ? (
              <div className="py-12 select-none">
                <EmptyState
                  title="No reports uploaded yet"
                  description="Use the upload area above to ingest PDF laboratory tests, clinical notes, or pathology images."
                />
              </div>
            ) : (
              <div className="flex flex-col select-none">
                {reports.map((report) => {
                  const isSelected = selectedReportId === report.id;
                  
                  return (
                    <div
                      key={report.id}
                      onClick={() => setSelectedReportId(report.id)}
                      className={cn(
                        "group border-b border-white/[0.04] hover:bg-white/[0.02] cursor-pointer flex items-center justify-between gap-4 transition-all relative select-none",
                        isSelected && "bg-[#508a7b]/5 border-l-2 border-l-[#508a7b]",
                        isCompact ? "p-3" : "p-4"
                      )}
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <div className={cn(
                          "h-8 w-8 rounded-lg border flex items-center justify-center shrink-0 transition-colors",
                          isSelected 
                            ? "bg-[#508a7b]/10 border-[#508a7b]/20 text-[#508a7b]" 
                            : "bg-white/[0.02] border-white/[0.06] text-muted-foreground group-hover:text-foreground"
                        )}>
                          <FileText className="h-4 w-4" />
                        </div>
                        
                        <div className="flex flex-col gap-0.5 min-w-0">
                          <span className="text-xs font-bold text-foreground truncate group-hover:text-[#508a7b] transition-colors leading-tight">
                            {report.original_filename || 'diagnostic_report.pdf'}
                          </span>
                          <span className="text-[10px] text-muted-foreground">
                            {displayDate(report.created_at || '')}
                          </span>
                        </div>
                      </div>

                      {/* Status Badges */}
                      <div className="shrink-0">
                        {report.ocr_status === 'ready' ? (
                          <Badge variant="outline" className="px-2 py-0.5 rounded-full text-[9px] font-bold border-emerald-500/20 bg-emerald-500/10 text-emerald-400 select-none flex items-center gap-1">
                            <CheckCircle2 className="h-2.5 w-2.5" />
                            Ready
                          </Badge>
                        ) : report.ocr_status === 'pending' ? (
                          <Badge variant="outline" className="px-2 py-0.5 rounded-full text-[9px] font-bold border-amber-500/20 bg-amber-500/10 text-amber-400 select-none flex items-center gap-1">
                            <AlertTriangle className="h-2.5 w-2.5 animate-pulse" />
                            Awaiting OCR
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="px-2 py-0.5 rounded-full text-[9px] font-bold border-rose-500/20 bg-rose-500/10 text-rose-400 select-none flex items-center gap-1">
                            <XCircle className="h-2.5 w-2.5" />
                            Failed
                          </Badge>
                        )}
                      </div>

                    </div>
                  );
                })}
              </div>
            )}

          </CardContent>
        </Card>

      </div>

      {/* ── Right Workspace Column: Details Panel ───────────────── */}
      <div className={cn('xl:col-span-7 flex flex-col', isCompact ? 'gap-4' : 'gap-6')}>
        
        {!selectedReportId ? (
          <Card className={cn('border border-white/[0.06] bg-slate-900/40 rounded-2xl select-none flex flex-col items-center justify-center text-center flex-1 relative overflow-hidden transition-all duration-200', isCompact ? 'p-6 min-h-[360px]' : 'p-8 min-h-[500px]')}>
            <div className="absolute top-0 right-0 w-32 h-32 bg-[#508a7b]/5 rounded-full blur-3xl pointer-events-none" />
            <div className="h-12 w-12 rounded-2xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-center text-muted-foreground/40 mb-4 shrink-0">
              <Search className="h-6 w-6" />
            </div>
            <h3 className="text-sm font-bold text-foreground mb-1 select-none">No Report Selected</h3>
            <p className="text-xs text-muted-foreground max-w-xs leading-relaxed select-none">
              Select a diagnostic report from the history list to view OCR parsed contents and clinical embedding pipelines.
            </p>
          </Card>
        ) : (
          <Card className={cn('border border-white/[0.06] bg-slate-900/40 shadow-lg rounded-2xl overflow-hidden flex-1 flex flex-col transition-all duration-200', isCompact ? 'min-h-[360px]' : 'min-h-[500px]')}>
            
            {isDetailLoading ? (
              <div className={cn('space-y-6 flex-1 select-none', isCompact ? 'p-4' : 'p-6')}>
                <div className="flex items-center justify-between gap-4">
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-5 w-1/3 animate-pulse" />
                    <Skeleton className="h-4 w-1/4 animate-pulse" />
                  </div>
                  <Skeleton className="h-8 w-24 rounded-xl animate-pulse" />
                </div>
                <Skeleton className="h-10 w-full rounded-xl animate-pulse" />
                <Skeleton className="h-64 w-full rounded-2xl animate-pulse" />
              </div>
            ) : (
              <div className="flex flex-col flex-1 select-none animate-in fade-in duration-200">
                
                {/* Detailed Header Block */}
                <div className={cn('border-b border-white/[0.06] flex flex-col md:flex-row md:items-center justify-between select-none', isCompact ? 'p-4 gap-3' : 'p-6 gap-4')}>
                  
                  <div className="flex flex-col gap-1 min-w-0">
                    <div className="flex items-center flex-wrap gap-2.5">
                      <h2 className="text-sm font-bold text-foreground truncate max-w-[280px]">
                        {selectedReport?.original_filename || 'diagnostic_report.pdf'}
                      </h2>
                      {selectedReport?.ocr_status === 'ready' ? (
                        <Badge className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[9px] rounded-full flex items-center gap-1 select-none">
                          <CheckCircle2 className="h-2.5 w-2.5" />
                          Ready
                        </Badge>
                      ) : selectedReport?.ocr_status === 'pending' ? (
                        <Badge className="bg-amber-500/10 text-amber-400 border border-amber-500/20 text-[9px] rounded-full flex items-center gap-1 select-none">
                          <AlertTriangle className="h-2.5 w-2.5 animate-pulse" />
                          Awaiting OCR
                        </Badge>
                      ) : (
                        <Badge className="bg-rose-500/10 text-rose-400 border border-rose-500/20 text-[9px] rounded-full flex items-center gap-1 select-none">
                          <XCircle className="h-2.5 w-2.5" />
                          Failed
                        </Badge>
                      )}
                    </div>
                    <span className="text-[10px] text-muted-foreground">
                      Uploaded on {displayDate(selectedReport?.created_at || '')}
                    </span>
                  </div>

                  {/* Header Actions */}
                  <div className="flex items-center gap-2 select-none">
                    
                    {/* PDF Document Download Button */}
                    <button
                      type="button"
                      onClick={handleDownload}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[10px] font-bold bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] active:scale-[0.98] text-foreground transition-all shrink-0 select-none"
                    >
                      <Download className="h-3.5 w-3.5" />
                      Open Original Document
                    </button>

                    {/* Delete Report Button */}
                    <button
                      type="button"
                      onClick={handleDelete}
                      disabled={deleteMutation.isPending}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[10px] font-bold bg-rose-950/30 hover:bg-rose-900/40 text-rose-400 border border-rose-500/20 active:scale-[0.98] transition-all disabled:opacity-50 shrink-0 select-none"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      {deleteMutation.isPending ? 'Deleting...' : 'Delete Report'}
                    </button>

                    {/* Run OCR Processing sage green button */}
                    {(selectedReport?.ocr_status === 'pending' || selectedReport?.ocr_status === 'failed') && (
                      <button
                        type="button"
                        onClick={() => handleRunOcr(selectedReport.id)}
                        disabled={runOcrMutation.isPending}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[10px] font-bold bg-[#508a7b] hover:bg-[#437568] active:bg-[#396358] text-white shadow-md active:scale-[0.98] transition-all disabled:opacity-50 shrink-0 select-none"
                      >
                        <Sparkles className="h-3.5 w-3.5 fill-current animate-pulse" />
                        {runOcrMutation.isPending ? 'Processing...' : 'Run OCR Ingestion'}
                      </button>
                    )}
                  </div>

                </div>

                {/* Sub-Tabs selector */}
                <div className={cn('border-b border-white/[0.06] bg-white/[0.01] select-none flex items-center', isCompact ? 'px-4 py-2 gap-1.5' : 'px-6 py-3 gap-2')}>
                  <button
                    type="button"
                    onClick={() => setDetailTab('text')}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all select-none",
                      detailTab === 'text' 
                        ? "bg-[#508a7b]/10 text-[#508a7b] border border-[#508a7b]/20" 
                        : "text-muted-foreground hover:text-foreground hover:bg-white/[0.02]"
                    )}
                  >
                    Parsed Text
                  </button>
                  <button
                    type="button"
                    onClick={() => setDetailTab('labs')}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all select-none",
                      detailTab === 'labs' 
                        ? "bg-[#508a7b]/10 text-[#508a7b] border border-[#508a7b]/20" 
                        : "text-muted-foreground hover:text-foreground hover:bg-white/[0.02]"
                    )}
                  >
                    Extracted Lab Values
                  </button>
                  <button
                    type="button"
                    onClick={() => setDetailTab('pipeline')}
                    className={cn(
                      "px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all select-none",
                      detailTab === 'pipeline' 
                        ? "bg-[#508a7b]/10 text-[#508a7b] border border-[#508a7b]/20" 
                        : "text-muted-foreground hover:text-foreground hover:bg-white/[0.02]"
                    )}
                  >
                    Pipeline Status
                  </button>
                </div>

                {/* Main Workspace Body */}
                <div className={cn('flex-1 flex flex-col justify-between select-none', isCompact ? 'p-4' : 'p-6')}>
                  
                  {/* Tab 1: Monospace Parsed text */}
                  {detailTab === 'text' && (
                    <div className={cn('flex-1 flex flex-col animate-in fade-in duration-200', isCompact ? 'gap-3' : 'gap-4')}>
                      
                      <div className="flex items-center justify-between gap-4">
                        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                          OCR parsed document logs
                        </span>
                        
                        {selectedReport?.ocr_text && (
                          <button
                            type="button"
                            onClick={handleCopyText}
                            className="inline-flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-white/[0.04] text-[10px] font-bold text-muted-foreground hover:text-foreground transition-all select-none"
                          >
                            <Copy className="h-3.5 w-3.5" />
                            Copy Log
                          </button>
                        )}
                      </div>

                      <div className={cn('flex-1 overflow-y-auto rounded-2xl border border-white/[0.04] bg-black/10 p-4 relative select-text leading-relaxed transition-all duration-200', isCompact ? 'min-h-[200px] max-h-[340px]' : 'min-h-[300px] max-h-[460px]')}>
                        {selectedReport?.ocr_status === 'pending' ? (
                          <div className="absolute inset-0 flex flex-col items-center justify-center text-xs text-muted-foreground italic text-center p-6 select-none">
                            OCR text data has not been extracted yet. Click "Run OCR Ingestion" in the header to process.
                          </div>
                        ) : selectedReport?.ocr_status === 'failed' ? (
                          <div className="absolute inset-0 flex flex-col items-center justify-center p-6 select-none">
                            <XCircle className="h-8 w-8 text-rose-400 mb-2 shrink-0 animate-bounce" />
                            <span className="text-xs text-rose-400 font-bold mb-1 select-none">Ingestion Extraction Failed</span>
                            <p className="text-[10px] text-muted-foreground max-w-sm text-center leading-relaxed select-none">
                              {selectedReport?.ocr_error || 'An unexpected analytical error occurred during Textract document extraction.'}
                            </p>
                          </div>
                        ) : !selectedReport?.ocr_text ? (
                          <div className="absolute inset-0 flex flex-col items-center justify-center text-xs text-muted-foreground italic text-center p-6 select-none">
                            Document processed successfully but returned empty parsed text strings.
                          </div>
                        ) : (
                          <p className="text-xs font-mono text-foreground/90 leading-relaxed whitespace-pre-wrap select-text">
                            {selectedReport.ocr_text}
                          </p>
                        )}
                      </div>

                    </div>
                  )}

                  {/* Tab 2: Premium Extracted Lab values custom placeholder card */}
                  {detailTab === 'labs' && (
                    <div className="flex-1 flex flex-col justify-center animate-in fade-in duration-200">
                      
                      <Card className={cn('border border-white/[0.06] bg-slate-900/60 rounded-2xl select-none max-w-lg mx-auto w-full relative overflow-hidden shadow-lg', isCompact ? 'p-4' : 'p-6')}>
                        <div className="absolute top-0 right-0 w-24 h-24 bg-[#508a7b]/5 rounded-full blur-2xl pointer-events-none" />
                        
                        <CardHeader className="p-0 mb-4 pb-4 border-b border-white/[0.04] flex flex-row items-center gap-3 select-none">
                          <div className="h-8 w-8 rounded-xl bg-[#508a7b]/10 border border-[#508a7b]/20 flex items-center justify-center text-[#508a7b] shrink-0">
                            <SearchCode className="h-4 w-4" />
                          </div>
                          <div>
                            <CardTitle className="text-xs font-bold uppercase tracking-widest text-[#508a7b]">
                              Acoustic Analytical Pipeline
                            </CardTitle>
                            <span className="text-[9px] text-muted-foreground font-semibold">
                              OCR Preservation Architecture
                            </span>
                          </div>
                        </CardHeader>
                        
                        <CardContent className="p-0 flex flex-col gap-4 text-xs select-none">
                          <div className="flex flex-col gap-1.5 leading-relaxed font-semibold text-foreground/90">
                            <p className="flex items-start gap-2">
                              <span className="text-[#508a7b] shrink-0 mt-0.5">·</span>
                              <span>Structured laboratory parameter tables are not currently isolated for individual reports inside the database schema.</span>
                            </p>
                            <p className="flex items-start gap-2">
                              <span className="text-[#508a7b] shrink-0 mt-0.5">·</span>
                              <span>The full raw OCR text has been safely preserved and mapped to the patient timeline records.</span>
                            </p>
                            <p className="flex items-start gap-2">
                              <span className="text-[#508a7b] shrink-0 mt-0.5">·</span>
                              <span>The document is fully indexed in the FAISS vector database to support advanced multi-patient semantic searches and grounded RAG clinical Q&A interactions.</span>
                            </p>
                          </div>
                          
                          <div className="border border-[#508a7b]/10 bg-[#508a7b]/5 rounded-xl px-4 py-3 flex items-center gap-3 select-none mt-2">
                            <Database className="h-4 w-4 text-[#508a7b] shrink-0" />
                            <span className="text-[10px] text-muted-foreground max-w-sm leading-relaxed">
                              This clinical decision protects logical modularity, ensuring all RAG search engines pull directly from the original verified source logs.
                            </span>
                          </div>
                        </CardContent>
                      </Card>

                    </div>
                  )}

                  {/* Tab 3: OCR Pipeline Timeline */}
                  {detailTab === 'pipeline' && (
                    <div className="flex-1 flex flex-col justify-center animate-in fade-in duration-200 max-w-lg mx-auto w-full select-none">
                      
                      <div className="flex flex-col gap-6 relative select-none pl-6 border-l border-white/[0.06]">
                        
                        {/* Step 1: Upload */}
                        <div className="relative select-none flex flex-col gap-1">
                          <div className="absolute -left-[31px] top-0 h-4 w-4 rounded-full border border-emerald-500/20 bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                            <CheckCircle2 className="h-3 w-3 shrink-0" />
                          </div>
                          <span className="text-xs font-bold text-foreground">1. File Ingest & Metadata Persistence</span>
                          <span className="text-[10px] text-muted-foreground leading-relaxed">
                            Original file parsed, renamed securely, and saved to file system disk alongside DB metadata index entries.
                          </span>
                        </div>

                        {/* Step 2: OCR */}
                        <div className="relative select-none flex flex-col gap-1">
                          <div className={cn(
                            "absolute -left-[31px] top-0 h-4 w-4 rounded-full flex items-center justify-center",
                            selectedReport?.ocr_status === 'ready'
                              ? "border border-emerald-500/20 bg-emerald-500/20 text-emerald-400"
                              : selectedReport?.ocr_status === 'failed'
                              ? "border border-rose-500/20 bg-rose-500/20 text-rose-400"
                              : "border border-amber-500/20 bg-amber-500/20 text-amber-400"
                          )}>
                            {selectedReport?.ocr_status === 'ready' ? (
                              <CheckCircle2 className="h-3 w-3 shrink-0" />
                            ) : selectedReport?.ocr_status === 'failed' ? (
                              <XCircle className="h-3 w-3 shrink-0" />
                            ) : (
                              <div className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-ping" />
                            )}
                          </div>
                          <span className="text-xs font-bold text-foreground">2. Document OCR Parsing Pipeline</span>
                          <span className="text-[10px] text-muted-foreground leading-relaxed">
                            Textract engine parses PDF/Image layers to clean text block arrays, capturing physiological values.
                          </span>
                        </div>

                        {/* Step 3: Vector Embedding */}
                        <div className="relative select-none flex flex-col gap-1">
                          <div className={cn(
                            "absolute -left-[31px] top-0 h-4 w-4 rounded-full flex items-center justify-center",
                            selectedReport?.ocr_status === 'ready'
                              ? "border border-emerald-500/20 bg-emerald-500/20 text-emerald-400"
                              : "border border-white/10 bg-white/[0.04] text-muted-foreground"
                          )}>
                            {selectedReport?.ocr_status === 'ready' ? (
                              <CheckCircle2 className="h-3 w-3 shrink-0" />
                            ) : (
                              <div className="h-1.5 w-1.5 rounded-full bg-muted-foreground/30" />
                            )}
                          </div>
                          <span className="text-xs font-bold text-foreground">3. Vector Search Indexing</span>
                          <span className="text-[10px] text-muted-foreground leading-relaxed">
                            SentenceTransformer model maps text to 384-dimensional cosine similarity vectors persisted inside FAISS search indices.
                          </span>
                        </div>

                      </div>

                    </div>
                  )}

                </div>

              </div>
            )}

          </Card>
        )}

      </div>

    </div>
  );
}
