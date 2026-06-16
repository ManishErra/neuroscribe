import { useEffect } from 'react';
import { useSettings } from '@/store/SettingsContext';
import { useAsk } from '@/features/search/hooks/useAsk';
import SearchBox from '@/features/search/components/SearchBox';
import AnswerPanel from '@/features/search/components/AnswerPanel';
import SourceList from '@/features/search/components/SourceList';
import { PAGE_TITLES } from '@/utils/constants';
import { cn } from '@/lib/utils';
import { FileSearch } from 'lucide-react';

export default function SearchPage() {
  const { settings } = useSettings();
  const { mutate, data, isPending, error } = useAsk();

  const isCompact = settings.density === 'compact';

  // Set document title on page mount
  useEffect(() => {
    document.title = PAGE_TITLES.search;
  }, []);

  const handleSearch = (query: string) => {
    mutate(query);
  };

  return (
    <div
      id="search-page"
      className={cn(
        'bg-background text-foreground select-none max-w-4xl mx-auto transition-all duration-200',
        isCompact ? 'p-4 space-y-4' : 'p-6 space-y-6'
      )}
    >
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className={cn('flex flex-col gap-1 border-b border-border', isCompact ? 'pb-3' : 'pb-5')}>
        <div className="flex items-center gap-2">
          <FileSearch className={cn('text-purple-400 shrink-0', isCompact ? 'h-5 w-5' : 'h-6 w-6')} />
          <h1 className={cn('font-bold tracking-tight text-foreground', isCompact ? 'text-xl' : 'text-2xl')}>
            Semantic Search Hub
          </h1>
        </div>
        <p className="text-xs text-muted-foreground mt-0.5">
          Ask questions or extract structured metrics from medical reports using Clinical RAG retrieval.
        </p>
      </div>

      {/* ── Search Input Area ──────────────────────────────────── */}
      <SearchBox
        onSearch={handleSearch}
        isPending={isPending}
        aiRagEnabled={settings.aiRagEnabled}
        isCompact={isCompact}
      />

      {/* ── Answer & Synthesis Panel ───────────────────────────── */}
      <AnswerPanel
        data={data}
        isPending={isPending}
        error={error}
        aiConfidenceLabels={settings.aiConfidenceLabels}
        aiRagEnabled={settings.aiRagEnabled}
        isCompact={isCompact}
      />

      {/* ── Source Attribution Area ───────────────────────────── */}
      {data && !isPending && !error && (
        <div className={cn('pt-4 border-t border-border/40', isCompact && 'pt-2')}>
          <SourceList
            chunks={data.chunks_used}
            isCompact={isCompact}
          />
        </div>
      )}
    </div>
  );
}
