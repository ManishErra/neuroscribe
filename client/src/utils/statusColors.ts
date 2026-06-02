// Maps clinical status strings to Tailwind CSS class names.
// Architecture ref: frontend_architecture.md §1 (utils/statusColors.js)

type ClinicalStatus = 'STABLE' | 'WARNING' | 'CRITICAL';

export function getStatusColor(status: ClinicalStatus | string): string {
  switch (status) {
    case 'STABLE':   return 'text-stable bg-stable/10 border-stable/20';
    case 'WARNING':  return 'text-warning bg-warning/10 border-warning/20';
    case 'CRITICAL': return 'text-critical bg-critical/10 border-critical/20';
    default:         return 'text-muted-foreground bg-muted border-border';
  }
}

export function getStatusDot(status: ClinicalStatus | string): string {
  switch (status) {
    case 'STABLE':   return 'bg-stable';
    case 'WARNING':  return 'bg-warning';
    case 'CRITICAL': return 'bg-critical';
    default:         return 'bg-muted-foreground';
  }
}
