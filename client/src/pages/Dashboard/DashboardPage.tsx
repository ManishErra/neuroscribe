// Dashboard page — Phase 1 stub.
// Full implementation in Phase 3: patient list + PatientCard grid + create dialog.
// Architecture ref: frontend_architecture.md §5.1, §15 Phase 3

import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Users } from 'lucide-react';

export default function DashboardPage() {
  return (
    <div id="dashboard-page" className="p-6 space-y-6">
      {/* ── Page header ────────────────────────────────────────── */}
      <div>
        <h1 className="text-2xl font-bold text-foreground tracking-tight">Dashboard</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Patient list and clinical overviews
        </p>
      </div>

      {/* ── Phase notice ───────────────────────────────────────── */}
      <Card id="dashboard-phase-card" className="border-border">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center">
              <Users className="h-5 w-5 text-blue-400" />
            </div>
            <div>
              <p className="font-semibold text-foreground">Patient Management</p>
              <p className="text-xs text-muted-foreground">Implemented in Phase 3</p>
            </div>
            <Badge variant="outline" className="ml-auto text-xs">
              Phase 3
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            This screen will render the full patient list from{' '}
            <code className="text-xs bg-muted px-1 py-0.5 rounded">GET /patients/</code>,
            per-patient clinical status cards from{' '}
            <code className="text-xs bg-muted px-1 py-0.5 rounded">GET /patient-overview/:id</code>,
            and a Create Patient dialog.
          </p>

          {/* Skeleton preview of what's coming */}
          <div className="mt-4 space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-4 p-3 rounded-xl border border-border">
                <Skeleton className="h-10 w-10 rounded-xl" />
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-3 w-32" />
                  <Skeleton className="h-2.5 w-20" />
                </div>
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Tailwind color verification strip */}
      <div className="flex gap-2 text-xs">
        <span className="px-2 py-1 rounded-full bg-stable/10 text-stable border border-stable/20">STABLE</span>
        <span className="px-2 py-1 rounded-full bg-warning/10 text-warning border border-warning/20">WARNING</span>
        <span className="px-2 py-1 rounded-full bg-critical/10 text-critical border border-critical/20">CRITICAL</span>
      </div>
    </div>
  );
}
