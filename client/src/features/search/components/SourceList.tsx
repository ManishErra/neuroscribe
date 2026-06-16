import type { SourceChunk } from '../types/search.types';
import SourceCard from './SourceCard';
import { cn } from '@/lib/utils';

interface SourceListProps {
  chunks: SourceChunk[];
  isCompact?: boolean;
}

export default function SourceList({ chunks, isCompact }: SourceListProps) {
  if (!chunks || chunks.length === 0) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between px-1 select-none">
        <h3 className={cn('font-bold text-foreground/80 tracking-wide uppercase', isCompact ? 'text-[10px]' : 'text-xs')}>
          Matched Clinical Reference Sources ({chunks.length})
        </h3>
      </div>
      <div className={cn('grid grid-cols-1 gap-3', isCompact && 'gap-2')}>
        {chunks.map((chunk) => (
          <SourceCard
            key={`${chunk.report_id}-${chunk.chunk_index}`}
            chunk={chunk}
            isCompact={isCompact}
          />
        ))}
      </div>
    </div>
  );
}
