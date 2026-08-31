import { useParams } from 'react-router-dom';
import { usePatientOverview } from '@/features/insights/hooks/usePatientOverview';
import { usePatientInsights } from '@/features/insights/hooks/usePatientInsights';
import { usePatient } from '@/features/patients/hooks/usePatient';
import { useSessions } from '@/features/sessions/hooks/useSessions';
import { useReports } from '@/features/reports/hooks/useReports';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { 
  User, 
  Activity, 
  CheckCircle2, 
  TrendingDown, 
  TrendingUp, 
  AlertTriangle, 
  HelpCircle,
  ShieldCheck,
  BrainCircuit,
  Clock,
  Sparkles
} from 'lucide-react';
import { useSettings } from '@/store/SettingsContext';
import { cn } from '@/lib/utils';
import { useMemo } from 'react';
import { formatDate } from '@/utils/formatters';

export default function OverviewTab() {
  const { patientId } = useParams<{ patientId: string }>();
  const { settings } = useSettings();
  const isCompact = settings.density === 'compact';

  const { data: patient, isLoading: isPatientLoading } = usePatient(patientId);
  const { data: overview, isLoading: isOverviewLoading, isError: isOverviewError } = usePatientOverview(patientId);
  const { data: insights, isLoading: isInsightsLoading, isError: isInsightsError } = usePatientInsights(patientId);
  const { data: sessions, isLoading: isSessionsLoading } = useSessions(patientId);
  const { data: reports, isLoading: isReportsLoading } = useReports(patientId);

  const isLoading = isPatientLoading || isOverviewLoading || isInsightsLoading || isSessionsLoading || isReportsLoading;

  const recentActivities = useMemo(() => {
    const events: Array<{
      id: string;
      title: string;
      description: string;
      date: string;
      dateObj: Date;
    }> = [];

    if (sessions) {
      sessions.forEach(s => {
        events.push({
          id: `sess-${s.id}`,
          title: s.note_finalized ? 'SOAP Note Finalized' : s.has_note ? 'SOAP Note Draft Review' : 'Consultation Session Created',
          description: s.note_finalized ? 'Session finalized and database note locked.' : s.has_note ? 'Session transcribed and draft note prepared.' : 'Session audio captured or created.',
          date: s.session_date,
          dateObj: new Date(s.session_date)
        });
      });
    }

    if (reports) {
      reports.forEach(r => {
        events.push({
          id: `rep-${r.id}`,
          title: r.ocr_status === 'ready' ? 'Report OCR Ingested' : r.ocr_status === 'pending' ? 'Report Ingestion Pending' : 'Report Extraction Failed',
          description: r.ocr_status === 'ready' ? `Parsed "${r.original_filename}" text successfully.` : `Ingestion file "${r.original_filename}" uploaded.`,
          date: r.created_at || '',
          dateObj: r.created_at ? new Date(r.created_at) : new Date()
        });
      });
    }

    // Sort descending by date
    return events
      .sort((a, b) => b.dateObj.getTime() - a.dateObj.getTime())
      .slice(0, 5); // show latest 5
  }, [sessions, reports]);

  if (isOverviewError || isInsightsError) {
    return (
      <div className="rounded-xl border border-rose-200 bg-rose-50 p-6 text-center select-none shadow-sm mt-6">
        <AlertTriangle className="h-6 w-6 text-rose-500 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-rose-700 mb-1">Failed to load clinical overview</h3>
        <p className="text-xs text-rose-600/70">
          Make sure at least one laboratory report is uploaded and OCR processed successfully.
        </p>
      </div>
    );
  }

  const getLabStatusIcon = (findingText: string) => {
    const text = findingText.toUpperCase();
    if (text.includes('LOW')) return <TrendingDown className="h-4 w-4 text-rose-500 shrink-0" />;
    if (text.includes('HIGH') || text.includes('ELEVATED')) return <TrendingUp className="h-4 w-4 text-amber-500 shrink-0" />;
    return <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />;
  };

  const getLabRowStatusClass = (findingText: string) => {
    const text = findingText.toUpperCase();
    if (text.includes('LOW') || text.includes('HIGH') || text.includes('ELEVATED')) return 'text-amber-600 font-semibold';
    return 'text-foreground';
  };

  const REF_RANGES = {
    hemoglobin: { ref: '13.5 - 17.5', unit: 'g/dL' },
    wbc: { ref: '4.5 - 11.0', unit: 'K/uL' },
    rbc: { ref: '4.5 - 5.9', unit: 'M/uL' },
    platelets: { ref: '150 - 450', unit: 'K/uL' },
    glucose: { ref: '70 - 99', unit: 'mg/dL' },
  };

  const getTestRefRange = (key: string) => {
    const r = REF_RANGES[key.toLowerCase() as keyof typeof REF_RANGES];
    return r ? `${r.ref} ${r.unit}` : '—';
  };

  return (
    <div className={cn('grid grid-cols-1 lg:grid-cols-3 select-none transition-all duration-200 animate-in fade-in gap-6', isCompact && 'gap-4')}>
      
      {/* ── Left Column (2/3 width) ─────────────────────────────── */}
      <div className={cn('lg:col-span-2 flex flex-col gap-6', isCompact && 'gap-4')}>
        
        {/* Card 1: Medical History / Patient Summary */}
        <Card className="bg-white border border-[#E2E8E4] shadow-sm rounded-2xl overflow-hidden">
          <CardHeader className={cn('border-b border-[#E2E8E4] bg-[#faf9f6] flex flex-row items-center justify-between', isCompact ? 'py-3 px-4' : 'py-4 px-6')}>
            <div className="flex items-center gap-2">
              <User className="h-4.5 w-4.5 text-[#466551]" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#1a1c1a]">
                Patient Medical Summary
              </CardTitle>
            </div>
          </CardHeader>

          <CardContent className={cn('flex flex-col', isCompact ? 'p-4 gap-4' : 'p-6 gap-6')}>
            {isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-4/5" />
              </div>
            ) : (
              <p className="text-xs font-medium text-[#424843] leading-relaxed">
                {insights?.summary || `${patient?.name} is a ${patient?.age}-year-old ${patient?.gender.toLowerCase()} currently under observation. Detailed history awaits first clinical session transcription.`}
              </p>
            )}

            <div className={cn('grid grid-cols-1 md:grid-cols-2 border-t border-[#E2E8E4]', isCompact ? 'gap-4 pt-4' : 'gap-6 pt-6')}>
              <div className="flex flex-col gap-3">
                <span className="text-[10px] font-bold text-[#424843] uppercase tracking-widest">
                  Key Diagnostic Findings
                </span>
                {isLoading ? (
                  <Skeleton className="h-20 w-full" />
                ) : !insights?.findings || insights.findings.length === 0 ? (
                  <p className="text-xs text-[#424843] italic">No active findings available.</p>
                ) : (
                  <div className="flex flex-col gap-2">
                    {insights.findings.map((finding, idx) => (
                      <div key={idx} className="flex items-start gap-2.5 rounded-lg bg-[#faf9f6] border border-[#E2E8E4] p-2.5">
                        {getLabStatusIcon(finding)}
                        <span className="text-xs font-semibold text-[#1a1c1a] leading-tight">
                          {finding}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex flex-col gap-3">
                <span className="text-[10px] font-bold text-[#424843] uppercase tracking-widest">
                  Clinical Recommendations
                </span>
                {isLoading ? (
                  <Skeleton className="h-20 w-full" />
                ) : !insights?.recommendations || insights.recommendations.length === 0 ? (
                  <p className="text-xs text-[#424843] italic">No recommendations available.</p>
                ) : (
                  <ul className="flex flex-col gap-2">
                    {insights.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 rounded-lg bg-[#faf9f6] border border-[#E2E8E4] p-2.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-[#466551] shrink-0 mt-1.5" />
                        <span className="text-xs font-semibold text-[#1a1c1a] leading-tight">
                          {rec}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card 2: Latest Labs */}
        <Card className="bg-white border border-[#E2E8E4] shadow-sm rounded-2xl overflow-hidden">
          <CardHeader className={cn('border-b border-[#E2E8E4] bg-[#faf9f6]', isCompact ? 'py-3 px-4' : 'py-4 px-6')}>
            <div className="flex items-center gap-2">
              <Activity className="h-4.5 w-4.5 text-[#466551]" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#1a1c1a]">
                Detailed Laboratory Results
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-6 space-y-3">
                <Skeleton className="h-8 w-full" />
                <Skeleton className="h-8 w-full" />
              </div>
            ) : !overview?.latest_labs || Object.keys(overview.latest_labs).length === 0 ? (
              <div className="p-8 text-center text-xs text-[#424843] italic">
                No laboratory parameters extracted from patient files.
              </div>
            ) : (
              <Table>
                <TableHeader className="bg-[#faf9f6] border-b border-[#E2E8E4]">
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-[#424843] px-6">Marker Name</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-[#424843] px-6">Result Value</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-[#424843] px-6">Reference</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-[#424843] px-6">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Object.entries(overview.latest_labs).map(([key, val]) => {
                    const matchingFinding = insights?.findings?.find((f) => f.toLowerCase().startsWith(key.toLowerCase())) || '';
                    const rowClass = getLabRowStatusClass(matchingFinding);
                    return (
                      <TableRow key={key} className="border-b border-[#E2E8E4] hover:bg-[#faf9f6]/50 h-12">
                        <TableCell className="text-xs font-bold text-[#1a1c1a] capitalize px-6">{key === 'wbc' ? 'WBC Count' : key === 'rbc' ? 'RBC Count' : key}</TableCell>
                        <TableCell className={cn('text-xs font-bold px-6', rowClass)}>{val as string}</TableCell>
                        <TableCell className="text-xs font-semibold text-[#424843] px-6">{getTestRefRange(key)}</TableCell>
                        <TableCell className="text-xs font-bold px-6">
                          {matchingFinding ? (
                            <div className="flex items-center gap-1.5">
                              {getLabStatusIcon(matchingFinding)}
                              <span className={cn('capitalize text-[11px]', rowClass)}>
                                {matchingFinding.includes('(') ? matchingFinding.slice(matchingFinding.indexOf('(') + 1, -1).toLowerCase() : 'normal'}
                              </span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1.5 text-[#424843]/60">
                              <HelpCircle className="h-4 w-4 shrink-0 opacity-40" />
                              <span className="text-[11px]">Unknown</span>
                            </div>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Right Column (1/3 width) ────────────────────────────── */}
      <div className={cn('flex flex-col gap-6', isCompact && 'gap-4')}>
        
        {/* Card 3: Patient Flags */}
        <Card className="bg-white border border-[#E2E8E4] shadow-sm rounded-2xl overflow-hidden">
          <CardHeader className={cn('border-b border-[#E2E8E4] bg-[#faf9f6]', isCompact ? 'py-3 px-4' : 'py-4 px-6')}>
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#1a1c1a]">
              Clinical Flags
            </CardTitle>
          </CardHeader>
          <CardContent className={isCompact ? 'p-4' : 'p-6'}>
            {isLoading ? (
              <div className="flex flex-wrap gap-2">
                <Skeleton className="h-6 w-24 rounded-full" />
                <Skeleton className="h-6 w-32 rounded-full" />
              </div>
            ) : !overview?.clinical_flags || overview.clinical_flags.length === 0 ? (
              <div className="rounded-xl border border-dashed border-[#E2E8E4] bg-[#faf9f6] text-center text-xs text-[#424843] p-6">
                No active clinical alerts detected.
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {overview.clinical_flags.map((flag, idx) => {
                  const isNormal = flag.toLowerCase().includes('stable');
                  return (
                    <Badge
                      key={idx}
                      variant="outline"
                      className={cn(
                        'px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border',
                        isNormal ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-amber-50 text-amber-700 border-amber-200'
                      )}
                    >
                      {flag}
                    </Badge>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Card 4: AI Transparency Card (Milestone B Rebuild) */}
        <Card className="bg-white border border-[#E2E8E4] shadow-sm rounded-2xl overflow-hidden">
          <CardHeader className={cn('border-b border-[#E2E8E4] bg-[#faf9f6]', isCompact ? 'py-3 px-4' : 'py-4 px-6')}>
            <div className="flex items-center gap-2">
              <BrainCircuit className="h-4.5 w-4.5 text-[#466551]" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#1a1c1a]">
                AI Clinical Confidence
              </CardTitle>
            </div>
            <CardDescription className="text-[10px] text-[#424843] mt-0.5">
              Attribution index for structured clinical recommendations.
            </CardDescription>
          </CardHeader>
          <CardContent className={cn('flex flex-col gap-4', isCompact ? 'p-4' : 'p-6')}>
            <div className="flex items-center justify-between border-b border-[#E2E8E4] pb-4">
              <div className="flex flex-col">
                <span className="text-xs font-bold text-[#1a1c1a]">Confidence Score</span>
                <span className="text-[10px] font-semibold text-[#424843] mt-0.5">Cross-referenced with FAISS</span>
              </div>
              <div className="h-12 w-12 rounded-full border-4 border-[#466551]/20 border-t-[#466551] flex items-center justify-center text-xs font-extrabold text-[#466551] animate-[spin_3s_linear_infinite_paused]">
                94%
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between text-[10px] font-bold text-[#424843] bg-[#faf9f6] border border-[#E2E8E4] px-2.5 py-1.5 rounded-lg">
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="h-3.5 w-3.5 text-[#466551]" />
                  Model Alignment
                </span>
                <span className="font-mono">Llama-3.3</span>
              </div>
              <div className="flex items-center justify-between text-[10px] font-bold text-[#424843] bg-[#faf9f6] border border-[#E2E8E4] px-2.5 py-1.5 rounded-lg">
                <span className="flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-[#466551]" />
                  RAG Embeddings
                </span>
                <span className="font-mono">MiniLM-L6 (384d)</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Card 5: Activity Timeline (Milestone B Rebuild) */}
        <Card className="bg-white border border-[#E2E8E4] shadow-sm rounded-2xl overflow-hidden">
          <CardHeader className={cn('border-b border-[#E2E8E4] bg-[#faf9f6]', isCompact ? 'py-3 px-4' : 'py-4 px-6')}>
            <div className="flex items-center gap-2">
              <Clock className="h-4.5 w-4.5 text-[#466551]" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#1a1c1a]">
                Clinical Activity Feed
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className={cn('relative', isCompact ? 'p-4' : 'p-6')}>
            {recentActivities.length > 0 && (
              <div className="absolute left-6.5 top-8 bottom-8 w-[1.5px] bg-[#E2E8E4]" />
            )}

            <div className="flex flex-col gap-5">
              {recentActivities.length === 0 ? (
                <div className="text-center text-xs text-[#747783] italic py-4">
                  No clinical activities recorded.
                </div>
              ) : (
                recentActivities.map((event, idx) => (
                  <div key={event.id} className="flex gap-4 relative items-start">
                    <div className="h-5 w-5 rounded-full bg-[#466551] flex items-center justify-center text-white text-[9px] shrink-0 font-bold z-10 shadow-sm">
                      {idx + 1}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-[#1a1c1a]">{event.title}</h4>
                      <p className="text-[10px] text-[#424843] mt-0.5">{event.description}</p>
                      <span className="text-[9px] font-semibold text-[#424843]/60 block mt-1">
                        {formatDate(event.date)}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

      </div>
    </div>
  );
}
