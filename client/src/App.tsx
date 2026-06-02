// Root router definition — full route tree for NeuroScribe.
// Architecture ref: frontend_architecture.md §4
//
// All routes except /login are wrapped in ProtectedRoute → PageShell.
// Nested patient profile tabs mount inside PatientProfilePage's <Outlet>.

import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import ProtectedRoute from '@/auth/ProtectedRoute';
import LoginPage from '@/auth/LoginPage';
import PageShell from '@/components/layout/PageShell';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import DashboardPage from '@/pages/Dashboard/DashboardPage';
import PatientDirectoryPage from '@/pages/PatientDirectory/PatientDirectoryPage';
import PatientProfilePage from '@/pages/PatientProfile/PatientProfilePage';
import OverviewTab from '@/pages/PatientProfile/tabs/OverviewTab';
import SessionsTab from '@/pages/PatientProfile/tabs/SessionsTab';
import ReportsTab from '@/pages/PatientProfile/tabs/ReportsTab';
import SessionDetailPage from '@/pages/SessionDetail/SessionDetailPage';
import NotFoundPage from '@/pages/NotFound/NotFoundPage';

// ── Phase 2–6 stubs ──────────────────────────────────────────────────────────
// These placeholders will be replaced with real pages in their respective phases.
function ComingSoon({ label }: { label: string }) {
  return (
    <div className="p-6 text-sm text-muted-foreground">
      <span className="font-medium text-foreground">{label}</span>
      {' '}— implemented in a future phase.
    </div>
  );
}

const router = createBrowserRouter([
  // ── Public routes ────────────────────────────────────────────────────────
  {
    path: '/login',
    element: <LoginPage />,
  },

  // ── Protected routes — all inside PageShell ──────────────────────────────
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <PageShell />
      </ProtectedRoute>
    ),
    children: [
      // Dashboard
      {
        index: true,
        element: (
          <ErrorBoundary>
            <DashboardPage />
          </ErrorBoundary>
        ),
      },

      // Patient Directory (Day 27)
      {
        path: 'patients',
        element: (
          <ErrorBoundary>
            <PatientDirectoryPage />
          </ErrorBoundary>
        ),
      },

      // Patient Profile — tabbed layout (Phase 3)
      {
        path: 'patients/:patientId',
        element: (
          <ErrorBoundary>
            <PatientProfilePage />
          </ErrorBoundary>
        ),
        children: [
          { index: true,          element: <Navigate to="overview" replace /> },
          { path: 'overview',     element: <OverviewTab /> },
          { path: 'sessions',     element: <SessionsTab /> },
          { path: 'reports',      element: <ReportsTab /> },
          { path: 'insights',     element: <ComingSoon label="Insights Tab" /> },
          { path: 'timeline',     element: <ComingSoon label="Timeline Tab" /> },
        ],
      },

      // Session Detail (Phase 4)
      {
        path: 'patients/:patientId/sessions/:sessionId',
        element: (
          <ErrorBoundary>
            <SessionDetailPage />
          </ErrorBoundary>
        ),
      },

      // Semantic Search (Phase 6)
      {
        path: 'search',
        element: (
          <ErrorBoundary>
            <ComingSoon label="Semantic Search" />
          </ErrorBoundary>
        ),
      },

      // 404 fallback
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
