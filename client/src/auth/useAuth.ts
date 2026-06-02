// Thin hook — reads auth state from AuthContext.
// Architecture ref: frontend_architecture.md §10 (useAuth.js)

import { useAuthContext } from './AuthContext';

export const useAuth = () => useAuthContext();
