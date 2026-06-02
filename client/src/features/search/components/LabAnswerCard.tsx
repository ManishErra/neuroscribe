import { useState } from 'react';
import type { StructuredAnswer } from '../types/search.types';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { ChevronDown, ChevronUp, Sparkles, CheckCircle2 } from 'lucide-react';

interface LabAnswerCardProps {
  answer: StructuredAnswer;
  aiConfidenceLabels: boolean;
  isCompact?: boolean;
}

export default function LabAnswerCard({ answer, aiConfidenceLabels, isCompact }: LabAnswerCardProps) {
  const [showReasons, setShowReasons] = useState(false);

  // Normalize status
  const rawStatus = answer.status || 'STABLE';
  const displayStatus = rawStatus.toUpperCase();

  // Confidence styling mapping
  const confidenceColor = {
    HIGH: 'bg-emerald-950/30 text-emerald-400 border-emerald-500/20',
    MEDIUM: 'bg-amber-950/30 text-amber-400 border-amber-500/20',
    LOW: 'bg-rose-950/30 text-rose-400 border-rose-500/20',
  }[answer.confidence_label || 'MEDIUM'];

  const confidenceScore = answer.confidence ? Math.round(answer.confidence * 100) : null;

  return (
    <div
      className={cn(
        'border border-border bg-card/25 rounded-xl shadow-md relative overflow-hidden backdrop-blur-sm transition-all',
        isCompact ? 'p-4' : 'p-5'
      )}
    >
      {/* Decorative ambient gradient backdrop */}
      <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/5 rounded-full blur-2xl pointer-events-none select-none" />

      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border/40 pb-3 mb-4 select-none">
        <div>
          <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
            Structured Extraction
          </span>
          <h2 className={cn('font-bold text-foreground capitalize mt-0.5', isCompact ? 'text-sm' : 'text-base')}>
            {answer.test} Measurement
          </h2>
        </div>
        <div className="flex items-center gap-2">
          {/* Clinical Alert Status Badge */}
          <StatusBadge status={displayStatus} />
        </div>
      </div>

      {/* Large value display */}
      <div className="flex items-baseline gap-2 mb-4 select-text">
        <span className={cn('font-bold text-foreground tracking-tight', isCompact ? 'text-2xl' : 'text-3xl')}>
          {answer.value}
        </span>
        {answer.unit && (
          <span className="text-muted-foreground text-sm font-medium">
            {answer.unit}
          </span>
        )}
      </div>

      {/* Confidence score details */}
      {aiConfidenceLabels && answer.confidence_label && (
        <div className="border-t border-border/30 pt-3 mt-3">
          <div className="flex items-center justify-between gap-3 select-none flex-wrap">
            <div className="flex items-center gap-2">
              <Sparkles className="h-3.5 w-3.5 text-purple-400" />
              <span className="text-xs font-semibold text-foreground/90">
                Confidence Rating:
              </span>
              <Badge variant="outline" className={cn('text-[10px] font-mono px-2 py-0.5 rounded-md', confidenceColor)}>
                {answer.confidence_label} {confidenceScore !== null && `(${confidenceScore}%)`}
              </Badge>
            </div>

            {answer.confidence_reason && answer.confidence_reason.length > 0 && (
              <button
                onClick={() => setShowReasons(!showReasons)}
                className="text-[10px] text-purple-400 hover:underline flex items-center gap-0.5 focus:outline-none"
              >
                <span>{showReasons ? 'Hide Breakdown' : 'Show Breakdown'}</span>
                {showReasons ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </button>
            )}
          </div>

          {/* Collapsible breakdown reasons and component weights */}
          {showReasons && answer.confidence_reason && (
            <div className="mt-3 bg-muted/10 border border-border/40 p-3 rounded-lg space-y-3">
              <div>
                <span className="text-[9px] uppercase font-bold text-muted-foreground tracking-wider block mb-1.5 select-none">
                  Confidence Attribution Reasons
                </span>
                <ul className="space-y-1.5 text-xs">
                  {answer.confidence_reason.map((reason, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-muted-foreground select-text">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500/70 shrink-0 mt-0.5" />
                      <span>{reason}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {answer.confidence_breakdown && (
                <div className="pt-2 border-t border-border/30 select-none">
                  <span className="text-[9px] uppercase font-bold text-muted-foreground tracking-wider block mb-2">
                    Attribution Weights
                  </span>
                  <div className="grid grid-cols-3 gap-2 text-center text-[10px] font-mono">
                    <div className="bg-muted/30 p-1.5 rounded border border-border/20">
                      <span className="block text-muted-foreground text-[8px] mb-0.5">Retrieval</span>
                      <span className="text-foreground font-semibold">
                        {Math.round(answer.confidence_breakdown.retrieval_component * 100)}%
                      </span>
                    </div>
                    <div className="bg-muted/30 p-1.5 rounded border border-border/20">
                      <span className="block text-muted-foreground text-[8px] mb-0.5">Extraction</span>
                      <span className="text-foreground font-semibold">
                        {Math.round(answer.confidence_breakdown.extraction_component * 100)}%
                      </span>
                    </div>
                    <div className="bg-muted/30 p-1.5 rounded border border-border/20">
                      <span className="block text-muted-foreground text-[8px] mb-0.5">Direct Match</span>
                      <span className="text-foreground font-semibold">
                        {Math.round(answer.confidence_breakdown.direct_match_component * 100)}%
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
