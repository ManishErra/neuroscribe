// PageShell — persistent app shell for all authenticated routes.
// Renders Sidebar + TopBar + <Outlet> (child route content).
// Architecture ref: frontend_architecture.md §8 (PageShell)
// Instantiated exactly once at the router root — never duplicated inside pages.

import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import { useAppContext } from '@/store/AppContext';
import { POP_TOAST } from '@/store/actions';
import { cn } from '@/lib/utils';
import { X, CheckCircle2, AlertCircle, Info } from 'lucide-react';

export default function PageShell() {
  const { state, dispatch } = useAppContext();
  const { toasts } = state;

  const handleDismiss = (id: string) => {
    dispatch({ type: POP_TOAST, payload: id });
  };

  return (
    <div id="page-shell" className="flex min-h-screen bg-background text-foreground select-none relative">
      {/* ── Left sidebar ─────────────────────────────────────── */}
      <Sidebar />

      {/* ── Main content area ────────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar />

        <main id="page-content" className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>

      {/* ── Global floating toast notification overlay ───────── */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={cn(
              'flex items-start gap-3 p-3.5 rounded-xl border shadow-xl backdrop-blur-md transition-all duration-300 animate-in fade-in slide-in-from-bottom-3',
              toast.type === 'success' && 'bg-emerald-950/40 border-emerald-500/20 text-emerald-400',
              toast.type === 'error' && 'bg-rose-950/40 border-rose-500/20 text-rose-400',
              toast.type === 'info' && 'bg-blue-950/40 border-blue-500/20 text-blue-400'
            )}
          >
            {toast.type === 'success' && <CheckCircle2 className="h-4.5 w-4.5 shrink-0 mt-0.5" />}
            {toast.type === 'error' && <AlertCircle className="h-4.5 w-4.5 shrink-0 mt-0.5" />}
            {toast.type === 'info' && <Info className="h-4.5 w-4.5 shrink-0 mt-0.5" />}

            <div className="flex-1 text-xs leading-normal">
              {toast.message}
            </div>

            <button
              onClick={() => handleDismiss(toast.id)}
              className="text-muted-foreground hover:text-foreground shrink-0 transition-colors"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
