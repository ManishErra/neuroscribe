// UI-only global state action type constants.
// Architecture ref: frontend_architecture.md §7

export const SET_SELECTED_PATIENT = 'SET_SELECTED_PATIENT' as const;
export const PUSH_TOAST           = 'PUSH_TOAST' as const;
export const POP_TOAST            = 'POP_TOAST' as const;
export const SET_SEARCH_QUERY     = 'SET_SEARCH_QUERY' as const;

export type AppAction =
  | { type: typeof SET_SELECTED_PATIENT; payload: string | null }
  | { type: typeof PUSH_TOAST;           payload: Toast }
  | { type: typeof POP_TOAST;            payload: string }
  | { type: typeof SET_SEARCH_QUERY;     payload: string };

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}
