// Sidebar — persistent left navigation. Shows logo, patient list, and Search link.
// Architecture ref: frontend_architecture.md §8 (Sidebar)

import { NavLink } from 'react-router-dom';
import { Search, Brain, Users, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';
import { usePatients } from '@/features/patients/hooks/usePatients';
import { Skeleton } from '@/components/ui/skeleton';

export default function Sidebar() {
  const { data: patients, isLoading, isError } = usePatients();

  return (
    <aside
      id="sidebar"
      className="flex flex-col w-64 min-h-screen bg-card border-r border-border shrink-0 select-none"
    >
      {/* ── Logo ────────────────────────────────────────────────── */}
      <NavLink
        to="/"
        className="flex items-center gap-3 px-5 py-5 border-b border-border hover:bg-accent/40 transition-colors"
      >
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/20 shrink-0">
          <Brain className="h-4.5 w-4.5 text-black" />
        </div>
        <div>
          <p className="text-sm font-semibold tracking-wide text-foreground">NeuroScribe</p>
          <p className="text-[11px] text-muted-foreground">AI Clinical Memory</p>
        </div>
      </NavLink>

      {/* ── Patient List Section ─────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-3 py-4 flex flex-col gap-1">
        <div className="flex items-center justify-between px-2 mb-2">
          <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
            Patients
          </p>
          <Users className="h-3 w-3 text-muted-foreground" />
        </div>

        {isLoading ? (
          // Dynamic Loading Skeleton Feed
          <div className="space-y-2 px-1">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex flex-col gap-1.5 py-2.5 px-3 border border-transparent">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-20" />
              </div>
            ))}
          </div>
        ) : isError ? (
          <div className="rounded-xl border border-border bg-destructive/5 py-4 px-3 text-center">
            <p className="text-xs text-rose-400 font-medium">Failed to load patients</p>
          </div>
        ) : !patients || patients.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border bg-muted/10 py-6 text-center">
            <p className="text-xs text-muted-foreground">No patients yet</p>
          </div>
        ) : (
          // Active Scrollable Micro-cards
          <div className="space-y-1">
            {patients.map((patient) => (
              <NavLink
                key={patient.id}
                to={`/patients/${patient.id}/overview`}
                className={({ isActive }) =>
                  cn(
                    'flex flex-col gap-0.5 py-2 px-3 rounded-xl text-sm transition-all border border-transparent',
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
      <div className="border-t border-border px-3 py-3 flex flex-col gap-1">
        <NavLink
          to="/patients"
          id="nav-patients"
          className={({ isActive }: { isActive: boolean }) =>
            cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors',
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
              'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors',
              isActive
                ? 'bg-primary/10 text-primary font-medium shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-accent/40'
            )
          }
        >
          <Search className="h-4 w-4 shrink-0" />
          Semantic Search
        </NavLink>
      </div>
    </aside>
  );
}
