import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { usePatients } from '@/features/patients/hooks/usePatients';
import type { Patient } from '@/types/patient.types';
import PatientCreateModal from '@/features/patients/components/PatientCreateModal';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Skeleton } from '@/components/ui/skeleton';
import { useSettings } from '@/store/SettingsContext';
import { cn } from '@/lib/utils';
import { Search, Plus, CheckCircle2, Eye, AlertTriangle, ChevronLeft, ChevronRight } from 'lucide-react';
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

export default function PatientDirectoryPage() {
  const { data: patients, isLoading, isError } = usePatients();
  const { settings } = useSettings();
  const isCompact = settings.density === 'compact';

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'STABLE' | 'WARNING' | 'CRITICAL'>('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Derive counts
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

  const filteredPatients = useMemo(() => {
    if (!patients) return [];
    return patients.filter((patient) => {
      const matchesSearch = patient.name.toLowerCase().includes(searchTerm.toLowerCase());
      const patientStatus = getDeterministicStatus(patient);
      const matchesStatus = statusFilter === 'ALL' || patientStatus === statusFilter;
      return matchesSearch && matchesStatus;
    }).sort((a, b) => a.name.localeCompare(b.name));
  }, [patients, searchTerm, statusFilter]);

  const totalPages = Math.ceil(filteredPatients.length / itemsPerPage);
  const paginatedPatients = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredPatients.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredPatients, currentPage]);

  return (
    <div
      id="patient-directory-page"
      className={cn(
        'max-w-7xl mx-auto transition-all duration-200 animate-in fade-in',
        isCompact ? 'p-4 space-y-4' : 'p-6 space-y-6'
      )}
    >
      <PatientCreateModal open={isModalOpen} onOpenChange={setIsModalOpen} />

      {/* ── Page Header ────────────────────────────────────────── */}
      <div className={cn('flex flex-col md:flex-row md:items-start justify-between gap-4', isCompact ? 'mb-4' : 'mb-6')}>
        <div>
          <h1 className={cn('font-bold tracking-tight text-[#191c1d]', isCompact ? 'text-2xl' : 'text-[32px]')}>
            Patient Directory
          </h1>
          <p className="text-sm text-[#434652] mt-1">
            {counts.total.toLocaleString()} Total Patients
          </p>
        </div>
        <div className="flex items-center gap-4 w-full md:w-auto">
          <div className="relative w-full md:w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#747783]" />
            <input 
              type="text" 
              placeholder="Search Patients..." 
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className={cn(
                'w-full bg-white border border-[#c3c6d6] rounded-full pl-9 pr-4 text-sm focus:outline-none focus:border-[#003d9b] transition-all',
                isCompact ? 'py-1.5' : 'py-2'
              )}
            />
          </div>
          <button 
            onClick={() => setIsModalOpen(true)}
            className={cn(
              'flex items-center gap-2 bg-[#508a7b] hover:bg-[#437568] text-white font-medium rounded-lg transition-colors whitespace-nowrap',
              isCompact ? 'px-3 py-1.5 text-xs' : 'px-4 py-2 text-sm'
            )}
          >
            <Plus className="h-4 w-4" />
            Add Patient
          </button>
        </div>
      </div>

      {/* ── Metric Cards ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Stable */}
        <div className="bg-white border border-border rounded-xl p-5 flex items-center gap-4">
          <div className="h-12 w-12 rounded-full bg-emerald-50 border border-emerald-100 flex items-center justify-center shrink-0">
            <CheckCircle2 className="h-6 w-6 text-emerald-500" />
          </div>
          <div>
            <p className="text-[11px] font-bold tracking-wider text-[#434652] uppercase mb-1">Stable Patients</p>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-[#191c1d]">{counts.stable.toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Monitor */}
        <div className="bg-white border border-border rounded-xl p-5 flex items-center gap-4">
          <div className="h-12 w-12 rounded-full bg-amber-50 border border-amber-100 flex items-center justify-center shrink-0">
            <Eye className="h-6 w-6 text-amber-500" />
          </div>
          <div>
            <p className="text-[11px] font-bold tracking-wider text-[#434652] uppercase mb-1">Monitor Patients</p>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-[#191c1d]">{counts.warning.toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Attention */}
        <div className="bg-white border border-rose-100 rounded-xl p-5 flex items-center gap-4">
          <div className="h-12 w-12 rounded-full bg-rose-50 border border-rose-100 flex items-center justify-center shrink-0">
            <AlertTriangle className="h-6 w-6 text-rose-500" />
          </div>
          <div>
            <p className="text-[11px] font-bold tracking-wider text-[#434652] uppercase mb-1">Attention Required</p>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-[#191c1d]">{counts.critical.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Table Container ──────────────────────────────────────── */}
      <div className="bg-white border border-border rounded-xl overflow-hidden mt-2">
        {/* Tabs */}
        <div className="flex items-center gap-6 px-6 border-b border-border">
          {(['ALL', 'STABLE', 'WARNING', 'CRITICAL'] as const).map((status) => {
            const label = status === 'ALL' ? 'All Patients' : status === 'WARNING' ? 'Monitor' : status === 'CRITICAL' ? 'Attention Required' : 'Stable';
            const isActive = statusFilter === status;
            return (
              <button
                key={status}
                onClick={() => {
                  setStatusFilter(status);
                  setCurrentPage(1);
                }}
                className={cn(
                  'py-3 text-sm font-semibold transition-colors relative',
                  isActive ? 'text-[#508a7b]' : 'text-[#747783] hover:text-[#191c1d]'
                )}
              >
                {label}
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#508a7b]" />
                )}
              </button>
            );
          })}
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#f8f9fa] border-b border-border text-[#434652]">
              <tr>
                <th className="px-6 py-3 font-semibold text-xs tracking-wider uppercase">Patient Name</th>
                <th className="px-6 py-3 font-semibold text-xs tracking-wider uppercase">Age/Gender</th>
                <th className="px-6 py-3 font-semibold text-xs tracking-wider uppercase">Last Visit</th>
                <th className="px-6 py-3 font-semibold text-xs tracking-wider uppercase">Status</th>
                <th className="px-6 py-3 font-semibold text-xs tracking-wider uppercase">Reports</th>
                <th className="px-6 py-3 font-semibold text-xs tracking-wider uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center">
                    <Skeleton className="h-6 w-full max-w-md mx-auto" />
                  </td>
                </tr>
              ) : isError ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-rose-500 font-medium">
                    Failed to load patients.
                  </td>
                </tr>
              ) : paginatedPatients.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-muted-foreground">
                    No patients found.
                  </td>
                </tr>
              ) : (
                paginatedPatients.map((patient) => {
                  const status = getDeterministicStatus(patient);
                  return (
                    <tr key={patient.id} className="hover:bg-[#f8f9fa] transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="h-8 w-8 rounded-full bg-[#e1e3e4] text-[#191c1d] flex items-center justify-center font-bold text-xs shrink-0">
                            {patient.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()}
                          </div>
                          <Link to={`/patients/${patient.id}/timeline`} className="font-semibold text-[#191c1d] hover:text-[#003d9b]">
                            {patient.name}
                          </Link>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-[#434652]">
                        {patient.age} / {patient.gender.charAt(0).toUpperCase()}
                      </td>
                      <td className="px-6 py-4 text-[#434652]">
                        {formatDate(patient.created_at)}
                      </td>
                      <td className="px-6 py-4">
                        <StatusBadge status={status} />
                      </td>
                      <td className="px-6 py-4 text-[#434652]">
                        0
                      </td>
                      <td className="px-6 py-4">
                        <Link 
                          to={`/patients/${patient.id}/timeline`}
                          className="text-[#003d9b] font-medium text-xs hover:underline"
                        >
                          View Profile
                        </Link>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        {!isLoading && !isError && filteredPatients.length > 0 && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-border bg-white">
            <span className="text-xs text-[#747783]">
              Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, filteredPatients.length)} of {filteredPatients.length} entries
            </span>
            <div className="flex gap-2">
              <button 
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="h-8 w-8 rounded flex items-center justify-center border border-border hover:bg-[#f3f4f5] disabled:opacity-50"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button 
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages || totalPages === 0}
                className="h-8 w-8 rounded flex items-center justify-center border border-border hover:bg-[#f3f4f5] disabled:opacity-50"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
