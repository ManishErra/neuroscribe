// OverviewTab — dynamic child sub-tab presenting patient case files, laboratory summaries, and flags.
// Architecture ref: frontend_architecture.md §4, §5.2, §8, §16.1

import { useParams } from 'react-router-dom';
import { usePatientOverview } from '@/features/insights/hooks/usePatientOverview';
import { usePatientInsights } from '@/features/insights/hooks/usePatientInsights';
import { usePatient } from '@/features/patients/hooks/usePatient';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { formatDate as displayDate } from '@/utils/formatters';
import { Brain, FileText, CheckCircle2, TrendingDown, TrendingUp, AlertTriangle, HelpCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function OverviewTab() {
  const { patientId } = useParams<{ patientId: string }>();

  // Parallel React Query fetches using cached state
  const { isLoading: isPatientLoading } = usePatient(patientId);
  const { data: overview, isLoading: isOverviewLoading, isError: isOverviewError } = usePatientOverview(patientId);
  const { data: insights, isLoading: isInsightsLoading, isError: isInsightsError } = usePatientInsights(patientId);

  const isLoading = isPatientLoading || isOverviewLoading || isInsightsLoading;

  if (isOverviewError || isInsightsError) {
    return (
      <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-6 text-center select-none shadow-sm">
        <AlertTriangle className="h-6 w-6 text-rose-400 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-rose-400 mb-1">Failed to load clinical overview</h3>
        <p className="text-xs text-muted-foreground">
          Make sure at least one laboratory report is uploaded and OCR processed successfully.
        </p>
      </div>
    );
  }

  // Parse lab test classifications from finding text
  const getLabStatusIcon = (findingText: string) => {
    const text = findingText.toUpperCase();
    if (text.includes('LOW')) {
      return <TrendingDown className="h-4 w-4 text-rose-400 shrink-0" />;
    }
    if (text.includes('HIGH') || text.includes('ELEVATED')) {
      return <TrendingUp className="h-4 w-4 text-rose-400 shrink-0" />;
    }
    return <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />;
  };

  const getLabRowStatusClass = (findingText: string) => {
    const text = findingText.toUpperCase();
    if (text.includes('LOW') || text.includes('HIGH') || text.includes('ELEVATED')) {
      return 'text-rose-400 font-semibold';
    }
    return 'text-foreground';
  };

  // Safe reference ranges
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
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 select-none">
      
      {/* ── Left Column (2/3 width) ─────────────────────────────── */}
      <div className="lg:col-span-2 flex flex-col gap-6">
        
        {/* Card 1: AI Insights */}
        <Card className="border border-white/[0.06] bg-slate-900/40 backdrop-blur-md shadow-lg rounded-2xl overflow-hidden relative">
          {/* Subtle logo vector watermark */}
          <div className="absolute -top-6 -right-6 w-24 h-24 bg-primary/5 rounded-full blur-2xl" />
          
          <CardHeader className="border-b border-white/[0.06] flex flex-row items-center justify-between py-4">
            <div className="flex items-center gap-2">
              <div className="h-7 w-7 rounded-lg bg-[#508a7b]/10 border border-[#508a7b]/20 flex items-center justify-center">
                <Brain className="h-4 w-4 text-[#508a7b]" />
              </div>
              <CardTitle className="text-sm font-bold tracking-wide text-foreground">
                NeuroScribe AI Insights
              </CardTitle>
            </div>
            
            {isLoading ? (
              <Skeleton className="h-5 w-24 rounded-full" />
            ) : (
              <Badge className="bg-[#508a7b]/10 text-[#508a7b] border border-[#508a7b]/20 hover:bg-[#508a7b]/20 text-[10px] py-0.5 rounded-full select-none">
                AI GENERATED
              </Badge>
            )}
          </CardHeader>

          <CardContent className="p-6 flex flex-col gap-6">
            
            {/* Clinical Summary Paragraph */}
            <div className="flex flex-col gap-2">
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                Clinical Summary
              </span>
              {isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-4 w-full animate-pulse" />
                  <Skeleton className="h-4 w-5/6 animate-pulse" />
                  <Skeleton className="h-4 w-4/5 animate-pulse" />
                </div>
              ) : (
                <p className="text-sm text-foreground/90 leading-relaxed font-medium">
                  {insights?.summary || 'No diagnostic summaries generated.'}
                </p>
              )}
            </div>

            {/* Findings & Recommendations Split */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-white/[0.04]">
              
              {/* Key Findings List */}
              <div className="flex flex-col gap-3">
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                  Key Findings
                </span>
                {isLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-3/4 animate-pulse" />
                    <Skeleton className="h-4 w-2/3 animate-pulse" />
                  </div>
                ) : !insights?.findings || insights.findings.length === 0 ? (
                  <p className="text-xs text-muted-foreground italic">No findings available.</p>
                ) : (
                  <div className="flex flex-col gap-2">
                    {insights.findings.map((finding, idx) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2.5 p-2 rounded-xl bg-white/[0.01] border border-white/[0.04]"
                      >
                        {getLabStatusIcon(finding)}
                        <span className="text-xs font-semibold text-foreground/90 leading-tight">
                          {finding}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Recommendations list */}
              <div className="flex flex-col gap-3">
                <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">
                  Recommendations
                </span>
                {isLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-4/5 animate-pulse" />
                    <Skeleton className="h-4 w-3/4 animate-pulse" />
                  </div>
                ) : !insights?.recommendations || insights.recommendations.length === 0 ? (
                  <p className="text-xs text-muted-foreground italic">No recommendations available.</p>
                ) : (
                  <ul className="flex flex-col gap-2">
                    {insights.recommendations.map((rec, idx) => (
                      <li
                        key={idx}
                        className="flex items-start gap-2.5 p-2 rounded-xl bg-white/[0.01] border border-white/[0.04]"
                      >
                        <span className="h-1.5 w-1.5 rounded-full bg-[#508a7b] shrink-0 mt-1.5 shadow-[0_0_6px_rgba(80,138,123,0.6)]" />
                        <span className="text-xs font-semibold text-foreground/90 leading-tight">
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
        <Card className="border border-white/[0.06] bg-slate-900/40 backdrop-blur-md shadow-lg rounded-2xl overflow-hidden">
          <CardHeader className="border-b border-white/[0.06] py-4">
            <CardTitle className="text-sm font-bold tracking-wide text-foreground">
              Latest Laboratory Results
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-6 space-y-3">
                <Skeleton className="h-8 w-full animate-pulse" />
                <Skeleton className="h-8 w-full animate-pulse" />
                <Skeleton className="h-8 w-full animate-pulse" />
              </div>
            ) : !overview?.latest_labs || Object.keys(overview.latest_labs).length === 0 ? (
              <div className="p-8 text-center text-xs text-muted-foreground italic select-none">
                No active laboratory parameters extracted from patient files.
              </div>
            ) : (
              <Table>
                <TableHeader className="bg-white/[0.02] border-b border-white/[0.06]">
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground py-3 h-auto select-none">
                      Marker Name
                    </TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground py-3 h-auto select-none">
                      Result Value
                    </TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground py-3 h-auto select-none">
                      Reference boundaries
                    </TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground py-3 h-auto select-none">
                      Interpretation Status
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className="border-none">
                  {Object.entries(overview.latest_labs).map(([key, val]) => {
                    // Match with findings to extract status description
                    const matchingFinding = insights?.findings?.find((f) =>
                      f.toLowerCase().startsWith(key.toLowerCase())
                    ) || '';
                    
                    const rowClass = getLabRowStatusClass(matchingFinding);
                    
                    return (
                      <TableRow
                        key={key}
                        className="border-b border-white/[0.04] hover:bg-white/[0.01]"
                      >
                        <TableCell className="text-xs font-bold text-foreground py-3.5 select-none capitalize">
                          {key === 'wbc' ? 'WBC Count' : key === 'rbc' ? 'RBC Count' : key}
                        </TableCell>
                        <TableCell className={cn('text-xs font-bold select-none', rowClass)}>
                          {val}
                        </TableCell>
                        <TableCell className="text-xs font-semibold text-muted-foreground select-none">
                          {getTestRefRange(key)}
                        </TableCell>
                        <TableCell className="text-xs font-bold select-none">
                          {matchingFinding ? (
                            <div className="flex items-center gap-1.5">
                              {getLabStatusIcon(matchingFinding)}
                              <span className={cn('capitalize text-[11px]', rowClass)}>
                                {matchingFinding.includes('(')
                                  ? matchingFinding.slice(matchingFinding.indexOf('(') + 1, -1).toLowerCase()
                                  : 'normal'}
                              </span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1.5 text-muted-foreground">
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
      <div className="flex flex-col gap-6">
        
        {/* Card 3: Patient Status & Flags */}
        <Card className="border border-white/[0.06] bg-slate-900/40 backdrop-blur-md shadow-lg rounded-2xl overflow-hidden select-none">
          <CardHeader className="border-b border-white/[0.06] py-4">
            <CardTitle className="text-sm font-bold tracking-wide text-foreground">
              Clinical Flags
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            {isLoading ? (
              <div className="flex flex-wrap gap-2">
                <Skeleton className="h-6 w-24 rounded-full" />
                <Skeleton className="h-6 w-32 rounded-full" />
              </div>
            ) : !overview?.clinical_flags || overview.clinical_flags.length === 0 ? (
              <div className="rounded-xl border border-dashed border-white/[0.08] bg-white/[0.01] p-6 text-center text-xs text-muted-foreground select-none">
                No active clinical alerts detected.
              </div>
            ) : (
              <div className="flex flex-wrap gap-2 select-none">
                {overview.clinical_flags.map((flag, idx) => {
                  const isNormal = flag.toLowerCase().includes('stable');
                  return (
                    <Badge
                      key={idx}
                      variant="outline"
                      className={cn(
                        'px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider select-none transition-colors border',
                        isNormal
                          ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
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

        {/* Card 4: Last Activity */}
        <Card className="border border-white/[0.06] bg-slate-900/40 backdrop-blur-md shadow-lg rounded-2xl overflow-hidden select-none">
          <CardHeader className="border-b border-white/[0.06] py-4">
            <CardTitle className="text-sm font-bold tracking-wide text-foreground">
              Last Diagnostic Activity
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 select-none">
            {isLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-4 w-1/3" />
                <Skeleton className="h-4 w-2/3" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            ) : !overview?.last_activity || !overview.last_activity.type ? (
              <div className="rounded-xl border border-dashed border-white/[0.08] bg-white/[0.01] p-6 text-center text-xs text-muted-foreground select-none">
                No recorded diagnostics yet.
              </div>
            ) : (
              <div className="rounded-2xl border border-white/[0.06] bg-white/[0.01] p-4 flex gap-4 select-none relative overflow-hidden">
                <div className="h-9 w-9 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shrink-0 select-none">
                  <FileText className="h-4 w-4" />
                </div>
                
                <div className="flex flex-col gap-1 select-none">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-[#508a7b] select-none">
                    {overview.last_activity.type.replace('_', ' ')}
                  </span>
                  
                  <span className="text-xs font-bold text-foreground select-none leading-normal">
                    Clinical Lab Report Processed Successfully
                  </span>

                  <div className="flex items-center flex-wrap gap-2 text-[10px] text-muted-foreground select-none mt-1">
                    <span>{displayDate(overview.last_activity.date)}</span>
                    <span className="text-white/[0.15]">·</span>
                    <span className="font-mono">ID: {overview.last_activity.id.slice(0, 8).toUpperCase()}</span>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

      </div>

    </div>
  );
}
