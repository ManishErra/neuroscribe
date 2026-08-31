import { useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { usePatientTimeline } from '@/features/insights/hooks/usePatientTimeline';
import { usePatientInsights } from '@/features/insights/hooks/usePatientInsights';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip 
} from 'recharts';
import { 
  TrendingUp, 
  TrendingDown, 
  CheckCircle2, 
  AlertTriangle, 
  Calendar,
  Sparkles,
  HelpCircle
} from 'lucide-react';
import { useSettings } from '@/store/SettingsContext';
import { cn } from '@/lib/utils';
import { formatDate } from '@/utils/formatters';

type BiomarkerKey = 'hemoglobin' | 'wbc' | 'platelets';

interface BiomarkerSpec {
  name: string;
  unit: string;
  refRange: string;
  minVal: number;
  maxVal: number;
}

const BIOMARKERS: Record<BiomarkerKey, BiomarkerSpec> = {
  hemoglobin: {
    name: 'Hemoglobin (Hb)',
    unit: 'g/dL',
    refRange: '13.5 - 17.5',
    minVal: 13.5,
    maxVal: 17.5,
  },
  wbc: {
    name: 'White Blood Cells (WBC)',
    unit: 'K/uL',
    refRange: '4.5 - 11.0',
    minVal: 4.5,
    maxVal: 11.0,
  },
  platelets: {
    name: 'Platelets (PLT)',
    unit: 'K/uL',
    refRange: '150 - 450',
    minVal: 150,
    maxVal: 450,
  },
};

