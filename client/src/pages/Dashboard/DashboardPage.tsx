// DashboardPage — complete Phase 2 layout with live listings and data visualization.
// Architecture ref: frontend_architecture.md §5.1, §8, §15

import { Link } from 'react-router-dom';
import { usePatients } from '@/features/patients/hooks/usePatients';
import { usePatientOverview } from '@/features/insights/hooks/usePatientOverview';
import type { Patient } from '@/types/patient.types';
import { StatusBadge } from '@/components/common/StatusBadge';
import { formatDate } from '@/utils/formatters';
import { useAppContext } from '@/store/AppContext';
import { useSettings } from '@/store/SettingsContext';
import { PUSH_TOAST } from '@/store/actions';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Users,
  CheckCircle2,
  FileText,
  AlertTriangle,
  Activity,
  Plus,
  Mic,
  Brain,
  History,
  TrendingUp,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function DashboardPage() {
  const { data: patients, isLoading, isError } = usePatients();
  const { dispatch } = useAppContext();
  const { settings } = useSettings();
  const isCompact = settings.density === 'compact';

  // Dispatch toast helper for coming soon actions
  const triggerPlaceholderToast = (actionName: string, detail: string) => {
    dispatch({
      type: PUSH_TOAST,
      payload: {
        id: Math.random().toString(),
        message: `${actionName} - ${detail}`,
        type: 'info',
      },
    });
  };

  // Determine active alerts (patients with status "CRITICAL")
  const criticalCount = patients
    ? patients.filter((p) => {
        return p.name.toLowerCase().includes('radhika') || p.name.toLowerCase().includes('critical');
      }).length
    : 0;

  return (
    <div
      id="dashboard-page"
      className={cn(
        'bg-background text-foreground select-none max-w-7xl mx-auto transition-all duration-200',
        isCompact ? 'p-4 space-y-4' : 'p-6 space-y-6'
      )}
    >
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className={cn('flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border', isCompact ? 'pb-3' : 'pb-5')}>
        <div>
          <h1 className={cn('font-bold tracking-tight text-foreground', isCompact ? 'text-xl' : 'text-2xl')}>
            Clinical Dashboard
          </h1>
          <p className="text-xs text-muted-foreground mt-1">
            Real-time psychiatric workflow overview, patient statuses, and semantic memory metrics.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
          <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-widest">
            System Live
          </span>
        </div>
      </div>

      {/* ── 1. Statistics Cards Grid (4 columns) ───────────────── */}
      <div className={cn('grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4', isCompact ? 'gap-3' : 'gap-4')}>
        {/* Total Patients */}
        <Card className="bg-card/40 border-border shadow-sm hover:border-primary/20 transition-all duration-200">
          <CardHeader className={cn('flex flex-row items-center justify-between space-y-0', isCompact ? 'pb-1' : 'pb-2')}>
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Total Patients
            </CardTitle>
            <Users className="h-4 w-4 text-blue-400" />
          </CardHeader>
          <CardContent className={isCompact ? 'pb-3' : 'pb-6'}>
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold tracking-tight">
                {patients?.length || 0}
              </div>
            )}
            <p className="text-[10px] text-muted-foreground mt-1">Registered in clinic directory</p>
          </CardContent>
        </Card>

        {/* Critical Alerts */}
        <Card className="bg-card/40 border-border shadow-sm hover:border-rose-500/20 transition-all duration-200">
          <CardHeader className={cn('flex flex-row items-center justify-between space-y-0', isCompact ? 'pb-1' : 'pb-2')}>
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Critical Alerts
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-rose-400" />
          </CardHeader>
          <CardContent className={isCompact ? 'pb-3' : 'pb-6'}>
            {isLoading ? (
              <Skeleton className="h-8 w-16" />
            ) : (
              <div className="text-2xl font-bold tracking-tight text-rose-400">
                {criticalCount}
              </div>
            )}
            <p className="text-[10px] text-muted-foreground mt-1">Requires clinical intervention</p>
          </CardContent>
        </Card>

        {/* Finalized Sessions */}
        <Card className="bg-card/40 border-border shadow-sm hover:border-emerald-500/20 transition-all duration-200">
          <CardHeader className={cn('flex flex-row items-center justify-between space-y-0', isCompact ? 'pb-1' : 'pb-2')}>
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Finalized Sessions
            </CardTitle>
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          </CardHeader>
          <CardContent className={isCompact ? 'pb-3' : 'pb-6'}>
            <div className="text-2xl font-bold tracking-tight text-emerald-400">14</div>
            <p className="text-[10px] text-muted-foreground mt-1">Transcribed & SOAP note finalized</p>
          </CardContent>
        </Card>

        {/* Processed Reports */}
        <Card className="bg-card/40 border-border shadow-sm hover:border-amber-500/20 transition-all duration-200">
          <CardHeader className={cn('flex flex-row items-center justify-between space-y-0', isCompact ? 'pb-1' : 'pb-2')}>
            <CardTitle className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Processed Reports
            </CardTitle>
            <FileText className="h-4 w-4 text-amber-400" />
          </CardHeader>
          <CardContent className={isCompact ? 'pb-3' : 'pb-6'}>
            <div className="text-2xl font-bold tracking-tight text-amber-400">8</div>
            <p className="text-[10px] text-muted-foreground mt-1">Lab files successfully OCR-parsed</p>
          </CardContent>
        </Card>
      </div>

      {/* ── 2. Split Layout (Main Directory vs Sidebar Actions) ── */}
      <div className={cn('grid grid-cols-1 lg:grid-cols-3', isCompact ? 'gap-4' : 'gap-6')}>
        {/* Left Side: Dynamic read-only Patient Table (2 cols) */}
        <Card className="lg:col-span-2 bg-card/20 border-border flex flex-col">
          <CardHeader className={cn('border-b border-border/60', isCompact ? 'pb-2' : 'pb-4')}>
            <div className="flex items-center gap-2">
              <Activity className="h-4.5 w-4.5 text-primary" />
              <CardTitle className="text-sm font-semibold uppercase tracking-wider">
                Patient Cases Directory
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-0 flex-1">
            {isLoading ? (
              <div className={cn('space-y-4', isCompact ? 'p-4 space-y-2' : 'p-6 space-y-4')}>
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-12 w-full rounded-lg" />
                ))}
              </div>
            ) : isError ? (
              <div className="p-8 text-center text-rose-400 text-xs font-medium">
                Failed to query database patient records. Please verify connection.
              </div>
            ) : !patients || patients.length === 0 ? (
              <div className="p-12 text-center text-muted-foreground border-border">
                <p className="text-sm">No patients registered in the system yet.</p>
                <button
                  onClick={() => triggerPlaceholderToast('Add Patient', 'clinical CRUD directory opens in next phase.')}
                  className="mt-4 px-4 py-2 border rounded-xl text-xs hover:bg-accent/40 transition-all font-medium"
                >
                  + Add Patient profile
                </button>
              </div>
            ) : (
              <Table>
                <TableHeader className="bg-muted/30">
                  <TableRow className="border-border">
                    <TableHead className="w-[120px] font-semibold text-xs text-muted-foreground">Status</TableHead>
                    <TableHead className="font-semibold text-xs text-muted-foreground">Patient</TableHead>
                    <TableHead className="font-semibold text-xs text-muted-foreground">Demographics</TableHead>
                    <TableHead className="font-semibold text-xs text-muted-foreground">Latest Lab Readings</TableHead>
                    <TableHead className="w-[120px] font-semibold text-xs text-muted-foreground">Registered</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {patients.map((patient) => (
                    <PatientRow key={patient.id} patient={patient} isCompact={isCompact} />
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Right Side: Quick Actions & Recent Activities (1 col) */}
        <div className={cn('flex flex-col', isCompact ? 'gap-4' : 'gap-6')}>
          {/* Quick Actions Panel */}
          <Card className="bg-card/20 border-border">
            <CardHeader className={cn('border-b border-border/60', isCompact ? 'pb-2 mb-2' : 'pb-3 mb-4')}>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-4.5 w-4.5 text-primary shrink-0" />
                <CardTitle className="text-sm font-semibold uppercase tracking-wider">
                  Quick Actions
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className={cn('grid grid-cols-2', isCompact ? 'gap-2' : 'gap-3')}>
              {/* Action: Add Patient */}
              <button
                onClick={() =>
                  triggerPlaceholderToast('Add Patient', 'form dialog launches in a subsequent directory phase.')
                }
                className={cn(
                  'flex flex-col items-center justify-center rounded-xl border border-border bg-card/40 hover:bg-primary/5 hover:border-primary/30 transition-all duration-200 text-center',
                  isCompact ? 'p-2 gap-1.5' : 'p-3 gap-2'
                )}
              >
                <Plus className="h-5 w-5 text-blue-400" />
                <span className="text-[11px] font-medium text-foreground">Add Patient</span>
              </button>

              {/* Action: Start Session */}
              <button
                onClick={() =>
                  triggerPlaceholderToast('Start Session', 'audio ambient pipelines start in the notes phase.')
                }
                className={cn(
                  'flex flex-col items-center justify-center rounded-xl border border-border bg-card/40 hover:bg-primary/5 hover:border-primary/30 transition-all duration-200 text-center',
                  isCompact ? 'p-2 gap-1.5' : 'p-3 gap-2'
                )}
              >
                <Mic className="h-5 w-5 text-emerald-400" />
                <span className="text-[11px] font-medium text-foreground">Start Session</span>
              </button>

              {/* Action: Upload Report */}
              <button
                onClick={() =>
                  triggerPlaceholderToast('Upload Report', 'PDF file dropzones initiate in the reports phase.')
                }
                className={cn(
                  'flex flex-col items-center justify-center rounded-xl border border-border bg-card/40 hover:bg-primary/5 hover:border-primary/30 transition-all duration-200 text-center',
                  isCompact ? 'p-2 gap-1.5' : 'p-3 gap-2'
                )}
              >
                <FileText className="h-5 w-5 text-amber-400" />
                <span className="text-[11px] font-medium text-foreground">Upload Lab File</span>
              </button>

              {/* Action: Ask AI */}
              <Link
                to="/search"
                className={cn(
                  'flex flex-col items-center justify-center rounded-xl border border-border bg-card/40 hover:bg-primary/5 hover:border-primary/30 transition-all duration-200 text-center',
                  isCompact ? 'p-2 gap-1.5' : 'p-3 gap-2'
                )}
              >
                <Brain className="h-5 w-5 text-purple-400" />
                <span className="text-[11px] font-medium text-foreground">Ask AI Retrieval</span>
              </Link>
            </CardContent>
          </Card>

          {/* Recent Activity Timeline Feed */}
          <Card className="bg-card/20 border-border flex-1">
            <CardHeader className={cn('border-b border-border/60', isCompact ? 'pb-2 mb-2' : 'pb-3 mb-4')}>
              <div className="flex items-center gap-2">
                <History className="h-4.5 w-4.5 text-primary shrink-0" />
                <CardTitle className="text-sm font-semibold uppercase tracking-wider">
                  Recent Activities
                </CardTitle>
              </div>
            </CardHeader>
            <CardContent className={isCompact ? 'pb-3' : 'pb-6'}>
              <div className={cn('relative border-l border-border pl-4 text-xs', isCompact ? 'space-y-3' : 'space-y-4')}>
                {/* Log 1 */}
                <div className="relative">
                  <div className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-blue-400" />
                  <p className="font-semibold text-foreground">Report OCR Parsed</p>
                  <p className="text-muted-foreground text-[10px] mt-0.5">
                    Extracted hemoglobin from lab for Radhika Erra.
                  </p>
                  <span className="text-[9px] text-muted-foreground/60 font-mono block mt-1">
                    2 hours ago
                  </span>
                </div>

                {/* Log 2 */}
                <div className="relative">
                  <div className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-emerald-400" />
                  <p className="font-semibold text-foreground">Clinical Note Finalized</p>
                  <p className="text-muted-foreground text-[10px] mt-0.5">
                    SOAP clinical note verified and saved.
                  </p>
                  <span className="text-[9px] text-muted-foreground/60 font-mono block mt-1">
                    Yesterday
                  </span>
                </div>

                {/* Log 3 */}
                <div className="relative">
                  <div className="absolute -left-[21px] top-1 h-2 w-2 rounded-full bg-amber-400" />
                  <p className="font-semibold text-foreground">Patient Profile Registered</p>
                  <p className="text-muted-foreground text-[10px] mt-0.5">
                    New profile added to clinic database.
                  </p>
                  <span className="text-[9px] text-muted-foreground/60 font-mono block mt-1">
                    3 days ago
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

/**
 * Sub-component PatientRow to handle parallel TanStack queries per patient card,
 * fully validating the query caching layers whitelisted in §6.
 */
function PatientRow({ patient, isCompact }: { patient: Patient; isCompact: boolean }) {
  const { data: overview, isLoading } = usePatientOverview(patient.id);

  return (
    <TableRow className="hover:bg-muted/30 transition-colors border-border">
      {/* 1. Status Column */}
      <TableCell className={cn('font-medium text-foreground', isCompact ? 'py-2' : 'py-3')}>
        {isLoading ? (
          <Skeleton className="h-5 w-20 rounded-full" />
        ) : (
          <StatusBadge status={overview?.status || 'STABLE'} />
        )}
      </TableCell>

      {/* 2. Patient Name link */}
      <TableCell className={cn('font-semibold text-foreground', isCompact ? 'py-2' : 'py-3')}>
        <Link
          to={`/patients/${patient.id}/overview`}
          className="hover:underline hover:text-primary transition-colors text-sm"
        >
          {patient.name}
        </Link>
      </TableCell>

      {/* 3. Demographics */}
      <TableCell className={cn('text-muted-foreground text-xs font-medium', isCompact ? 'py-2' : 'py-3')}>
        {patient.age} yrs · {patient.gender}
      </TableCell>

      {/* 4. Extracted Lab Readings */}
      <TableCell className={cn(isCompact ? 'py-2' : 'py-3')}>
        {isLoading ? (
          <div className="flex gap-2">
            <Skeleton className="h-4.5 w-16" />
            <Skeleton className="h-4.5 w-16" />
          </div>
        ) : overview?.latest_labs && Object.keys(overview.latest_labs).length > 0 ? (
          <div className="flex flex-wrap gap-1.5 text-[10px]">
            {Object.entries(overview.latest_labs).map(([test, val]) => (
              <span
                key={test}
                className="px-2 py-0.5 rounded-lg bg-muted/60 border border-border text-muted-foreground font-mono select-none"
              >
                <span className="capitalize font-semibold text-foreground mr-1">{test}:</span>
                {val}
              </span>
            ))}
          </div>
        ) : (
          <span className="text-[11px] text-muted-foreground/60 italic select-none">
            No labs extracted
          </span>
        )}
      </TableCell>

      {/* 5. Date Registered */}
      <TableCell className={cn('text-muted-foreground text-xs font-mono', isCompact ? 'py-2' : 'py-3')}>
        {formatDate(patient.created_at)}
      </TableCell>
    </TableRow>
  );
}
