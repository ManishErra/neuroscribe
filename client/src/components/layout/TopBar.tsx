// TopBar — persistent top navigation bar. Shows breadcrumb and search shortcut.
// Architecture ref: frontend_architecture.md §8 (TopBar)

import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Search, Calendar } from 'lucide-react';

function buildBreadcrumb(pathname: string): string {
  const parts = pathname.split('/').filter(Boolean);
  if (parts.length === 0) return 'Dashboard';

  const mappedParts = parts.map((part) => {
    // If it's a UUID (patientId / sessionId), map to static reference label
    if (part.length === 36 && part.includes('-')) {
      return 'Profile';
    }

    // Standard static mappings
    switch (part.toLowerCase()) {
      case 'patients':
        return 'Patients';
      case 'search':
        return 'Search';
      case 'settings':
        return 'Settings';
      case 'overview':
        return 'Overview';
      case 'sessions':
        return 'Sessions';
      case 'reports':
        return 'Reports';
      case 'insights':
        return 'Insights';
      case 'timeline':
        return 'Timeline';
      default:
        return part.charAt(0).toUpperCase() + part.slice(1);
    }
  });

  return ['Dashboard', ...mappedParts.filter(p => p !== 'Dashboard')].join('  /  ');
}

export default function TopBar() {
  const location = useLocation();
  const navigate = useNavigate();
  const breadcrumb = buildBreadcrumb(location.pathname);

  // Get active date for header display
  const today = new Date();
  const formattedDate = today.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  // Capture "/" hotkey press to trigger immediate route navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Avoid firing hotkeys when user is actively inside input fields
      if (
        document.activeElement?.tagName === 'INPUT' ||
        document.activeElement?.tagName === 'TEXTAREA'
      ) {
        return;
      }
      if (e.key === '/') {
        e.preventDefault();
        navigate('/search');
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [navigate]);

  return (
    <header
      id="topbar"
      className="sticky top-0 z-40 flex items-center justify-between h-14 px-6 bg-background/80 backdrop-blur-sm border-b border-border select-none"
    >
      {/* ── Dynamic Breadcrumb Routing ────────────────────────── */}
      <nav aria-label="Breadcrumb">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1">
          {breadcrumb}
        </p>
      </nav>

      {/* ── Search shortcut and Date Picker ────────────────────── */}
      <div className="flex items-center gap-4">
        {/* Date tracker banner */}
        <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground border-r border-border pr-4 h-5 select-none">
          <Calendar className="h-3.5 w-3.5" />
          <span>{formattedDate}</span>
        </div>

        {/* Global search launcher */}
        <button
          id="topbar-search"
          onClick={() => navigate('/search')}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-border bg-muted/40 text-xs text-muted-foreground hover:bg-accent/40 hover:text-foreground transition-all duration-200"
          aria-label="Open semantic search"
        >
          <Search className="h-3.5 w-3.5" />
          <span>Search patients…</span>
          <kbd className="ml-1 text-[9px] font-mono bg-background border border-border px-1 rounded opacity-60">/</kbd>
        </button>
      </div>
    </header>
  );
}
