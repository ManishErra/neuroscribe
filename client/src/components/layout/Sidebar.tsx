// Sidebar — persistent left navigation. Shows logo, patient list, and Search link.
// Architecture ref: frontend_architecture.md §8 (Sidebar)
// Phase 1: static shell only. Patient list populated in Phase 3 via usePatients().

import { NavLink } from 'react-router-dom';
import { Search, Brain } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function Sidebar() {
  return (
    <aside
      id="sidebar"
      className="flex flex-col w-64 min-h-screen bg-card border-r border-border shrink-0"
    >
      {/* ── Logo ────────────────────────────────────────────────── */}
      <NavLink
        to="/"
        className="flex items-center gap-3 px-5 py-5 border-b border-border hover:bg-accent/40 transition-colors"
      >
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/20 shrink-0">
          <Brain className="h-4 w-4 text-black" />
        </div>
        <div>
          <p className="text-sm font-semibold tracking-wide text-foreground">NeuroScribe</p>
          <p className="text-[11px] text-muted-foreground">AI Clinical Memory</p>
        </div>
      </NavLink>

      {/* ── Patient list placeholder ─────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-3 py-4">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground px-2 mb-3">
          Patients
        </p>
        {/* Phase 3: replace with <PatientList /> powered by usePatients() */}
        <div className="rounded-xl border border-dashed border-border bg-muted/20 py-6 text-center">
          <p className="text-xs text-muted-foreground">Patient list in Phase 3</p>
        </div>
      </div>

      {/* ── Bottom nav links ─────────────────────────────────── */}
      <div className="border-t border-border px-3 py-3">
        <NavLink
          to="/search"
          id="nav-search"
          className={({ isActive }: { isActive: boolean }) =>
            cn(
              'flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors',
              isActive
                ? 'bg-primary/10 text-primary font-medium'
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
