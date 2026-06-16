import type { AskResponse } from '../types/search.types';
import { isStructuredAnswer, isStructuredAnswerArray } from '../types/search.types';
import LabAnswerCard from './LabAnswerCard';
import EmptyState from '@/components/common/EmptyState';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { Sparkles, AlertCircle, FileSearch, ShieldAlert, BookOpen } from 'lucide-react';

interface AnswerPanelProps {
  data: AskResponse | null | undefined;
  isPending: boolean;
  error: Error | null;
  aiConfidenceLabels: boolean;
  aiRagEnabled: boolean;
  isCompact?: boolean;
}

export default function AnswerPanel({
  data,
  isPending,
  error,
  aiConfidenceLabels,
  aiRagEnabled,
  isCompact,
}: AnswerPanelProps) {
  
  // 1. RAG disabled state
  if (!aiRagEnabled) {
    return (
      <EmptyState
        icon={<ShieldAlert className="h-10 w-10 text-amber-500" />}
        title="Clinical RAG Engine Disabled"
        description="To perform semantic searches and ask questions about report archives, enable 'RAG Retrieval' in settings."
        className="py-12"
      />
    );
  }

  // 2. Loading state
  if (isPending) {
    return (
      <div className={cn('border border-border bg-card/10 rounded-xl space-y-4', isCompact ? 'p-4' : 'p-6')}>
        <div className="flex items-center gap-3 border-b border-border/40 pb-3">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-4 w-12 ml-auto" />
        </div>
        <div className="space-y-2">
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-5/6" />
        </div>
        <div className="border-t border-border/30 pt-3 flex items-center gap-3">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-3 w-24 ml-auto" />
        </div>
      </div>
    );
  }

  // 3. Request error state
  if (error) {
    return (
      <div className="flex items-start gap-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 p-4 rounded-xl">
        <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
        <div className="space-y-1 select-text">
          <span className="text-sm font-semibold">Search Failure</span>
          <p className="text-xs opacity-90">{error.message || 'An unexpected retrieval error occurred.'}</p>
        </div>
      </div>
    );
  }

  // 4. Idle state (no search performed yet)
  if (!data) {
    return (
      <EmptyState
        icon={<FileSearch className="h-10 w-10 text-purple-400" />}
        title="Clinical Knowledge Q&A"
        description="Query lab results, summaries, and patient diagnostics extracted across all medical reports."
        className="py-16"
      />
    );
  }

  // 5. Inspect polymorphic answer field
  const answer = data.answer;

  // 5a. Backend returned error/failure status in answer string
  if (typeof answer === 'string' && answer.startsWith('LLM generation failed:')) {
    return (
      <div className="flex items-start gap-3 bg-amber-500/10 border border-amber-500/20 text-amber-400 p-4 rounded-xl">
        <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
        <div className="space-y-1 select-text">
          <span className="text-sm font-semibold">Synthesis Error</span>
          <p className="text-xs opacity-90">
            The database successfully retrieved relevant clinical sources, but the text generation engine was offline or failed to generate a summary.
          </p>
          <p className="text-[10px] opacity-75 font-mono bg-amber-950/20 px-2 py-1 rounded border border-amber-500/10 mt-2">
            {answer}
          </p>
        </div>
      </div>
    );
  }

  // 5b. Backend returned no-results explanation in answer string
  if (typeof answer === 'string' && answer === 'No relevant medical context found.') {
    return (
      <EmptyState
        icon={<AlertCircle className="h-10 w-10 text-muted-foreground opacity-50" />}
        title="No Context Found"
        description="Your query did not match any clinical records in the database. Try adjusting your query keywords."
        className="py-12"
      />
    );
  }

  // 5c. Render StructuredAnswer (Single Card)
  if (isStructuredAnswer(answer)) {
    return (
      <LabAnswerCard
        answer={answer}
        aiConfidenceLabels={aiConfidenceLabels}
        isCompact={isCompact}
      />
    );
  }

  // 5d. Render StructuredAnswer[] (List of Cards)
  if (isStructuredAnswerArray(answer)) {
    return (
      <div className={cn('grid grid-cols-1 gap-4', isCompact && 'gap-3')}>
        {answer.map((item, idx) => (
          <LabAnswerCard
            key={`${item.test}-${idx}`}
            answer={item}
            aiConfidenceLabels={aiConfidenceLabels}
            isCompact={isCompact}
          />
        ))}
      </div>
    );
  }

  // 5e. Render Prose String Answer
  if (typeof answer === 'string') {
    return (
      <div
        className={cn(
          'border border-border bg-card/15 rounded-xl relative overflow-hidden backdrop-blur-sm shadow-md',
          isCompact ? 'p-4' : 'p-5'
        )}
      >
        <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/5 rounded-full blur-2xl pointer-events-none select-none" />

        <div className="flex items-center gap-2 border-b border-border/40 pb-2.5 mb-3 select-none">
          <BookOpen className="h-4 w-4 text-purple-400 shrink-0" />
          <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
            Clinical Synthesis
          </span>
        </div>

        <div className="text-foreground leading-relaxed select-text font-normal whitespace-pre-wrap">
          <p className={isCompact ? 'text-xs' : 'text-sm'}>
            {answer}
          </p>
        </div>

        <div className="border-t border-border/30 pt-2.5 mt-4 flex items-center justify-between text-[10px] text-muted-foreground select-none">
          <div className="flex items-center gap-1">
            <Sparkles className="h-3 w-3 text-purple-400" />
            <span>AI Generated Prose Summary</span>
          </div>
        </div>
      </div>
    );
  }

  // Fallback for unexpected payloads
  return (
    <div className="flex items-start gap-3 bg-amber-500/10 border border-amber-500/20 text-amber-400 p-4 rounded-xl">
      <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
      <div className="space-y-1 select-text">
        <span className="text-sm font-semibold">Unexpected Data Format</span>
        <p className="text-xs opacity-90">Received search payload that cannot be formatted cleanly.</p>
      </div>
    </div>
  );
}
