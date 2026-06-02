// PageShell — persistent app shell for all authenticated routes.
// Renders Sidebar + TopBar + <Outlet> (child route content).
// Architecture ref: frontend_architecture.md §8 (PageShell)
// Instantiated exactly once at the router root — never duplicated inside pages.

import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function PageShell() {
  return (
    <div id="page-shell" className="flex min-h-screen bg-background text-foreground">
      {/* ── Left sidebar ─────────────────────────────────────── */}
      <Sidebar />

      {/* ── Main content area ────────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar />

        <main id="page-content" className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
