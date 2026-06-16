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
client.interceptors.response.use(
  (res) => res.data,
  async (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('ns_access_token');
      window.location.href = '/login';
    }
    const message = err.response?.data?.detail || err.message || 'Request failed';
    return Promise.reject(new Error(message));
  }
);

export default client;
