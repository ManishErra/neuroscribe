// Loading spinner — wraps Lucide Loader2 with animate-spin.
// Architecture ref: frontend_architecture.md §11.2 (components/common/Spinner)

import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeMap = {
  sm: 'h-4 w-4',
  md: 'h-6 w-6',
  lg: 'h-8 w-8',
};

export default function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <Loader2
      className={cn('animate-spin text-muted-foreground', sizeMap[size], className)}
      aria-label="Loading"
    />
  );
}
