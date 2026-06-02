// UI-only global state reducer.
// Architecture ref: frontend_architecture.md §7

import {
  type AppAction,
  SET_SELECTED_PATIENT,
  PUSH_TOAST,
  POP_TOAST,
  SET_SEARCH_QUERY,
  type Toast,
} from './actions';

export interface AppState {
  selectedPatientId: string | null; // drives Sidebar highlight
  toasts: Toast[];                  // notification queue
  searchQuery: string;              // persisted search input across nav
}

export const initialState: AppState = {
  selectedPatientId: null,
  toasts: [],
  searchQuery: '',
};

export function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case SET_SELECTED_PATIENT:
      return { ...state, selectedPatientId: action.payload };

    case PUSH_TOAST:
      return { ...state, toasts: [...state.toasts, action.payload] };

    case POP_TOAST:
      return { ...state, toasts: state.toasts.filter((t) => t.id !== action.payload) };

    case SET_SEARCH_QUERY:
      return { ...state, searchQuery: action.payload };

    default:
      return state;
  }
}
