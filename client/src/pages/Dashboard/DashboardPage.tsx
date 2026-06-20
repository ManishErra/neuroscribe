import { useState } from 'react';
import { Link } from 'react-router-dom';
import { usePatients } from '@/features/patients/hooks/usePatients';
import { Search, Plus, Mic, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSettings } from '@/store/SettingsContext';
import PatientCreateModal from '@/features/patients/components/PatientCreateModal';

export default function DashboardPage() {
  const { data: patients, isLoading } = usePatients();
  const { settings } = useSettings();
  const isCompact = settings.density === 'compact';
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Sorting for recent patients
  const recentPatients = patients 
    ? [...patients].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 5)
    : [];

  return (
    <div
      id="dashboard-page"
      className={cn(
        'bg-background text-foreground max-w-7xl mx-auto transition-all duration-200 animate-in fade-in',
        isCompact ? 'p-4 space-y-4' : 'p-6 space-y-6'
      )}
    >
      <PatientCreateModal open={isModalOpen} onOpenChange={setIsModalOpen} />

      {/* ── Header & Global Search ──────────────────────────────────────── */}
      <div className={cn('flex flex-col md:flex-row md:items-center justify-between gap-4', isCompact ? 'mb-4' : 'mb-8')}>
        <div>
          <h1 className={cn('font-bold tracking-tight text-foreground', isCompact ? 'text-xl' : 'text-3xl', 'text-[#001848]')}>
            Clinical Workspace
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Welcome back. Here is your recent clinical activity.
          </p>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative w-full md:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input 
              type="text" 
              placeholder="Search NeuroScribe..." 
              className={cn(
                'w-full bg-white border border-[#c3c6d6] rounded-lg pl-9 pr-4 text-sm focus:outline-none focus:ring-1 focus:ring-[#003d9b] transition-all',
                isCompact ? 'py-1.5' : 'py-2'
              )}
            />
          </div>
          <button 
            onClick={() => setIsModalOpen(true)}
            className={cn(
              'flex items-center gap-2 bg-[#003d9b] hover:bg-[#001848] text-white font-medium rounded-lg transition-colors whitespace-nowrap',
              isCompact ? 'px-3 py-1.5 text-xs' : 'px-4 py-2 text-sm'
            )}
          >
            <Plus className="h-4 w-4" />
            Add Patient
          </button>
        </div>
      </div>

      {/* ── Grid Layout ─────────────────────────────────────────── */}
      <div className={cn('grid grid-cols-1 lg:grid-cols-3', isCompact ? 'gap-4' : 'gap-6')}>
        
        {/* Left Column: Recent Patients & Sessions */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          
          {/* Recent Patients */}
          <section className="bg-white rounded-xl border border-border overflow-hidden">
            <div className={cn('border-b border-border bg-[#f8f9fa]', isCompact ? 'px-4 py-2' : 'px-5 py-3')}>
              <h2 className="text-sm font-semibold text-[#001848] uppercase tracking-wide">Recent Patients</h2>
            </div>
            <div className="p-0">
              {isLoading ? (
                <div className="p-4 space-y-3">
                  <div className="h-4 bg-muted rounded w-3/4 animate-pulse"></div>
                  <div className="h-4 bg-muted rounded w-1/2 animate-pulse"></div>
                </div>
              ) : recentPatients.length > 0 ? (
                <ul className="divide-y divide-border">
                  {recentPatients.map(p => (
                    <li key={p.id}>
                      <Link 
                        to={`/patients/${p.id}/timeline`} 
                        className={cn(
                          'flex items-center justify-between hover:bg-accent/40 transition-colors',
                          isCompact ? 'px-4 py-2.5' : 'px-5 py-3'
                        )}
                      >
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-full bg-[#dae2fc] text-[#001848] flex items-center justify-center font-bold text-xs">
                            {p.name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="text-sm font-semibold text-[#191c1d]">{p.name}</p>
                            <p className="text-xs text-muted-foreground">{p.age}Y · {p.gender}</p>
                          </div>
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="p-8 text-center text-muted-foreground text-sm">
                  No recent patients found.
                </div>
              )}
            </div>
          </section>

          {/* Recent Sessions */}
          <section className="bg-white rounded-xl border border-border overflow-hidden">
            <div className={cn('border-b border-border bg-[#f8f9fa]', isCompact ? 'px-4 py-2' : 'px-5 py-3')}>
              <h2 className="text-sm font-semibold text-[#001848] uppercase tracking-wide">Recent Sessions</h2>
            </div>
            <div className="p-8 text-center text-muted-foreground text-sm border-b border-border/50">
              <Mic className="h-6 w-6 mx-auto mb-2 opacity-20" />
              <p>No recent sessions captured today.</p>
              <p className="text-xs mt-1">Start a session from within a Patient Workspace.</p>
            </div>
          </section>

        </div>

        {/* Right Column: Pending Reports */}
        <div className="flex flex-col gap-6">
          <section className="bg-white rounded-xl border border-border overflow-hidden h-full">
            <div className={cn('border-b border-border bg-[#f8f9fa]', isCompact ? 'px-4 py-2' : 'px-5 py-3')}>
              <h2 className="text-sm font-semibold text-[#001848] uppercase tracking-wide">Pending Reports</h2>
            </div>
            <div className="p-8 text-center text-muted-foreground text-sm">
              <FileText className="h-6 w-6 mx-auto mb-2 opacity-20" />
              <p>No reports currently pending OCR extraction.</p>
            </div>
          </section>
        </div>

      </div>
    </div>
  );
}
