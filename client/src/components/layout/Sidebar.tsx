// Sidebar — persistent left navigation. Shows logo, patient list, and Search link.
// Architecture ref: frontend_architecture.md §8 (Sidebar)

import { NavLink } from 'react-router-dom';
import { Search, Brain, Users, Activity, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';
import { usePatients } from '@/features/patients/hooks/usePatients';
import { Skeleton } from '@/components/ui/skeleton';
import { useSettings } from '@/store/SettingsContext';

export default function Sidebar() {
  const { data: patients, isLoading, isError } = usePatients();
  const { settings } = useSettings();
  const isCompact = settings.density === 'compact';

  return (
    <aside
      id="sidebar"
      className={cn(
        'flex flex-col min-h-screen bg-card border-r border-border shrink-0 select-none transition-all duration-200',
        isCompact ? 'w-52' : 'w-64'
      )}
    >
      {/* ── Logo ────────────────────────────────────────────────── */}
      <NavLink
        to="/"
        className={cn(
          'flex items-center gap-3 border-b border-border hover:bg-accent/40 transition-colors',
          isCompact ? 'px-4 py-3' : 'px-5 py-5'
        )}
      >
        <div
          className={cn(
            'rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/20 shrink-0 transition-all duration-200',
            isCompact ? 'w-8 h-8' : 'w-9 h-9'
          )}
        >
          <Brain className={cn(isCompact ? 'h-4 w-4' : 'h-4.5 w-4.5', 'text-black')} />
        </div>
        <div>
          <p className={cn('font-semibold tracking-wide text-foreground', isCompact ? 'text-xs' : 'text-sm')}>
            NeuroScribe
          </p>
          <p className="text-[11px] text-muted-foreground">AI Clinical Memory</p>
        </div>
      </NavLink>

      {/* ── Patient List Section ─────────────────────────────────── */}
      <div
        className={cn(
          'flex-1 overflow-y-auto flex flex-col',
          isCompact ? 'px-2 py-3 gap-0.5' : 'px-3 py-4 gap-1'
        )}
      >
        <div className={cn('flex items-center justify-between px-2', isCompact ? 'mb-1' : 'mb-2')}>
          <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
            Patients
          </p>
          <Users className="h-3 w-3 text-muted-foreground" />
        </div>

        {isLoading ? (
          // Dynamic Loading Skeleton Feed
          <div className={cn('space-y-2', isCompact ? 'px-0.5' : 'px-1')}>
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className={cn(
                  'flex flex-col gap-1.5 border border-transparent',
                  isCompact ? 'py-1.5 px-2' : 'py-2.5 px-3'
                )}
              >
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-20" />
              </div>
            ))}
          </div>
        ) : isError ? (
          <div className={cn('rounded-xl border border-border bg-destructive/5 text-center', isCompact ? 'py-3 px-2' : 'py-4 px-3')}>
            <p className="text-xs text-rose-400 font-medium">Failed to load patients</p>
          </div>
        ) : !patients || patients.length === 0 ? (
          <div className={cn('rounded-xl border border-dashed border-border bg-muted/10 text-center', isCompact ? 'py-4' : 'py-6')}>
            <p className="text-xs text-muted-foreground">No patients yet</p>
          </div>
        ) : (
          // Active Scrollable Micro-cards
          <div className={cn(isCompact ? 'space-y-0.5' : 'space-y-1')}>
            {patients.map((patient) => (
              <NavLink
                key={patient.id}
                to={`/patients/${patient.id}/overview`}
                className={({ isActive }) =>
                  cn(
                    'flex flex-col gap-0.5 rounded-xl transition-all border border-transparent',
                    isCompact ? 'py-1.5 px-2 text-xs' : 'py-2 px-3 text-sm',
                    isActive
                      ? 'bg-primary/10 border-primary/20 text-primary font-medium shadow-sm'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent/40'
                  )
                }
              >
                <div className="flex items-center justify-between gap-1">
                  <span className="truncate font-medium text-foreground">{patient.name}</span>
                  <Activity className="h-3 w-3 opacity-30 shrink-0" />
                </div>
                <span className="text-[11px] opacity-70">
                  {patient.age} yrs · {patient.gender}
                </span>
              </NavLink>
            ))}
          </div>
        )}
      </div>

      {/* ── Bottom nav links ─────────────────────────────────── */}
      <div
        className={cn(
          'border-t border-border flex flex-col',
          isCompact ? 'px-2 py-2 gap-0.5' : 'px-3 py-3 gap-1'
        )}
      >
        <NavLink
          to="/patients"
          id="nav-patients"
          className={({ isActive }: { isActive: boolean }) =>
            cn(
              'flex items-center gap-3 rounded-xl transition-colors',
              isCompact ? 'px-2 py-2 text-xs' : 'px-3 py-2.5 text-sm',
              isActive
                ? 'bg-primary/10 text-primary font-medium shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent/40'
            )
          }
        >
          <Users className="h-4 w-4 shrink-0" />
          Patient Directory
        </NavLink>

        <NavLink
          to="/search"
          id="nav-search"
          className={({ isActive }: { isActive: boolean }) =>
            cn(
              'flex items-center gap-3 rounded-xl transition-colors',
              isCompact ? 'px-2 py-2 text-xs' : 'px-3 py-2.5 text-sm',
              isActive
                ? 'bg-primary/10 text-primary font-medium shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent/40'
            )
          }
        >
          <Search className="h-4 w-4 shrink-0" />
          Semantic Search
        </NavLink>

        <NavLink
          to="/settings"
          id="nav-settings"
          className={({ isActive }: { isActive: boolean }) =>
            cn(
              'flex items-center gap-3 rounded-xl transition-colors',
              isCompact ? 'px-2 py-2 text-xs' : 'px-3 py-2.5 text-sm',
              isActive
                ? 'bg-primary/10 text-primary font-medium shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent/40'
            )
          }
        >
          <Settings className="h-4 w-4 shrink-0" />
          Settings
        </NavLink>
      </div>
    </aside>
  );
}
