// PatientProfilePage — dynamic parent profile page.
// Architecture ref: frontend_architecture.md §4, §5.2, §8

import { useParams, NavLink, Outlet, Link, useNavigate } from 'react-router-dom';
import { usePatient } from '@/features/patients/hooks/usePatient';
import { usePatientOverview } from '@/features/insights/hooks/usePatientOverview';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, Upload, Play, Sparkles } from 'lucide-react';
import { useSettings } from '@/store/SettingsContext';
import { cn } from '@/lib/utils';
import { useCreateSession } from '@/features/sessions/hooks/useCreateSession';

export default function PatientProfilePage() {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const { settings } = useSettings();
  const isCompact = settings.density === 'compact';

  // Fetch patient profile basic details
  const { data: patient, isLoading: isPatientLoading, isError: isPatientError } = usePatient(patientId);

  // Fetch patient high-level overview data (for the StatusBadge, flags, and latest activity)
  const { data: overview, isLoading: isOverviewLoading } = usePatientOverview(patientId);

  const createSessionMutation = useCreateSession(patientId);

  const handleStartSession = () => {
    createSessionMutation.mutate(undefined, {
      onSuccess: (data) => {
        navigate(`/patients/${patientId}/sessions/${data.id}`);
      },
    });
  };

  const isLoading = isPatientLoading || isOverviewLoading;

  if (isPatientError) {
    return (
      <div className="p-6 text-center max-w-lg mx-auto mt-20">
        <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-6 shadow-sm">
          <h3 className="text-sm font-semibold text-rose-400 mb-2">Error Loading Profile</h3>
          <p className="text-xs text-muted-foreground mb-4">
            The patient profile data could not be retrieved from the database.
          </p>
          <Link
            to="/patients"
            className="inline-flex items-center gap-2 text-xs font-semibold text-[#466551] hover:underline"
          >
            <ArrowLeft className="h-3 w-3" />
            Return to Patients Directory
          </Link>
        </div>
      </div>
    );
  }

  // Visual dot details generator
  const getSubtextString = () => {
    if (!patient) return '';
    return `${patient.age}Y · ${patient.gender} · Blood A+`;
  };

  return (
    <div
      className={cn(
        'flex flex-col max-w-[1600px] mx-auto w-full select-none animate-in fade-in duration-300 transition-all duration-200',
        isCompact ? 'gap-4 p-4' : 'gap-6 p-6'
      )}
    >
      {/* ── Back Navigation ─────────────────────────────────────── */}
      <Link
        to="/patients"
        className="flex items-center gap-2 text-xs text-[#424843] hover:text-[#1a1c1a] font-bold transition-colors w-fit group"
      >
        <ArrowLeft className="h-3.5 w-3.5 transition-transform group-hover:-translate-x-1" />
        Back to Patients Directory
      </Link>

      {/* ── Patient Profile Header Panel ───────────────────────── */}
      <div
        className={cn(
          'relative rounded-2xl border border-[#E2E8E4] bg-white shadow-sm flex flex-col md:flex-row md:items-center justify-between overflow-hidden transition-all duration-200',
          isCompact ? 'p-4 gap-4' : 'p-6 gap-6'
        )}
      >
        {/* Decorative backdrop light mesh */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-[#466551]/5 rounded-full blur-[100px] pointer-events-none" />

        <div className={cn('flex items-center z-10', isCompact ? 'gap-3.5' : 'gap-5')}>
          {isLoading ? (
            <Skeleton className={cn('rounded-full shrink-0', isCompact ? 'h-12 w-12' : 'h-16 w-16')} />
          ) : (
            <div
              className={cn(
                'rounded-full bg-[#466551]/10 border border-[#466551]/20 flex items-center justify-center text-[#466551] font-bold shadow-sm select-none shrink-0 transition-all duration-200',
                isCompact ? 'h-12 w-12 text-xs' : 'h-16 w-16 text-sm'
              )}
            >
              {patient?.name.split(' ').map((n) => n[0]).join('').toUpperCase() || 'PT'}
            </div>
          )}

          <div className="flex flex-col gap-1">
            <div className="flex items-center flex-wrap gap-3">
              {isLoading ? (
                <Skeleton className="h-7 w-44" />
              ) : (
                <h1 className={cn('font-bold tracking-tight text-[#1a1c1a]', isCompact ? 'text-sm' : 'text-base')}>{patient?.name}</h1>
              )}

              {/* ID Badge */}
              {isLoading ? (
                <Skeleton className="h-5 w-20 rounded-full" />
              ) : (
                <span className="px-2 py-0.5 rounded-md text-[9px] font-bold bg-[#faf9f6] border border-[#c3c6d6] text-[#424843] uppercase tracking-wider select-none">
                  MR-{patientId?.slice(0, 4).toUpperCase()}
                </span>
              )}

              {/* StatusBadge */}
              {isLoading ? (
                <Skeleton className="h-5 w-20 rounded-full" />
              ) : (
                <StatusBadge status={overview?.status || 'STABLE'} />
              )}
            </div>

            {isLoading ? (
              <Skeleton className="h-4 w-32" />
            ) : (
              <p className="text-[10px] font-bold text-[#424843]">{getSubtextString()}</p>
            )}
          </div>
        </div>

        {/* Action Controls Menu */}
        <div className={cn('flex items-center flex-wrap z-10', isCompact ? 'gap-1.5' : 'gap-2.5')}>
          <Link
            to={`/patients/${patientId}/reports`}
            className={cn(
              'inline-flex items-center gap-2 rounded-lg text-xs font-bold bg-white border border-[#c3c6d6] text-[#1a1c1a] hover:bg-[#faf9f6] active:scale-[0.98] transition-all shadow-sm',
              isCompact ? 'px-2.5 py-1.5' : 'px-3.5 py-2'
            )}
          >
            <Upload className="h-3.5 w-3.5 text-[#424843]/80" />
            Upload Report
          </Link>
          
          <button
            type="button"
            onClick={handleStartSession}
            disabled={createSessionMutation.isPending}
            className={cn(
              'inline-flex items-center gap-2 rounded-lg text-xs font-bold bg-white border border-[#c3c6d6] text-[#1a1c1a] hover:bg-[#faf9f6] active:scale-[0.98] transition-all shadow-sm disabled:opacity-50',
              isCompact ? 'px-2.5 py-1.5' : 'px-3.5 py-2'
            )}
          >
            <Play className="h-3.5 w-3.5 text-[#424843]/80" />
            {createSessionMutation.isPending ? 'Starting...' : 'Start Session'}
          </button>

          {/* Premium Sage Green Action Button */}
          <Link
            to={`/patients/${patientId}/ask`}
            className={cn(
              'inline-flex items-center gap-2 rounded-lg text-xs font-bold bg-[#466551] hover:bg-[#3b5443] active:bg-[#396358] text-white shadow-sm active:scale-[0.98] transition-all',
              isCompact ? 'px-3 py-1.5' : 'px-4 py-2'
            )}
          >
            <Sparkles className="h-3.5 w-3.5 fill-current" />
            Ask NeuroScribe
          </Link>
        </div>
      </div>

      {/* ── Sub Navigation Tabs Deck ────────────────────────────── */}
      <div className={cn('border-b border-[#E2E8E4] flex items-center overflow-x-auto select-none no-scrollbar bg-[#faf9f6]', isCompact ? 'gap-4' : 'gap-6')}>
        {[
          { path: 'timeline', label: 'Timeline' },
          { path: 'overview', label: 'Overview' },
          { path: 'sessions', label: 'Sessions' },
          { path: 'reports', label: 'Reports' },
          { path: 'ask', label: 'Ask NeuroScribe' },
        ].map((tab) => (
          <NavLink
            key={tab.path}
            to={tab.path}
            className={({ isActive }) =>
              cn(
                'text-xs font-bold transition-all relative select-none whitespace-nowrap uppercase tracking-wider',
                isCompact ? 'pb-2' : 'pb-3',
                isActive
                  ? 'text-[#466551] font-bold'
                  : 'text-[#424843] hover:text-[#1a1c1a]'
              )
            }
          >
            {({ isActive }) => (
              <>
                {tab.label}
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#466551] rounded-full animate-in slide-in-from-left duration-200" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </div>

      {/* ── Tab Layout Outlet ───────────────────────────────────── */}
      <div className="min-h-[400px] w-full">
        <Outlet />
      </div>

    </div>
  );
}
