// SessionsTab — lists all consultation logs and anchors session creation.
// Architecture ref: frontend_architecture.md §4, §5.3, §8

import { useParams, useNavigate } from 'react-router-dom';
import { useSessions } from '@/features/sessions/hooks/useSessions';
import { useCreateSession } from '@/features/sessions/hooks/useCreateSession';
import { Skeleton } from '@/components/ui/skeleton';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import EmptyState from '@/components/common/EmptyState';
import { formatDate as displayDate } from '@/utils/formatters';
import { Calendar, Play, CheckCircle2, AlertTriangle, FileMinus, ArrowRight } from 'lucide-react';


export default function SessionsTab() {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();

  // Queries and mutations
  const { data: sessions, isLoading, isError } = useSessions(patientId);
  const createSessionMutation = useCreateSession(patientId);

  // Allocate new consultation row and redirect instantly
  const handleCreateSession = () => {
    createSessionMutation.mutate(undefined, {
      onSuccess: (data) => {
        navigate(`/patients/${patientId}/sessions/${data.id}`);
      },
    });
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 select-none">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="border border-white/[0.06] bg-slate-900/40 p-6 space-y-4">
            <Skeleton className="h-6 w-1/3 animate-pulse" />
            <Skeleton className="h-4 w-1/2 animate-pulse" />
            <Skeleton className="h-5 w-24 rounded-full animate-pulse" />
          </Card>
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-6 text-center select-none shadow-sm">
        <AlertTriangle className="h-6 w-6 text-rose-400 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-rose-400 mb-1">Failed to load consultation logs</h3>
        <p className="text-xs text-muted-foreground">
          A network anomaly occurred. Please refresh or try again later.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 select-none animate-in fade-in duration-300">
      
      {/* ── Header Toolbar ──────────────────────────────────────── */}
      <div className="flex items-center justify-between gap-4 select-none">
        <div className="flex flex-col gap-1">
          <h2 className="text-md font-bold tracking-tight text-foreground select-none">
            Consultation Sessions Log
          </h2>
          <p className="text-xs text-muted-foreground">
            {sessions ? `${sessions.length} sessions recorded` : 'No sessions recorded'}
          </p>
        </div>

        {/* Premium Sage Green Allocation Button */}
        <button
          type="button"
          onClick={handleCreateSession}
          disabled={createSessionMutation.isPending}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-[#508a7b] hover:bg-[#437568] active:bg-[#396358] text-white shadow-md shadow-[#508a7b]/10 active:scale-[0.98] transition-all disabled:opacity-50"
        >
          <Play className="h-3.5 w-3.5 fill-current" />
          {createSessionMutation.isPending ? 'Starting...' : 'New Session'}
        </button>
      </div>

      {/* ── Sessions Cards Grid ─────────────────────────────────── */}
      {!sessions || sessions.length === 0 ? (
        <EmptyState
          title="No recorded consultations yet"
          description="Click 'New Session' above to capture clinical transcripts and generate AI clinical notes."
          action={(
            <button
              type="button"
              onClick={handleCreateSession}
              disabled={createSessionMutation.isPending}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold bg-[#508a7b] hover:bg-[#437568] active:bg-[#396358] text-white shadow-md active:scale-[0.98] transition-all disabled:opacity-50"
            >
              Allocate First Session
            </button>
          )}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6 select-none">
          {sessions.map((session, idx) => {
            // Chronological numbering logic (descending list, latest is sessions.length - idx)
            const sessionNum = sessions.length - idx;
            
            return (
              <Card
                key={session.id}
                onClick={() => navigate(`/patients/${patientId}/sessions/${session.id}`)}
                className="group border border-white/[0.06] bg-slate-900/40 hover:bg-slate-900/60 hover:border-[#508a7b]/30 cursor-pointer shadow-lg rounded-2xl overflow-hidden select-none transition-all duration-200 relative flex flex-col justify-between min-h-[160px]"
              >
                {/* Sage Glow watermark */}
                <div className="absolute top-0 right-0 w-24 h-24 bg-[#508a7b]/5 rounded-full blur-2xl group-hover:bg-[#508a7b]/10 transition-colors pointer-events-none" />

                <CardContent className="p-5 flex flex-col gap-3 flex-1 select-none">
                  
                  {/* Calendar / ID Block */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded-xl bg-white/[0.02] border border-white/[0.06] flex items-center justify-center text-muted-foreground group-hover:text-foreground transition-colors shrink-0">
                        <Calendar className="h-4 w-4" />
                      </div>
                      <div className="flex flex-col gap-0.5">
                        <h3 className="text-sm font-bold text-foreground leading-snug">
                          Session #{sessionNum}
                        </h3>
                        <span className="text-[10px] text-muted-foreground">
                          Consultation Session
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Session Date */}
                  <div className="text-xs font-semibold text-muted-foreground select-none mt-1">
                    Recorded on {displayDate(session.session_date)}
                  </div>

                </CardContent>

                {/* Footer status markers bar */}
                <div className="border-t border-white/[0.04] bg-white/[0.01] px-5 py-3 flex items-center justify-between select-none">
                  
                  {/* Status Badge */}
                  {session.note_finalized ? (
                    <Badge variant="outline" className="px-2.5 py-0.5 rounded-full text-[10px] font-bold border-emerald-500/20 bg-emerald-500/10 text-emerald-400 select-none flex items-center gap-1">
                      <CheckCircle2 className="h-3 w-3 shrink-0" />
                      Finalized
                    </Badge>
                  ) : session.has_note ? (
                    <Badge variant="outline" className="px-2.5 py-0.5 rounded-full text-[10px] font-bold border-amber-500/20 bg-amber-500/10 text-amber-400 select-none flex items-center gap-1">
                      <AlertTriangle className="h-3 w-3 shrink-0" />
                      Draft Review
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="px-2.5 py-0.5 rounded-full text-[10px] font-bold border-white/10 bg-white/[0.04] text-muted-foreground select-none flex items-center gap-1">
                      <FileMinus className="h-3 w-3 shrink-0" />
                      No Note Created
                    </Badge>
                  )}

                  {/* Redirect indicator */}
                  <span className="text-xs font-bold text-muted-foreground group-hover:text-primary transition-colors flex items-center gap-1">
                    Open Session
                    <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
                  </span>

                </div>

              </Card>
            );
          })}
        </div>
      )}

    </div>
  );
}
