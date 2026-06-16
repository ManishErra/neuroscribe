// Query key registry — single source of truth for all TanStack Query keys.
// Architecture ref: frontend_architecture.md §6.2

export const QUERY_KEYS = {
  // Patients
  patients:        (): string[] => ['patients'],
  patient:         (id: string): string[] => ['patient', id],
  patientOverview: (id: string): string[] => ['patient-overview', id],

  // Sessions
  sessions:        (patientId: string): string[] => ['sessions', patientId],
  session:         (id: string): string[] => ['session', id],

  // Reports
  reports:         (patientId: string): string[] => ['reports', patientId],
  report:          (id: string): string[] => ['report', id],

  // Insights
  patientInsights: (id: string): string[] => ['patient-insights', id],

  // Timeline & Comparison
  timeline:        (id: string): string[] => ['timeline', id],
  comparison:      (id: string): string[] => ['comparison', id],
} as const;

export const PAGE_TITLES = {
  dashboard:     'Dashboard — NeuroScribe',
  patients:      'Patients — NeuroScribe',
  sessions:      'Sessions — NeuroScribe',
  reports:       'Reports — NeuroScribe',
  insights:      'Clinical Insights — NeuroScribe',
  timeline:      'Lab Timeline — NeuroScribe',
  search:        'Semantic Search — NeuroScribe',
  login:         'Sign In — NeuroScribe',
  settings:      'Settings — NeuroScribe',
} as const;

export const AI_ENGINE_LABEL = 'Clinical Intelligence Engine' as const;

