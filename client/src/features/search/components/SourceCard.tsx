import { useState } from 'react';
import type { SourceChunk } from '../types/search.types';
import { ChevronDown, ChevronUp, Database, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

interface SourceCardProps {
  chunk: SourceChunk;
  isCompact?: boolean;
}

export default function SourceCard({ chunk, isCompact }: SourceCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showTechDetails, setShowTechDetails] = useState(false);

  const confidencePct = Math.round(chunk.similarity_score * 100);

  // Shorten preview text for clinicians
  const previewText = chunk.chunk_text.slice(0, 180);
  const hasMoreText = chunk.chunk_text.length > 180;

  return (
    <div
      className={cn(
        'border border-border bg-card/5 rounded-xl transition-all duration-200 hover:bg-card/10',
        isCompact ? 'p-3' : 'p-4'
      )}
    >
      {/* Clinician-friendly header */}
      <div className="flex items-center justify-between gap-4 flex-wrap mb-2 select-none">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-purple-400 shrink-0" />
          <span className="text-xs font-semibold text-foreground">
            {chunk.report_source ? `Source: ${chunk.report_source.replace(/_/g, ' ')}` : 'Report Fragment'}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Badge
            variant="secondary"
            className={cn(
              'font-semibold border-none text-[10px] px-2 py-0.5',
              chunk.similarity_score >= 0.70
                ? 'bg-emerald-950/20 text-emerald-400'
                : chunk.similarity_score >= 0.50
                ? 'bg-amber-950/20 text-amber-400'
                : 'bg-rose-950/20 text-rose-400'
            )}
          >
            {confidencePct}% Match Confidence
          </Badge>
        </div>
      </div>

      {/* Source preview / full content */}
      <div className="text-muted-foreground leading-relaxed break-words mb-3 select-text">
        <p className={cn(isCompact ? 'text-[11px]' : 'text-xs')}>
          {isExpanded ? chunk.chunk_text : `${previewText}${hasMoreText ? '...' : ''}`}
        </p>
        {hasMoreText && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-[10px] text-purple-400 hover:underline font-semibold mt-1.5 flex items-center gap-0.5 transition-all focus:outline-none select-none"
          >
            {isExpanded ? (
              <>
                Show Less <ChevronUp className="h-3 w-3" />
              </>
            ) : (
              <>
                Show Full Text <ChevronDown className="h-3 w-3" />
              </>
            )}
          </button>
        )}
      </div>

      {/* Optional Technical Details Collapsible */}
      <div className="border-t border-border/40 pt-2 mt-2 select-none">
        <button
          onClick={() => setShowTechDetails(!showTechDetails)}
          className="text-[9px] text-muted-foreground/60 hover:text-muted-foreground flex items-center gap-1 font-mono transition-all focus:outline-none uppercase tracking-wider"
        >
          <Database className="h-3 w-3 text-muted-foreground/55" />
          <span>{showTechDetails ? 'Hide Technical Details' : 'Show Technical Details'}</span>
        </button>

        {showTechDetails && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 mt-2.5 bg-muted/10 p-2.5 rounded-lg border border-border/30 text-[10px] font-mono text-muted-foreground select-text">
            <div className="min-w-0">
              <span className="block opacity-65 text-[9px] mb-0.5">Report ID</span>
              <span className="text-[9px] text-foreground font-semibold truncate block" title={chunk.report_id}>
                {chunk.report_id}
              </span>
            </div>
            <div>
              <span className="block opacity-65 text-[9px] mb-0.5">Chunk Index</span>
              <span className="text-foreground font-semibold">{chunk.chunk_index}</span>
            </div>
            {chunk.chunk_length !== undefined && (
              <div>
                <span className="block opacity-65 text-[9px] mb-0.5">Char Length</span>
                <span className="text-foreground font-semibold">{chunk.chunk_length}</span>
              </div>
            )}
            {chunk.chunk_position !== undefined && (
              <div>
                <span className="block opacity-65 text-[9px] mb-0.5">Char Position</span>
                <span className="text-foreground font-semibold">{chunk.chunk_position}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
