// Route guard — redirects unauthenticated users to /login.
// Architecture ref: frontend_architecture.md §10.4
//
// VITE_AUTH_ENABLED=false → renders children unconditionally (dev bypass).
// VITE_AUTH_ENABLED=true  → shows Spinner while loading, redirects if !isAuthenticated.

import { Navigate } from 'react-router-dom';
import { useAuth } from './useAuth';
import Spinner from '@/components/common/Spinner';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const authEnabled = import.meta.env.VITE_AUTH_ENABLED !== 'false';

  // Always call hooks unconditionally — rules of hooks requirement
  const { isAuthenticated, isLoading } = useAuth();

  // Auth disabled — render children directly (development bypass)
  if (!authEnabled) return <>{children}</>;

  // Token validation in progress — show full-screen spinner to prevent login flash
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Spinner size="lg" />
      </div>
    );
  }

  // Not authenticated — redirect to login
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
