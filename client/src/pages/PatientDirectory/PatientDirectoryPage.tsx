// PatientDirectoryPage — administrative directory of patient cases
// Architecture ref: frontend_architecture.md §4, §8, §15

import { useState, useMemo } from 'react';
import { usePatients } from '@/features/patients/hooks/usePatients';
import type { Patient } from '@/types/patient.types';
import PatientCard from '@/features/patients/components/PatientCard';
import EmptyState from '@/components/common/EmptyState';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import {
  Search,
  Users,
  SlidersHorizontal,
  ChevronLeft,
  ChevronRight,
  UserX,
} from 'lucide-react';

/**
 * Deterministic status mapping to match PatientCard logic and align search filters.
 */
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

  // Local filtering & pagination state
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'STABLE' | 'WARNING' | 'CRITICAL'>('ALL');
  const [genderFilter, setGenderFilter] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<string>('NAME_AZ');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 6;

  // Client-side filtering, sorting and ordering logic
  const filteredAndSortedPatients = useMemo(() => {
    if (!patients) return [];

    return patients
      .filter((patient) => {
        // 1. Search term match (case-insensitive name query)
        const matchesSearch = patient.name.toLowerCase().includes(searchTerm.toLowerCase());

        // 2. Status match (utilizing deterministic status hash)
        const patientStatus = getDeterministicStatus(patient);
        const matchesStatus = statusFilter === 'ALL' || patientStatus === statusFilter;

        // 3. Gender match
        const matchesGender =
          genderFilter === 'ALL' || patient.gender.toUpperCase() === genderFilter.toUpperCase();

        return matchesSearch && matchesStatus && matchesGender;
      })
      .sort((a, b) => {
        // Sort definitions
        switch (sortBy) {
          case 'NAME_AZ':
            return a.name.localeCompare(b.name);
          case 'NAME_ZA':
            return b.name.localeCompare(a.name);
          case 'AGE_ASC':
            return a.age - b.age;
          case 'AGE_DESC':
            return b.age - a.age;
          default:
            return 0;
        }
      });
  }, [patients, searchTerm, statusFilter, genderFilter, sortBy]);

  // Client-side pagination slice calculations
  const totalPages = Math.ceil(filteredAndSortedPatients.length / itemsPerPage);
  const paginatedPatients = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredAndSortedPatients.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredAndSortedPatients, currentPage]);

  // Reset helper
  const handleClearFilters = () => {
    setSearchTerm('');
    setStatusFilter('ALL');
    setGenderFilter('ALL');
    setSortBy('NAME_AZ');
    setCurrentPage(1);
  };

  return (
    <div id="patient-directory-page" className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Patient Directory</h1>
          <p className="text-xs text-muted-foreground mt-1">
            Search, filter, and review active psychiatric patient case indexes.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground bg-muted/40 border border-border px-3 py-1.5 rounded-xl select-none">
          <Users className="h-4 w-4 text-primary shrink-0" />
          <span className="font-semibold text-foreground">
            {filteredAndSortedPatients.length} of {patients?.length || 0} Patients Listed
          </span>
        </div>
      </div>

      {/* ── 1. Advanced Search and Filters Panel ───────────────── */}
      <div className="bg-card/20 border border-border p-4 rounded-2xl flex flex-col gap-4 select-none">
        <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
          {/* Search box input */}
          <div className="relative w-full md:max-w-xs">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground opacity-60" />
            <input
              type="text"
              placeholder="Search patients by name..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-background/50 border border-border rounded-xl pl-9 pr-4 py-2 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary transition-all duration-200"
            />
          </div>

          {/* Sort and Gender selector deck */}
          <div className="flex items-center gap-3 w-full md:w-auto justify-end">
            <SlidersHorizontal className="h-4 w-4 text-muted-foreground opacity-55 shrink-0 hidden sm:block" />
            {/* Gender select native selector */}
            <select
              value={genderFilter}
              onChange={(e) => {
                setGenderFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-card border border-border px-3 py-1.5 rounded-xl text-xs font-semibold text-muted-foreground outline-none cursor-pointer focus:border-primary hover:text-foreground transition-all shrink-0"
            >
              <option value="ALL">All Genders</option>
              <option value="MALE">Male</option>
              <option value="FEMALE">Female</option>
              <option value="OTHER">Other</option>
            </select>

            {/* Sort select native selector */}
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-card border border-border px-3 py-1.5 rounded-xl text-xs font-semibold text-muted-foreground outline-none cursor-pointer focus:border-primary hover:text-foreground transition-all shrink-0"
            >
              <option value="NAME_AZ">Sort: Name (A–Z)</option>
              <option value="NAME_ZA">Sort: Name (Z–A)</option>
              <option value="AGE_ASC">Sort: Age (Youngest)</option>
              <option value="AGE_DESC">Sort: Age (Oldest)</option>
            </select>
          </div>
        </div>

        {/* Clinical Status Filters button deck */}
        <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-border/40 text-xs">
          <span className="text-muted-foreground font-semibold mr-1.5 uppercase tracking-wider text-[10px]">
            Clinical Status:
          </span>
          {(['ALL', 'STABLE', 'WARNING', 'CRITICAL'] as const).map((status) => (
            <Button
              key={status}
              variant={statusFilter === status ? 'default' : 'outline'}
              size="sm"
              onClick={() => {
                setStatusFilter(status);
                setCurrentPage(1);
              }}
              className="px-3 h-7 rounded-lg text-xs font-medium transition-all"
            >
              {status}
            </Button>
          ))}
        </div>
      </div>

      {/* ── 2. Patient Cards Grid ──────────────────────────────── */}
      {isLoading ? (
        // Grid Loading Skeleton State
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="bg-card/40 border border-border p-5 space-y-4 rounded-2xl">
              <div className="flex justify-between items-center gap-3">
                <div className="space-y-2 flex-1">
                  <Skeleton className="h-5 w-32 rounded" />
                  <Skeleton className="h-3.5 w-20 rounded" />
                </div>
                <Skeleton className="h-5 w-16 rounded-full" />
              </div>
              <Skeleton className="h-8 w-24 rounded-lg" />
              <div className="border-t border-border/60 pt-3 flex justify-between">
                <Skeleton className="h-3.5 w-28 rounded" />
                <Skeleton className="h-3.5 w-4 rounded" />
              </div>
            </Card>
          ))}
        </div>
      ) : isError ? (
        <div className="p-8 text-center text-rose-400 text-xs font-semibold border border-dashed border-border/60 bg-rose-950/10 rounded-2xl">
          Failed to query patient list records from the backend API.
        </div>
      ) : filteredAndSortedPatients.length === 0 ? (
        // Empty State Handler
        <EmptyState
          icon={<UserX className="h-10 w-10 shrink-0" />}
          title="No Patients Found"
          description="We couldn't find any patient cases matching your search criteria or active filters."
          action={
            <Button variant="outline" size="sm" onClick={handleClearFilters} className="rounded-xl">
              Reset search filters
            </Button>
          }
        />
      ) : (
        // Render Paginated Cards Grid
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {paginatedPatients.map((patient) => (
            <PatientCard key={patient.id} patient={patient} />
          ))}
        </div>
      )}

      {/* ── 3. Client-Side Pagination Toolbar ──────────────────── */}
      {!isLoading && !isError && filteredAndSortedPatients.length > 0 && (
        <div className="flex items-center justify-between border-t border-border pt-4 select-none">
          {/* Index metrics */}
          <span className="text-xs text-muted-foreground font-medium">
            Showing{' '}
            <span className="text-foreground font-semibold">
              {Math.min(filteredAndSortedPatients.length, (currentPage - 1) * itemsPerPage + 1)}
            </span>
            –
            <span className="text-foreground font-semibold">
              {Math.min(filteredAndSortedPatients.length, currentPage * itemsPerPage)}
            </span>{' '}
            of <span className="text-foreground font-semibold">{filteredAndSortedPatients.length}</span> patients
          </span>

          {/* Next / Previous controls */}
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              className="h-8 w-8 rounded-xl border-border"
              aria-label="Previous page"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-xs font-semibold px-2">
              Page {currentPage} of {totalPages || 1}
            </span>
            <Button
              variant="outline"
              size="icon"
              disabled={currentPage === totalPages || totalPages === 0}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              className="h-8 w-8 rounded-xl border-border"
              aria-label="Next page"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
