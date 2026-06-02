// Auth context — manages user identity and authentication state.
// Architecture ref: frontend_architecture.md §10.2
//
// VITE_AUTH_ENABLED=false → bypasses all auth checks (dev mode).
// VITE_AUTH_ENABLED=true  → full JWT auth flow.

import { createContext, useContext, useReducer, useEffect, type ReactNode } from 'react';
import { getCurrentUser, loginService, logoutService } from './authService';

export interface AuthUser {
  id: string;
  email: string;
  name: string;
}

interface AuthState {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

type AuthAction =
  | { type: 'SET_USER'; payload: AuthUser | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'CLEAR_USER' };

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_USER':
      return { ...state, user: action.payload, isAuthenticated: !!action.payload, isLoading: false };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'CLEAR_USER':
      return { user: null, isAuthenticated: false, isLoading: false };
    default:
      return state;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const authEnabled = import.meta.env.VITE_AUTH_ENABLED !== 'false';

  const [state, dispatch] = useReducer(authReducer, {
    user: null,
    // If auth is disabled, treat as immediately authenticated
    isAuthenticated: !authEnabled,
    isLoading: authEnabled,
  });

  useEffect(() => {
    if (!authEnabled) return; // bypass — already marked authenticated above

    // On mount: check stored token and restore session without a network call
    const user = getCurrentUser();
    dispatch({ type: 'SET_USER', payload: user });
  }, [authEnabled]);

  async function login(email: string, password: string) {
    const user = await loginService(email, password);
    dispatch({ type: 'SET_USER', payload: user });
  }

  function logout() {
    logoutService();
    dispatch({ type: 'CLEAR_USER' });
  }

  return (
    <AuthContext.Provider value={{ ...state, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuthContext must be used within AuthProvider');
  return ctx;
}
