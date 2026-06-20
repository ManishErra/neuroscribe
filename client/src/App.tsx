// Root router definition — full route tree for NeuroScribe.
// Architecture ref: frontend_architecture.md §4
//
// All routes except /login are wrapped in ProtectedRoute → PageShell.
// Nested patient profile tabs mount inside PatientProfilePage's <Outlet>.

import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import ProtectedRoute from '@/auth/ProtectedRoute';
import LoginPage from '@/auth/LoginPage';
import RegisterPage from '@/auth/RegisterPage';
import PageShell from '@/components/layout/PageShell';
import ErrorBoundary from '@/components/common/ErrorBoundary';
import DashboardPage from '@/pages/Dashboard/DashboardPage';
import PatientDirectoryPage from '@/pages/PatientDirectory/PatientDirectoryPage';
import PatientProfilePage from '@/pages/PatientProfile/PatientProfilePage';
import OverviewTab from '@/pages/PatientProfile/tabs/OverviewTab';
import TimelineTab from '@/pages/PatientProfile/tabs/TimelineTab';
import SessionsTab from '@/pages/PatientProfile/tabs/SessionsTab';
import ReportsTab from '@/pages/PatientProfile/tabs/ReportsTab';
import AskTab from '@/pages/PatientProfile/tabs/AskTab';
import SessionDetailPage from '@/pages/SessionDetail/SessionDetailPage';
import SettingsPage from '@/pages/Settings/SettingsPage';

import NotFoundPage from '@/pages/NotFound/NotFoundPage';

// ── Phase 2–6 placeholders removed as functionality is complete ────────────

const router = createBrowserRouter([
  // ── Public routes ────────────────────────────────────────────────────────
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/register',
    element: <RegisterPage />,
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
          { index: true,          element: <Navigate to="timeline" replace /> },
          { path: 'timeline',     element: <TimelineTab /> },
          { path: 'overview',     element: <OverviewTab /> },
          { path: 'sessions',     element: <SessionsTab /> },
          { path: 'reports',      element: <ReportsTab /> },
          { path: 'ask',          element: <AskTab /> },
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


      // Settings (Day 31)
      {
        path: 'settings',
        element: (
          <ErrorBoundary>
            <SettingsPage />
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
