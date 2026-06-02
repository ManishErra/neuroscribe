// Application entry point — mounts the full provider stack.
// Architecture ref: frontend_architecture.md §6.1, §8
//
// Provider order (outermost first):
//   QueryClientProvider → AuthProvider → AppContextProvider → RouterProvider (inside App)

import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/auth/AuthContext';
import { AppContextProvider } from '@/store/AppContext';
import App from './App';
import './index.css';

// ── TanStack Query client ─────────────────────────────────────────────────────
// Architecture ref: frontend_architecture.md §6.1
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,   // 5 minutes — clinical data doesn't change every second
      gcTime:    1000 * 60 * 10,  // 10 minutes — keep inactive cache alive
      retry: 1,                    // one retry on network error
      refetchOnWindowFocus: false, // clinical UI — avoid surprise refetches
    },
  },
});

// ── Mount ─────────────────────────────────────────────────────────────────────
const rootElement = document.getElementById('root');
if (!rootElement) throw new Error('Root element not found — check index.html');

createRoot(rootElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AppContextProvider>
          <App />
        </AppContextProvider>
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>
);
