import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Search, CornerDownLeft, Sparkles, AlertTriangle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SearchBoxProps {
  onSearch: (query: string) => void;
  isPending: boolean;
  aiRagEnabled: boolean;
  isCompact?: boolean;
}

export default function SearchBox({ onSearch, isPending, aiRagEnabled, isCompact }: SearchBoxProps) {
  const [query, setQuery] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (isPending || !aiRagEnabled || !query.trim()) return;
    onSearch(query);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Auto-resize textarea height as text flows
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [query]);

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div
        className={cn(
          'relative flex items-end gap-2 border border-border bg-card/10 backdrop-blur-md rounded-xl transition-all duration-200',
          'focus-within:border-purple-500/50 focus-within:ring-1 focus-within:ring-purple-500/30',
          isCompact ? 'p-2' : 'p-3',
          !aiRagEnabled && 'opacity-60 cursor-not-allowed bg-muted/5'
        )}
      >
        <div className={cn('flex items-center justify-center text-muted-foreground shrink-0', isCompact ? 'h-7 w-7' : 'h-8 w-8')}>
          {aiRagEnabled ? (
            <Sparkles className={cn('text-purple-400', isCompact ? 'h-4.5 w-4.5' : 'h-5 w-5')} />
          ) : (
            <AlertTriangle className={cn('text-amber-500', isCompact ? 'h-4.5 w-4.5' : 'h-5 w-5')} />
          )}
        </div>

        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            aiRagEnabled
              ? "Ask a clinical question (e.g. 'What was Radhika Erra's hemoglobin trend?')"
              : "RAG search is disabled. Enable it under Settings to query."
          }
          disabled={isPending || !aiRagEnabled}
          rows={1}
          className={cn(
            'flex-1 min-h-[24px] max-h-[160px] resize-none bg-transparent border-0 ring-0 outline-none p-1 text-sm text-foreground placeholder:text-muted-foreground/60',
            isCompact ? 'text-xs' : 'text-sm'
          )}
        />

        <div className="flex items-center gap-1.5 shrink-0 select-none pb-0.5">
          {query.trim() && aiRagEnabled && !isPending && (
            <span className="text-[10px] text-muted-foreground/50 font-mono hidden sm:flex items-center gap-0.5 mr-1">
              <span>Enter</span>
              <CornerDownLeft className="h-2.5 w-2.5" />
            </span>
          )}
          <Button
            type="submit"
            disabled={isPending || !aiRagEnabled || !query.trim()}
            variant="default"
            size={isCompact ? 'icon-sm' : 'icon'}
            className={cn(
              'flex items-center justify-center rounded-lg border-none shadow-sm transition-all',
              aiRagEnabled && query.trim() && !isPending
                ? 'bg-purple-600 hover:bg-purple-500 text-white'
                : 'bg-muted text-muted-foreground opacity-50'
            )}
          >
            <Search className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </form>
  );
}
