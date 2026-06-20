import { useParams } from 'react-router-dom';
import { usePatientOverview } from '@/features/insights/hooks/usePatientOverview';
import { usePatientInsights } from '@/features/insights/hooks/usePatientInsights';
import { usePatient } from '@/features/patients/hooks/usePatient';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { 
  User, Activity, CheckCircle2, TrendingDown, TrendingUp, AlertTriangle, HelpCircle
} from 'lucide-react';
import { useSettings } from '@/store/SettingsContext';
import { cn } from '@/lib/utils';

export default function OverviewTab() {
  const { patientId } = useParams<{ patientId: string }>();
  const { settings } = useSettings();
  const isCompact = settings.density === 'compact';

  const { data: patient, isLoading: isPatientLoading } = usePatient(patientId);
  const { data: overview, isLoading: isOverviewLoading, isError: isOverviewError } = usePatientOverview(patientId);
  const { data: insights, isLoading: isInsightsLoading, isError: isInsightsError } = usePatientInsights(patientId);

  const isLoading = isPatientLoading || isOverviewLoading || isInsightsLoading;

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
    <div className={cn('grid grid-cols-1 lg:grid-cols-3 select-none transition-all duration-200 animate-in fade-in', isCompact ? 'gap-4 pt-4' : 'gap-6 pt-6')}>
      
      {/* ── Left Column (2/3 width) ─────────────────────────────── */}
      <div className={cn('lg:col-span-2 flex flex-col', isCompact ? 'gap-4' : 'gap-6')}>
        
        {/* Card 1: Medical History / Patient Summary */}
        <Card className="bg-white border border-border shadow-sm rounded-xl overflow-hidden">
          <CardHeader className={cn('border-b border-border bg-[#f8f9fa] flex flex-row items-center justify-between', isCompact ? 'py-3 px-4' : 'py-4 px-6')}>
            <div className="flex items-center gap-2">
              <User className="h-4.5 w-4.5 text-[#003d9b]" />
              <CardTitle className="text-sm font-bold tracking-wide text-[#191c1d] uppercase">
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
              <p className="text-sm text-[#434652] leading-relaxed">
                {insights?.summary || `${patient?.name} is a ${patient?.age}-year-old ${patient?.gender.toLowerCase()} currently under observation. Detailed history awaits first clinical session transcription.`}
              </p>
            )}

            <div className={cn('grid grid-cols-1 md:grid-cols-2 border-t border-border', isCompact ? 'gap-4 pt-4' : 'gap-6 pt-6')}>
              <div className="flex flex-col gap-3">
                <span className="text-[10px] font-bold text-[#747783] uppercase tracking-widest">
                  Key Diagnostic Findings
                </span>
                {isLoading ? (
                  <Skeleton className="h-20 w-full" />
                ) : !insights?.findings || insights.findings.length === 0 ? (
                  <p className="text-xs text-[#747783] italic">No active findings available.</p>
                ) : (
                  <div className="flex flex-col gap-2">
                    {insights.findings.map((finding, idx) => (
                      <div key={idx} className="flex items-start gap-2.5 rounded-lg bg-[#f8f9fa] border border-border p-2.5">
                        {getLabStatusIcon(finding)}
                        <span className="text-xs font-semibold text-[#191c1d] leading-tight">
                          {finding}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex flex-col gap-3">
                <span className="text-[10px] font-bold text-[#747783] uppercase tracking-widest">
                  Clinical Recommendations
                </span>
                {isLoading ? (
                  <Skeleton className="h-20 w-full" />
                ) : !insights?.recommendations || insights.recommendations.length === 0 ? (
                  <p className="text-xs text-[#747783] italic">No recommendations available.</p>
                ) : (
                  <ul className="flex flex-col gap-2">
                    {insights.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2.5 rounded-lg bg-[#f8f9fa] border border-border p-2.5">
                        <span className="h-1.5 w-1.5 rounded-full bg-[#508a7b] shrink-0 mt-1.5" />
                        <span className="text-xs font-semibold text-[#191c1d] leading-tight">
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
        <Card className="bg-white border border-border shadow-sm rounded-xl overflow-hidden">
          <CardHeader className={cn('border-b border-border bg-[#f8f9fa]', isCompact ? 'py-3 px-4' : 'py-4 px-6')}>
            <div className="flex items-center gap-2">
              <Activity className="h-4.5 w-4.5 text-[#003d9b]" />
              <CardTitle className="text-sm font-bold tracking-wide text-[#191c1d] uppercase">
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
              <div className="p-8 text-center text-sm text-[#747783] italic">
                No laboratory parameters extracted from patient files.
              </div>
            ) : (
              <Table>
                <TableHeader className="bg-[#f8f9fa] border-b border-border">
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-[#747783]">Marker Name</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-[#747783]">Result Value</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-[#747783]">Reference</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-[#747783]">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Object.entries(overview.latest_labs).map(([key, val]) => {
                    const matchingFinding = insights?.findings?.find((f) => f.toLowerCase().startsWith(key.toLowerCase())) || '';
                    const rowClass = getLabRowStatusClass(matchingFinding);
                    return (
                      <TableRow key={key} className="border-b border-border hover:bg-[#f8f9fa]">
                        <TableCell className="text-xs font-bold text-[#191c1d] capitalize">{key === 'wbc' ? 'WBC Count' : key === 'rbc' ? 'RBC Count' : key}</TableCell>
                        <TableCell className={cn('text-xs font-bold', rowClass)}>{val as string}</TableCell>
                        <TableCell className="text-xs font-semibold text-[#747783]">{getTestRefRange(key)}</TableCell>
                        <TableCell className="text-xs font-bold">
                          {matchingFinding ? (
                            <div className="flex items-center gap-1.5">
                              {getLabStatusIcon(matchingFinding)}
                              <span className={cn('capitalize text-[11px]', rowClass)}>
                                {matchingFinding.includes('(') ? matchingFinding.slice(matchingFinding.indexOf('(') + 1, -1).toLowerCase() : 'normal'}
                              </span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1.5 text-[#747783]">
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
      <div className={cn('flex flex-col', isCompact ? 'gap-4' : 'gap-6')}>
        
        {/* Card 3: Patient Flags */}
        <Card className="bg-white border border-border shadow-sm rounded-xl overflow-hidden">
          <CardHeader className={cn('border-b border-border bg-[#f8f9fa]', isCompact ? 'py-3 px-4' : 'py-4 px-6')}>
            <CardTitle className="text-sm font-bold tracking-wide text-[#191c1d] uppercase">
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
              <div className="rounded-xl border border-dashed border-border bg-[#f8f9fa] text-center text-xs text-[#747783] p-6">
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
                        'px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider',
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

      </div>
    </div>
  );
}
