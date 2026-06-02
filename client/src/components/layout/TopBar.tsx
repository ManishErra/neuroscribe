// TopBar — persistent top navigation bar. Shows breadcrumb and search shortcut.
// Architecture ref: frontend_architecture.md §8 (TopBar)
// Phase 1: static shell. Breadcrumb and search wired in later phases.

import { useLocation } from 'react-router-dom';
import { Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

function buildBreadcrumb(pathname: string): string {
  const parts = pathname.split('/').filter(Boolean);
  if (parts.length === 0) return 'Dashboard';
  return parts
    .map((p) => (p.length === 36 && p.includes('-') ? '…' : p.charAt(0).toUpperCase() + p.slice(1)))
    .join(' › ');
}

export default function TopBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const breadcrumb = buildBreadcrumb(location.pathname);

  return (
    <header
      id="topbar"
      className="sticky top-0 z-40 flex items-center justify-between h-14 px-6 bg-background/80 backdrop-blur-sm border-b border-border"
    >
      {/* ── Breadcrumb ───────────────────────────────────────── */}
      <nav aria-label="Breadcrumb">
        <p className="text-sm font-medium text-foreground">{breadcrumb}</p>
      </nav>

      {/* ── Search shortcut ──────────────────────────────────── */}
      <button
        id="topbar-search"
        onClick={() => navigate('/search')}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-muted/40 text-xs text-muted-foreground hover:bg-accent/40 hover:text-foreground transition-colors"
        aria-label="Open semantic search"
      >
        <Search className="h-3.5 w-3.5" />
        <span>Search patients…</span>
        <kbd className="ml-1 text-[10px] font-mono bg-background border border-border px-1 rounded opacity-60">/</kbd>
      </button>
    </header>
  );
}
