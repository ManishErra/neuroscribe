// PatientProfilePage — dynamic parent profile page.
// Architecture ref: frontend_architecture.md §4, §5.2, §8

import { useParams, NavLink, Outlet, Link } from 'react-router-dom';
import { usePatient } from '@/features/patients/hooks/usePatient';
import { usePatientOverview } from '@/features/insights/hooks/usePatientOverview';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, Upload, Play, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function PatientProfilePage() {
  const { patientId } = useParams<{ patientId: string }>();

  // Fetch patient profile basic details
  const { data: patient, isLoading: isPatientLoading, isError: isPatientError } = usePatient(patientId);

  // Fetch patient high-level overview data (for the StatusBadge, flags, and latest activity)
  const { data: overview, isLoading: isOverviewLoading } = usePatientOverview(patientId);

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
            className="inline-flex items-center gap-2 text-xs font-semibold text-primary hover:underline"
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
    // Format age and DOB/gender
    return `${patient.age}Y · ${patient.gender} · Blood A+`;
  };

  return (
    <div className="flex flex-col gap-6 p-6 max-w-[1600px] mx-auto w-full select-none animate-in fade-in duration-300">
      
      {/* ── Back Navigation ─────────────────────────────────────── */}
      <Link
        to="/patients"
        className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground font-semibold transition-colors w-fit group"
      >
        <ArrowLeft className="h-3.5 w-3.5 transition-transform group-hover:-translate-x-1" />
        Back to Patients Directory
      </Link>

      {/* ── Patient Profile Header Panel ───────────────────────── */}
      <div className="relative rounded-2xl border border-white/[0.06] bg-slate-900/40 backdrop-blur-md p-6 shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-6 overflow-hidden">
        {/* Decorative backdrop light mesh */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-primary/5 rounded-full blur-[100px] pointer-events-none" />

        <div className="flex items-center gap-5 z-10">
          {isLoading ? (
            <Skeleton className="h-16 w-16 rounded-full shrink-0" />
          ) : (
            <div className="h-16 w-16 rounded-full bg-gradient-to-br from-slate-800 to-slate-700 border border-white/[0.08] flex items-center justify-center text-foreground font-semibold text-lg shadow-inner select-none shrink-0">
              {patient?.name.split(' ').map((n) => n[0]).join('').toUpperCase() || 'PT'}
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <div className="flex items-center flex-wrap gap-3">
              {isLoading ? (
                <Skeleton className="h-7 w-44" />
              ) : (
                <h1 className="text-xl font-bold tracking-tight text-foreground">{patient?.name}</h1>
              )}

              {/* ID Badge */}
              {isLoading ? (
                <Skeleton className="h-5 w-20 rounded-full" />
              ) : (
                <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-white/[0.04] border border-white/[0.06] text-muted-foreground uppercase tracking-wider select-none">
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
              <p className="text-xs font-semibold text-muted-foreground">{getSubtextString()}</p>
            )}
          </div>
        </div>

        {/* Action Controls Menu */}
        <div className="flex items-center flex-wrap gap-2.5 z-10">
          <button
            type="button"
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-white/[0.04] border border-white/[0.08] text-foreground hover:bg-white/[0.08] active:scale-[0.98] transition-all"
          >
            <Upload className="h-3.5 w-3.5 text-muted-foreground" />
            Upload Report
          </button>
          
          <button
            type="button"
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-white/[0.04] border border-white/[0.08] text-foreground hover:bg-white/[0.08] active:scale-[0.98] transition-all"
          >
            <Play className="h-3.5 w-3.5 text-muted-foreground" />
            Start Session
          </button>

          {/* Premium Sage Green Action Button */}
          <button
            type="button"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-[#508a7b] hover:bg-[#437568] active:bg-[#396358] text-white shadow-md shadow-[#508a7b]/10 active:scale-[0.98] transition-all"
          >
            <Sparkles className="h-3.5 w-3.5 fill-current" />
            Ask NeuroScribe
          </button>
        </div>
      </div>

      {/* ── Sub Navigation Tabs Deck ────────────────────────────── */}
      <div className="border-b border-white/[0.06] flex items-center gap-6 overflow-x-auto select-none no-scrollbar">
        {[
          { path: 'overview', label: 'Overview' },
          { path: 'reports', label: 'Reports' },
          { path: 'timeline', label: 'Clinical Trends' },
          { path: 'sessions', label: 'Sessions' },
        ].map((tab) => (
          <NavLink
            key={tab.path}
            to={tab.path}
            className={({ isActive }) =>
              cn(
                'pb-3 text-xs font-bold transition-all relative select-none whitespace-nowrap',
                isActive
                  ? 'text-primary font-bold'
                  : 'text-muted-foreground hover:text-foreground'
              )
            }
          >
            {({ isActive }) => (
              <>
                {tab.label}
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#508a7b] rounded-full shadow-[0_0_8px_rgba(80,138,123,0.5)] animate-in slide-in-from-left duration-200" />
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
