import { useParams, Link } from 'react-router-dom';
import { useSessions } from '@/features/sessions/hooks/useSessions';
import { useReports } from '@/features/reports/hooks/useReports';
import { usePatientOverview } from '@/features/insights/hooks/usePatientOverview';
import { Skeleton } from '@/components/ui/skeleton';
import { Activity, Mic, FileText, TrendingUp, AlertTriangle } from 'lucide-react';
import { formatDate } from '@/utils/formatters';
import { cn } from '@/lib/utils';
import { useSettings } from '@/store/SettingsContext';

export default function TimelineTab() {
  const { patientId } = useParams<{ patientId: string }>();
  const { settings } = useSettings();
  const isCompact = settings.density === 'compact';

  // Fetch chronological data streams
  const { data: sessions, isLoading: isSessionsLoading } = useSessions(patientId);
  const { data: reports, isLoading: isReportsLoading } = useReports(patientId);
  const { data: overview, isLoading: isOverviewLoading } = usePatientOverview(patientId);

  const isLoading = isSessionsLoading || isReportsLoading || isOverviewLoading;

  // Aggregate and sort timeline events
  interface TimelineEvent {
    id: string;
    type: string;
    date: Date;
    title: string;
    description: string;
    icon: any;
    color: string;
    bg: string;
    link?: string;
  }
  const timelineEvents: TimelineEvent[] = [];
  
  if (sessions) {
    sessions.forEach(s => {
      timelineEvents.push({
        id: `sess-${s.id}`,
        type: 'session',
        date: s.session_date ? new Date(s.session_date) : new Date(),
        title: 'Clinical Session Recorded',
        description: s.has_note ? 'Session transcribed and SOAP note generated.' : 'Session audio captured.',
        icon: Mic,
        color: 'text-emerald-500',
        bg: 'bg-emerald-50 border-emerald-100',
        link: `/patients/${patientId}/sessions/${s.id}`
      });
    });
  }

  if (reports) {
    reports.forEach(r => {
      timelineEvents.push({
        id: `rep-${r.id}`,
        type: 'report',
        date: r.created_at ? new Date(r.created_at) : new Date(),
        title: 'Lab Report Uploaded',
        description: r.ocr_status === 'ready' ? 'PDF OCR extracted and indexed.' : 'Report pending processing.',
        icon: FileText,
        color: 'text-amber-500',
        bg: 'bg-amber-50 border-amber-100',
        link: undefined
      });
    });
  }

  // Sort descending
  timelineEvents.sort((a, b) => b.date.getTime() - a.date.getTime());

  return (
    <div className={cn('grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in', isCompact ? 'pt-4' : 'pt-6')}>
      
      {/* ── Left Column: Timeline Feed ────────────────────────────────── */}
      <div className="lg:col-span-2 flex flex-col gap-6">
        <section className="bg-white rounded-xl border border-border p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-6">
            <Activity className="h-5 w-5 text-[#003d9b]" />
            <h2 className="text-lg font-bold text-[#191c1d]">Clinical Timeline</h2>
          </div>

          {isLoading ? (
            <div className="space-y-6">
              {[1, 2, 3].map(i => (
                <div key={i} className="flex gap-4">
                  <Skeleton className="h-10 w-10 rounded-full shrink-0" />
                  <div className="space-y-2 flex-1">
                    <Skeleton className="h-4 w-1/3" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </div>
              ))}
            </div>
          ) : timelineEvents.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground border border-dashed border-border rounded-xl bg-muted/20">
              <p className="text-sm">No clinical activities recorded yet.</p>
              <p className="text-xs mt-1">Start a session or upload a report to begin building the timeline.</p>
            </div>
          ) : (
            <div className="relative border-l-2 border-muted ml-5 space-y-8 pb-4">
              {timelineEvents.map(event => {
                const Icon = event.icon;
                return (
                  <div key={event.id} className="relative pl-8">
                    {/* Timeline Node */}
                    <div className={cn('absolute -left-[21px] top-0 h-10 w-10 rounded-full border-2 flex items-center justify-center bg-white', event.bg)}>
                      <Icon className={cn('h-4 w-4', event.color)} />
                    </div>
                    
                    {/* Content */}
                    <div className="bg-[#f8f9fa] border border-border rounded-xl p-4 transition-all hover:shadow-md">
                      <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
                        <h3 className="font-semibold text-[#191c1d] text-sm">{event.title}</h3>
                        <span className="text-xs font-mono text-muted-foreground bg-white px-2 py-0.5 rounded border border-border">
                          {formatDate(event.date.toISOString())}
                        </span>
                      </div>
                      <p className="text-xs text-[#434652] mb-3">{event.description}</p>
                      
                      {event.link && (
                        <Link 
                          to={event.link}
                          className="text-xs font-semibold text-[#003d9b] hover:underline inline-flex items-center gap-1"
                        >
                          View Details
                        </Link>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>

      {/* ── Right Column: Insights & Quick Context ────────────────────── */}
      <div className="flex flex-col gap-6">
        <section className="bg-white rounded-xl border border-border p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="h-5 w-5 text-[#508a7b]" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-[#191c1d]">Latest Insights</h2>
          </div>
          
          {isLoading ? (
            <div className="space-y-4">
              <Skeleton className="h-16 w-full rounded-lg" />
              <Skeleton className="h-16 w-full rounded-lg" />
            </div>
          ) : overview?.clinical_flags && overview.clinical_flags.length > 0 ? (
            <div className="space-y-2">
              {overview.clinical_flags.map((flag, idx) => (
                <div key={idx} className="bg-[#f8f9fa] p-3 rounded-xl border border-border text-xs text-[#434652] leading-relaxed font-semibold">
                  • {flag}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-sm text-muted-foreground text-center py-6 bg-muted/20 rounded-xl border border-dashed border-border">
              No AI summary generated yet.
            </div>
          )}
        </section>

        {overview?.latest_labs && Object.keys(overview.latest_labs).length > 0 && (
          <section className="bg-white rounded-xl border border-border p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#191c1d]">Recent Vitals</h2>
            </div>
            <div className="flex flex-wrap gap-2">
              {Object.entries(overview.latest_labs).map(([key, val]) => (
                <div key={key} className="bg-amber-50 border border-amber-100 rounded-lg px-3 py-2 flex flex-col">
                  <span className="text-[10px] uppercase font-bold text-amber-700/70">{key}</span>
                  <span className="text-sm font-bold text-amber-900">{val as string}</span>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>

    </div>
  );
}
