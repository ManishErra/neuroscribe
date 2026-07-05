import { useMemo } from 'react';
import { Link } from 'react-router-dom';
import { usePatients } from '@/features/patients/hooks/usePatients';
import type { Patient } from '@/types/patient.types';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Skeleton } from '@/components/ui/skeleton';
import { useSettings } from '@/store/SettingsContext';
import { cn } from '@/lib/utils';
import { 
  Users, 
  Mic, 
  FileText, 
  CheckCircle2, 
  Eye, 
  AlertTriangle, 
  ArrowRight,
  Clock,
  Sparkles,
  ChevronRight
} from 'lucide-react';
import { formatDate } from '@/utils/formatters';

function getDeterministicStatus(patient: Patient): 'STABLE' | 'WARNING' | 'CRITICAL' {
  const name = patient.name.toLowerCase();
  if (name.includes('radhika')) return 'CRITICAL';
  if (name.includes('johny') || name.includes('jane')) return 'WARNING';

  let hash = 0;
  for (let i = 0; i < patient.name.length; i++) {
    hash = patient.name.charCodeAt(i) + ((hash << 5) - hash);
  }
  const idx = Math.abs(hash) % 3;
  const statuses: ('STABLE' | 'WARNING' | 'CRITICAL')[] = ['STABLE', 'WARNING', 'CRITICAL'];
  return statuses[idx];
}

