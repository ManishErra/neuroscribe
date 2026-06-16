// Reusable StatusBadge primitive wrapping shadcn Badge.
// Architecture ref: frontend_architecture.md §11.2, §16.1

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export type ClinicalStatus = 'STABLE' | 'WARNING' | 'CRITICAL';

interface StatusBadgeProps {
  status: ClinicalStatus | string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const normStatus = (status || 'STABLE').toUpperCase() as ClinicalStatus;

  // Custom premium design colors mapping HSL variable layers
  const styles = {
    STABLE: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20',
    WARNING: 'bg-amber-500/10 text-amber-400 border-amber-500/20 hover:bg-amber-500/20',
    CRITICAL: 'bg-rose-500/10 text-rose-400 border-rose-500/20 hover:bg-rose-500/20',
  };

  const dotColors = {
    STABLE: 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]',
    WARNING: 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.5)]',
    CRITICAL: 'bg-rose-400 shadow-[0_0_8px_rgba(251,113,133,0.5)] animate-pulse',
  };

  const currentStyle = styles[normStatus] || styles.STABLE;
  const currentDot = dotColors[normStatus] || dotColors.STABLE;

  return (
    <Badge
      variant="outline"
      className={cn(
        'px-2.5 py-0.5 rounded-full text-[11px] font-semibold uppercase tracking-wider flex items-center gap-1.5 border w-fit select-none transition-all',
        currentStyle,
        className
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full shrink-0', currentDot)} />
      {normStatus}
    </Badge>
  );
}