export default function TrendsTab() {
  const { patientId } = useParams<{ patientId: string }>();
  const { settings } = useSettings();
  const isCompact = settings.density === 'compact';

  // Fetch real backend data streams
  const { data: timelineData, isLoading: isTimelineLoading, isError: isTimelineError } = usePatientTimeline(patientId);
  const { data: insightsData } = usePatientInsights(patientId);

  const [activeBiomarker, setActiveBiomarker] = useState<BiomarkerKey>('hemoglobin');
  const [timeRange, setTimeRange] = useState<'30' | '90' | '180'>('90');

  // Compute active biomarker data points dynamically from database OCR records
  const chartData = useMemo(() => {
    const history = timelineData?.timeline?.[activeBiomarker]?.history || [];
    const formatted = history
      .map(h => ({
        date: h.report_date || 'Unknown',
        value: h.numeric_value ?? 0,
        rawValue: h.value,
        status: h.status,
        unit: h.unit
      }))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    // Filter by date range selection
    if (timeRange === '30') {
      return formatted.slice(-2);
    }
    if (timeRange === '90') {
      return formatted.slice(-4);
    }
    return formatted;
  }, [timelineData, activeBiomarker, timeRange]);

  // Aggregate unique dates from all biomarkers histories to construct comparison grid
  const uniqueDates = useMemo(() => {
    const dates = new Set<string>();
    const timeline = timelineData?.timeline || {};
    Object.values(timeline).forEach((detail: any) => {
      detail.history.forEach((h: any) => {
        if (h.report_date) dates.add(h.report_date);
      });
    });
    return Array.from(dates).sort((a, b) => new Date(b).getTime() - new Date(a).getTime());
  }, [timelineData]);

  const activeSpec = BIOMARKERS[activeBiomarker];

  // Helper to determine status style classes
  const getStatusStyles = (status: string) => {
    const normalized = status.toUpperCase();
    if (normalized.includes('LOW') || normalized.includes('DECREASED')) {
      return { label: 'Low', color: 'text-rose-500 bg-rose-50 border-rose-100', icon: TrendingDown };
    }
    if (normalized.includes('HIGH') || normalized.includes('ELEVATED')) {
      return { label: 'High', color: 'text-amber-500 bg-amber-50 border-amber-100', icon: TrendingUp };
    }
    if (normalized.includes('NORMAL') || normalized.includes('STABLE')) {
      return { label: 'Normal', color: 'text-emerald-600 bg-emerald-50 border-emerald-100', icon: CheckCircle2 };
    }
    return { label: 'Normal', color: 'text-[#424843] bg-gray-50 border-gray-100', icon: CheckCircle2 };
  };

  const hasData = useMemo(() => {
    const timeline = timelineData?.timeline || {};
    return Object.values(timeline).some((detail: any) => detail.report_count > 0);
  }, [timelineData]);

  if (isTimelineLoading) {
    return <div className="p-6 text-center text-xs text-[#747783] select-none font-semibold">Loading trends dashboard...</div>;
  }

  if (isTimelineError || !hasData) {
    return (
      <div className="rounded-xl border border-dashed border-[#E2E8E4] bg-white text-center p-8 select-none shadow-sm mt-6 max-w-xl mx-auto">
        <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto mb-3" />
        <h3 className="text-sm font-bold text-[#1a1c1a] mb-1">No Trend Data Available</h3>
        <p className="text-xs text-[#747783] leading-relaxed max-w-sm mx-auto">
          Longitudinal biomarker trends are generated dynamically from parsed laboratory report values.
          Please upload and run OCR extraction on PDF reports to begin visual charting.
        </p>
      </div>
    );
  }

  return (
    <div className={cn('grid grid-cols-1 lg:grid-cols-3 gap-6', isCompact && 'gap-4')}>
      
      {/* ── LEFT/CENTER COLUMN: biomarker KPI cards and longitudinal charts ── */}
      <div className={cn('lg:col-span-2 flex flex-col gap-6', isCompact && 'gap-4')}>
        
        {/* Vitals Biomarker KPI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {(Object.keys(BIOMARKERS) as BiomarkerKey[]).map((key) => {
            const spec = BIOMARKERS[key];
            const detail = timelineData?.timeline?.[key];
            const val = detail?.latest_value || '—';
            const rawStatus = detail?.history?.[detail.history.length - 1]?.status || 'NORMAL';
            const stat = getStatusStyles(rawStatus);
            const StatIcon = stat.icon;
            const isSelected = activeBiomarker === key;

            return (
              <button
                key={key}
                type="button"
                onClick={() => setActiveBiomarker(key)}
                className={cn(
                  'bg-white border rounded-2xl p-4 text-left flex flex-col justify-between shadow-sm transition-all relative overflow-hidden group select-none outline-none',
                  isSelected 
                    ? 'border-[#466551] ring-2 ring-[#466551]/10' 
                    : 'border-[#E2E8E4] hover:bg-[#faf9f6]'
                )}
              >
                <div className="flex items-start justify-between w-full">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#424843]">
                    {spec.name.split(' ')[0]}
                  </span>
                  {detail && detail.report_count > 0 ? (
                    <span className={cn('px-2 py-0.5 rounded text-[9px] font-bold border capitalize shrink-0', stat.color)}>
                      {stat.label}
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-[9px] font-bold border capitalize bg-gray-50 border-gray-100 text-[#747783] shrink-0">
                      No Data
                    </span>
                  )}
                </div>

                <div className="mt-3.5 flex items-baseline gap-1">
                  <span className="text-xl font-bold text-[#1a1c1a]">{val}</span>
                  {detail && detail.report_count > 0 && (
                    <span className="text-[10px] font-medium text-[#424843]/70">{spec.unit}</span>
                  )}
                </div>

                <div className="mt-2.5 flex items-center justify-between text-[9px] text-[#424843]/60 border-t border-[#faf9f6] pt-2 w-full">
                  <span>Ref: {spec.refRange}</span>
                  {detail && detail.report_count > 0 ? (
                    <StatIcon className="h-3.5 w-3.5 shrink-0 opacity-80" />
                  ) : (
                    <HelpCircle className="h-3.5 w-3.5 shrink-0 opacity-40" />
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* Longitudinal Recharts Chart Area */}
        <Card className="bg-white border border-[#E2E8E4] shadow-sm rounded-2xl overflow-hidden">
          <CardHeader className={cn('border-b border-[#E2E8E4] bg-[#faf9f6] flex flex-row items-center justify-between flex-wrap gap-2', isCompact ? 'py-3 px-4' : 'py-4 px-6')}>
            <div className="flex items-center gap-2">
              <Calendar className="h-4.5 w-4.5 text-[#466551]" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#1a1c1a]">
                Longitudinal Biomarker Analysis
              </CardTitle>
            </div>
            {/* Time range selection controls */}
            <div className="flex items-center bg-[#eeeeeb] rounded-lg p-0.5 border border-[#c2c8c1] shrink-0">
              {[
                { label: '30D', value: '30' },
                { label: '90D', value: '90' },
                { label: '6M', value: '180' },
              ].map((btn) => (
                <button
                  key={btn.value}
                  type="button"
                  onClick={() => setTimeRange(btn.value as any)}
                  className={cn(
                    'px-2 py-1 text-[9px] font-bold rounded-md transition-all uppercase tracking-wider',
                    timeRange === btn.value
                      ? 'bg-white text-[#466551] shadow-sm'
                      : 'text-[#424843] hover:text-[#1a1c1a]'
                  )}
                >
                  {btn.label}
                </button>
              ))}
            </div>
          </CardHeader>
          <CardContent className="p-6">
            {chartData.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center text-xs text-[#747783] italic border border-dashed border-[#E2E8E4] rounded-xl bg-[#faf9f6]">
                No tracking timeline data points available for {activeSpec.name}.
              </div>
            ) : (
              <div className="h-64 w-full text-xs font-medium text-[#424843]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorSage" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
                        <stop offset="5%" stopColor="#466551" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#466551" stopOpacity={0.01} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e5" />
                    <XAxis 
                      dataKey="date" 
                      tickFormatter={(tick) => formatDate(tick).split(' ').slice(0, 2).join(' ')} 
                      stroke="#727972" 
                      tick={{ fontSize: 10 }}
                    />
                    <YAxis 
                      domain={['auto', 'auto']}
                      stroke="#727972" 
                      tick={{ fontSize: 10 }}
                    />
                    <Tooltip
                      labelFormatter={(label) => `Date: ${formatDate(label)}`}
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        border: '1px solid #E2E8E4',
                        borderRadius: '12px',
                        fontSize: '11px',
                        boxShadow: '0 4px 12px rgba(124, 157, 134, 0.08)',
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      name={activeSpec.name.split(' ')[0]}
                      stroke="#466551"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#colorSage)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Comparison Analysis Table */}
        <Card className="bg-white border border-[#E2E8E4] shadow-sm rounded-2xl overflow-hidden">
          <CardHeader className={cn('border-b border-[#E2E8E4] bg-[#faf9f6]', isCompact ? 'py-3 px-4' : 'py-4 px-6')}>
            <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#1a1c1a]">
              Historical Reference Mapping
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {uniqueDates.length === 0 ? (
              <div className="p-8 text-center text-xs text-[#747783] italic">
                No historical records mapped yet.
              </div>
            ) : (
              <Table>
                <TableHeader className="bg-[#faf9f6] border-b border-[#E2E8E4]">
                  <TableRow className="hover:bg-transparent">
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-[#424843] px-6">Report Date</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-[#424843] px-6">Hemoglobin ({BIOMARKERS.hemoglobin.unit})</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-[#424843] px-6">WBC Count ({BIOMARKERS.wbc.unit})</TableHead>
                    <TableHead className="text-[10px] font-bold uppercase tracking-widest text-[#424843] px-6">Platelets ({BIOMARKERS.platelets.unit})</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {uniqueDates.map((date) => {
                    const hb = timelineData?.timeline?.hemoglobin?.history.find((h: any) => h.report_date === date);
                    const wbc = timelineData?.timeline?.wbc?.history.find((h: any) => h.report_date === date);
                    const platelets = timelineData?.timeline?.platelets?.history.find((h: any) => h.report_date === date);

                    return (
                      <TableRow key={date} className="border-b border-[#E2E8E4] hover:bg-[#faf9f6]/50 h-12">
                        <TableCell className="text-xs font-bold text-[#1a1c1a] px-6">{formatDate(date)}</TableCell>
                        <TableCell className={cn(
                          'text-xs font-semibold px-6',
                          hb && getStatusStyles(hb.status).label !== 'Normal' && 'text-rose-500 font-bold'
                        )}>
                          {hb?.value || '—'}
                        </TableCell>
                        <TableCell className={cn(
                          'text-xs font-semibold px-6',
                          wbc && getStatusStyles(wbc.status).label !== 'Normal' && 'text-rose-500 font-bold'
                        )}>
                          {wbc?.value || '—'}
                        </TableCell>
                        <TableCell className={cn(
                          'text-xs font-semibold px-6',
                          platelets && getStatusStyles(platelets.status).label !== 'Normal' && 'text-rose-500 font-bold'
                        )}>
                          {platelets?.value || '—'}
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

      {/* ── RIGHT COLUMN: AI Clinical trend summary ── */}
      <div className={cn('flex flex-col gap-6', isCompact && 'gap-4')}>
        
        {/* AI Trend Summary panel */}
        <Card className="bg-white border border-[#E2E8E4] shadow-sm rounded-2xl overflow-hidden">
          <CardHeader className={cn('border-b border-[#E2E8E4] bg-[#faf9f6]', isCompact ? 'py-3 px-4' : 'py-4 px-6')}>
            <div className="flex items-center gap-2">
              <Sparkles className="h-4.5 w-4.5 text-[#466551]" />
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-[#1a1c1a]">
                AI Longitudinal Synthesis
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className={cn('flex flex-col gap-4', isCompact ? 'p-4' : 'p-6')}>
            <div className="flex flex-col border-b border-[#E2E8E4] pb-4 gap-1">
              <h3 className="text-xs font-bold text-[#1a1c1a]">Clinical Observations</h3>
              <p className="text-[10px] text-[#424843]/80">Extracted from Patient Diagnostic Insights</p>
            </div>
            
            <div className="flex flex-col gap-3">
              {insightsData?.findings && insightsData.findings.length > 0 ? (
                insightsData.findings.map((pt, idx) => (
                  <div key={idx} className="flex items-start gap-2.5 rounded-lg bg-[#faf9f6] border border-[#E2E8E4] p-3 shadow-[0_1px_2px_rgba(0,0,0,0.01)]">
                    <span className="h-1.5 w-1.5 rounded-full bg-[#466551] shrink-0 mt-1.5" />
                    <span className="text-xs font-semibold text-[#424843] leading-relaxed">
                      {pt}
                    </span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-[#747783] italic text-center py-6">
                  No diagnostic findings found. Please upload lab reports to run clinical synthesis.
                </div>
              )}
            </div>
          </CardContent>
        </Card>

      </div>

    </div>
  );
}