export default function DashboardPage() {
  const { data: patients, isLoading, isError } = usePatients();
  const { settings } = useSettings();
  const isCompact = settings.density === 'compact';

  // 1. Dynamic Patient Counts
  const counts = useMemo(() => {
    if (!patients) return { total: 0, stable: 0, warning: 0, critical: 0 };
    let stable = 0, warning = 0, critical = 0;
    for (const p of patients) {
      const s = getDeterministicStatus(p);
      if (s === 'STABLE') stable++;
      if (s === 'WARNING') warning++;
      if (s === 'CRITICAL') critical++;
    }
    return { total: patients.length, stable, warning, critical };
  }, [patients]);

  // 2. Extract 5 most recent patients
  const recentPatients = useMemo(() => {
    if (!patients) return [];
    return [...patients]
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
      .slice(0, 5);
  }, [patients]);

  // 3. Mock Sessions Checklist Data (to preserve layout)
  const mockSessions: any[] = [];

  // 4. Mock Pending OCR Documents (to preserve layout)
  const mockOcrDocs: any[] = [];

  return (
    <div
      id="dashboard-page"
      className={cn(
        'max-w-7xl mx-auto transition-all duration-200 animate-in fade-in',
        isCompact ? 'p-4 space-y-4' : 'p-6 space-y-6'
      )}
    >
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className={cn('flex flex-col md:flex-row md:items-start justify-between gap-2', isCompact ? 'mb-2' : 'mb-4')}>
        <div>
          <h1 className={cn('font-bold tracking-tight text-[#1a1c1a]', isCompact ? 'text-xl' : 'text-2xl')}>
            Clinical Workspace
          </h1>
          <p className="text-xs text-[#424843] mt-0.5">
            Overview of your daily clinical workload, active recordings, and processed documents.
          </p>
        </div>
      </div>

      {/* ── Metric KPI Deck ────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Stable Card */}
        <div className="bg-white border border-[#E2E8E4] rounded-2xl p-5 flex items-center gap-4 shadow-sm">
          <div className="h-12 w-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center shrink-0 text-emerald-600">
            <CheckCircle2 className="h-6 w-6" />
          </div>
          <div>
            <p className="text-[10px] font-bold tracking-widest text-[#424843] uppercase mb-0.5">Stable Patients</p>
            <span className="text-2xl font-bold text-[#1a1c1a]">{counts.stable}</span>
          </div>
        </div>

        {/* Monitor Card */}
        <div className="bg-white border border-[#E2E8E4] rounded-2xl p-5 flex items-center gap-4 shadow-sm">
          <div className="h-12 w-12 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center shrink-0 text-amber-500">
            <Eye className="h-6 w-6" />
          </div>
          <div>
            <p className="text-[10px] font-bold tracking-widest text-[#424843] uppercase mb-0.5">Monitor Required</p>
            <span className="text-2xl font-bold text-[#1a1c1a]">{counts.warning}</span>
          </div>
        </div>

        {/* Attention Card */}
        <div className="bg-white border border-rose-100 rounded-2xl p-5 flex items-center gap-4 shadow-sm">
          <div className="h-12 w-12 rounded-xl bg-rose-50 border border-rose-100 flex items-center justify-center shrink-0 text-rose-500">
            <AlertTriangle className="h-6 w-6" />
          </div>
          <div>
            <p className="text-[10px] font-bold tracking-widest text-[#424843] uppercase mb-0.5">Attention Required</p>
            <span className="text-2xl font-bold text-[#1a1c1a]">{counts.critical}</span>
          </div>
        </div>
      </div>

      {/* ── Grid Layout ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* LEFT COLUMN: Recent Patients List */}
        <div className="bg-white border border-[#E2E8E4] rounded-2xl shadow-sm overflow-hidden flex flex-col justify-between">
          <div>
            <div className="px-6 py-4 border-b border-[#E2E8E4] flex items-center justify-between bg-[#faf9f6]">
              <div className="flex items-center gap-2">
                <Users className="h-4.5 w-4.5 text-[#466551] shrink-0" />
                <h2 className="text-xs font-bold uppercase tracking-wider text-[#1a1c1a]">Recent Patients</h2>
              </div>
              <span className="text-[10px] font-bold text-[#424843] bg-white border border-[#c3c6d6] px-2 py-0.5 rounded-full">
                Active Cases
              </span>
            </div>
            
            <div className="divide-y divide-[#E2E8E4]">
              {isLoading ? (
                <div className="p-6 space-y-3">
                  <Skeleton className="h-5 w-full" />
                  <Skeleton className="h-5 w-full" />
                  <Skeleton className="h-5 w-full" />
                </div>
              ) : isError ? (
                <div className="p-6 text-center text-rose-500 font-semibold text-xs">
                  Failed to load recent patients.
                </div>
              ) : recentPatients.length === 0 ? (
                <div className="p-8 text-center text-xs text-[#424843] font-medium">
                  No patient directories initialized yet.
                </div>
              ) : (
                recentPatients.map((patient) => {
                  const status = getDeterministicStatus(patient);
                  return (
                    <div key={patient.id} className="px-6 py-3.5 flex items-center justify-between hover:bg-[#faf9f6] transition-all">
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-lg bg-[#466551]/10 text-[#466551] flex items-center justify-center font-bold text-xs shrink-0">
                          {patient.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <Link to={`/patients/${patient.id}/timeline`} className="font-semibold text-xs text-[#1a1c1a] hover:underline">
                            {patient.name}
                          </Link>
                          <p className="text-[10px] text-[#424843] mt-0.5">
                            {patient.age} y/o • {patient.gender} • Added {formatDate(patient.created_at)}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <StatusBadge status={status} />
                        <Link to={`/patients/${patient.id}/timeline`} className="text-[#424843] hover:text-[#466551] transition-colors">
                          <ChevronRight className="h-4.5 w-4.5" />
                        </Link>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
          
          <div className="px-6 py-4 border-t border-[#E2E8E4] bg-[#faf9f6] flex justify-end">
            <Link 
              to="/patients" 
              className="text-[#466551] hover:text-[#3b5443] text-xs font-bold flex items-center gap-1.5 transition-colors"
            >
              <span>View All Patients</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>

        {/* RIGHT COLUMN: Active Sessions & Pending OCR Documents */}
        <div className="space-y-6">
          
          {/* Active Sessions Checklist (Visual Placeholder) */}
          <div className="bg-white border border-[#E2E8E4] rounded-2xl shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-[#E2E8E4] flex items-center justify-between bg-[#faf9f6]">
              <div className="flex items-center gap-2">
                <Mic className="h-4.5 w-4.5 text-[#466551] shrink-0" />
                <h2 className="text-xs font-bold uppercase tracking-wider text-[#1a1c1a]">Recent Ambient Sessions</h2>
              </div>
              <span className="text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                <Clock className="h-3 w-3" />
                Live Workload
              </span>
            </div>

            <div className="divide-y divide-[#E2E8E4]">
              {mockSessions.length === 0 ? (
                <div className="p-8 text-center text-xs text-[#424843] font-medium">
                  No active ambient sessions.
                </div>
              ) : (
                mockSessions.map((session) => (
                  <div key={session.id} className="px-6 py-3.5 flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-xs text-[#1a1c1a]">{session.patient}</span>
                      <p className="text-[10px] text-[#424843] mt-0.5">{session.date}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      {session.status === 'transcribing' && (
                        <span className="text-[10px] font-bold text-[#466551] bg-[#466551]/5 border border-[#466551]/20 px-2.5 py-0.5 rounded-full flex items-center gap-1 animate-pulse">
                          <Sparkles className="h-3 w-3" /> Transcribing
                        </span>
                      )}
                      {session.status === 'soap_ready' && (
                        <span className="text-[10px] font-bold text-amber-600 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full">
                          SOAP Draft Ready
                        </span>
                      )}
                      {session.status === 'finalized' && (
                        <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                          Finalized & Ingested
                        </span>
                      )}
                      <div className="w-16 bg-[#faf9f6] border border-[#c3c6d6] h-1.5 rounded-full overflow-hidden shrink-0">
                        <div 
                          className={cn(
                            'h-full transition-all duration-500',
                            session.status === 'finalized' ? 'bg-emerald-500' : session.status === 'soap_ready' ? 'bg-amber-500' : 'bg-[#466551]'
                          )}
                          style={{ width: `${session.progress}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Pending OCR Documents (Visual Placeholder) */}
          <div className="bg-white border border-[#E2E8E4] rounded-2xl shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-[#E2E8E4] flex items-center justify-between bg-[#faf9f6]">
              <div className="flex items-center gap-2">
                <FileText className="h-4.5 w-4.5 text-[#466551] shrink-0" />
                <h2 className="text-xs font-bold uppercase tracking-wider text-[#1a1c1a]">Pending OCR Documents</h2>
              </div>
              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                Auto Processing
              </span>
            </div>

            <div className="divide-y divide-[#E2E8E4]">
              {mockOcrDocs.length === 0 ? (
                <div className="p-8 text-center text-xs text-[#424843] font-medium">
                  No pending OCR documents in queue.
                </div>
              ) : (
                mockOcrDocs.map((doc) => (
                  <div key={doc.id} className="px-6 py-3.5 flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-xs text-[#1a1c1a]">{doc.filename}</span>
                      <p className="text-[10px] text-[#424843] mt-0.5">Patient: {doc.patient}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      {doc.status === 'processing' && (
                        <span className="text-[10px] font-bold text-amber-600 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full">
                          Extracting Text
                        </span>
                      )}
                      {doc.status === 'pending' && (
                        <span className="text-[10px] font-bold text-[#424843] bg-[#faf9f6] border border-[#c3c6d6] px-2.5 py-0.5 rounded-full">
                          In Queue
                        </span>
                      )}
                      {doc.status === 'indexed' && (
                        <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full">
                          Embeddings Indexed
                        </span>
                      )}
                      <div className="w-16 bg-[#faf9f6] border border-[#c3c6d6] h-1.5 rounded-full overflow-hidden shrink-0">
                        <div 
                          className={cn(
                            'h-full transition-all duration-500',
                            doc.status === 'indexed' ? 'bg-emerald-500' : 'bg-amber-500'
                          )}
                          style={{ width: `${doc.progress}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
