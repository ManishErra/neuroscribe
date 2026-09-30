// Axios HTTP client — base URL, auth interceptor, 401 handler
// Architecture ref: frontend_architecture.md §9.3

import axios from 'axios';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor: attach Bearer token ─────────────────────────────────
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('ns_access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: normalize errors, handle 401 ───────────────────────

function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;

    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }

    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) => {
          if (typeof item === 'string') return item;
          if (item && typeof item === 'object' && 'msg' in item) {
            const msg = (item as { msg?: unknown }).msg;
            return typeof msg === 'string' ? msg : null;
          }
          return null;
        })
        .filter((message): message is string => Boolean(message));

      if (messages.length) return messages.join('. ');
    }

    if (detail && typeof detail === 'object' && 'message' in detail) {
      const message = (detail as { message?: unknown }).message;
      if (typeof message === 'string' && message.trim()) return message;
    }

    if (typeof err.response?.data?.message === 'string' && err.response.data.message.trim()) {
      return err.response.data.message;
    }

    if (err.message) return err.message;
  }

  if (err instanceof Error && err.message) return err.message;
  return 'Request failed. Please try again.';
}

client.interceptors.response.use(
  (res) => res.data,
  (err: unknown) => {
    const hasAccessToken = Boolean(localStorage.getItem('ns_access_token'));

    // A failed login itself returns 401. Do not redirect an already logged-out
    // user back to the same login page. Only expire an existing session.
    if (axios.isAxiosError(err) && err.response?.status === 401 && hasAccessToken) {
      localStorage.removeItem('ns_access_token');
      window.location.href = '/login';
    }

    return Promise.reject(new Error(getErrorMessage(err)));
  }
);

export default client;
