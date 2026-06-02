// Auth service — login, logout, and token decode utilities.
// Architecture ref: frontend_architecture.md §10.3
//
// NOTE: Backend auth endpoints (/auth/login, /auth/me) are not yet implemented.
// These functions are stubs. login() will throw until the backend is ready.
// Use VITE_AUTH_ENABLED=false during development to bypass the auth flow entirely.

import client from '@/api/axiosClient';
import type { AuthUser } from './AuthContext';

const TOKEN_KEY = 'ns_access_token';

interface LoginResponse {
  access_token: string;
  token_type: string;
}

/** POST /auth/login — exchanges credentials for a JWT. */
export async function loginService(email: string, password: string): Promise<AuthUser> {
  const response = await client.post<LoginResponse>('/auth/login', { email, password });
  const { access_token } = response as unknown as LoginResponse;
  localStorage.setItem(TOKEN_KEY, access_token);
  const user = decodeToken(access_token);
  if (!user) throw new Error('Invalid token received from server');
  return user;
}

/** Removes the stored token and clears the auth session. No server call needed for JWT. */
export function logoutService(): void {
  localStorage.removeItem(TOKEN_KEY);
}

/** Decodes the stored JWT and returns the user payload synchronously.
 *  Returns null if no token or token is expired. */
export function getCurrentUser(): AuthUser | null {
  const token = localStorage.getItem(TOKEN_KEY);
  if (!token) return null;
  return decodeToken(token);
}

/** Minimal JWT payload decoder — does not verify signature (client-side only). */
function decodeToken(token: string): AuthUser | null {
  try {
    const payloadBase64 = token.split('.')[1];
    const payload = JSON.parse(atob(payloadBase64));
    // Check expiry
    if (payload.exp && Date.now() / 1000 > payload.exp) {
      localStorage.removeItem(TOKEN_KEY);
      return null;
    }
    return {
      id:    payload.sub ?? payload.id ?? '',
      email: payload.email ?? '',
      name:  payload.name ?? payload.email ?? 'User',
    };
  } catch {
    return null;
  }
}
