// Date, unit, and number formatters shared across the app.
// Architecture ref: frontend_architecture.md §1 (utils/formatters.js)

export function formatDate(isoString: string): string {
  if (!isoString) return '—';
  return new Date(isoString).toLocaleDateString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  });
}

export function formatUnit(value: string | number | null | undefined, unit: string): string {
  if (value === null || value === undefined || value === '') return '—';
  return `${value} ${unit}`;
}

export function formatNumber(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined) return '—';
  return value.toFixed(decimals);
}
