# NeuroScribe Frontend Architecture

## Overview

NeuroScribe is a clinical intelligence platform for managing patients, recording sessions, uploading lab reports, and surfacing AI-generated clinical insights. The frontend is a **React** single-page application (SPA) built with **Vite**, using **React Router v6** for routing, **TanStack Query (React Query v5)** for all server state, a lightweight **Context + useReducer** store for UI-only global state, and **Axios** for HTTP. The component layer is built on **shadcn/ui** over **TailwindCSS**, with **Lucide React** for icons.

---

## 1. React Project Structure

The project uses a **feature-based** layout where each domain owns its own components, hooks, services, and types. Shared primitives live in top-level `components/`, `hooks/`, and `types/` directories.

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── main.jsx                        # Vite entry — mounts QueryClientProvider + AuthProvider + App
│   ├── App.jsx                         # Root router definition
│   ├── index.css                       # Global design tokens & resets
│   │
│   ├── api/
│   │   └── axiosClient.js              # Axios instance, base URL, auth interceptor
│   │
│   ├── auth/                           # Authentication feature (see Section 10)
│   │   ├── AuthContext.jsx             # Auth context + provider
│   │   ├── useAuth.js                  # Hook to read auth state
│   │   ├── authService.js              # login(), logout(), refreshToken() calls
│   │   ├── ProtectedRoute.jsx          # Route guard wrapper
│   │   └── LoginPage.jsx               # /login screen
│   │
│   ├── features/                       # Feature-based domain modules
│   │   ├── patients/
│   │   │   ├── components/
│   │   │   │   ├── PatientCard.jsx
│   │   │   │   ├── PatientForm.jsx
│   │   │   │   └── PatientStatusBadge.jsx
│   │   │   ├── hooks/
│   │   │   │   ├── usePatients.js      # useQuery — GET /patients/
│   │   │   │   ├── usePatient.js       # useQuery — GET /patients/:id
│   │   │   │   ├── useCreatePatient.js # useMutation — POST /patients/
│   │   │   │   └── useDeletePatient.js # useMutation — DELETE /patients/:id
│   │   │   ├── services/
│   │   │   │   └── patients.service.js # API call functions (consumed by hooks)
│   │   │   └── types/
│   │   │       └── patient.types.js    # Patient, PatientCreate, PatientOverview
│   │   │
│   │   ├── sessions/
│   │   │   ├── components/
│   │   │   │   ├── SessionList.jsx
│   │   │   │   ├── SessionCard.jsx
│   │   │   │   └── AudioUploader.jsx
│   │   │   ├── hooks/
│   │   │   │   ├── useSessions.js          # useQuery — GET /sessions/patient/:id
│   │   │   │   ├── useSession.js           # useQuery — GET /sessions/:id
│   │   │   │   ├── useCreateSession.js     # useMutation — POST /sessions/
│   │   │   │   └── useUploadAudio.js       # useMutation — POST /upload-audio
│   │   │   ├── services/
│   │   │   │   └── sessions.service.js
│   │   │   └── types/
│   │   │       └── session.types.js
│   │   │
│   │   ├── notes/
│   │   │   ├── components/
│   │   │   │   ├── NoteEditor.jsx
│   │   │   │   └── NoteViewer.jsx
│   │   │   ├── hooks/
│   │   │   │   ├── useGenerateNote.js   # useMutation — POST /generate-note
│   │   │   │   ├── useSaveNote.js       # useMutation — POST /save-note
│   │   │   │   └── useEmbedNote.js      # useMutation — POST /embed/note (auto)
│   │   │   ├── services/
│   │   │   │   └── notes.service.js
│   │   │   └── types/
│   │   │       └── note.types.js
│   │   │
│   │   ├── reports/
│   │   │   ├── components/
│   │   │   │   ├── ReportUploader.jsx
│   │   │   │   ├── ReportCard.jsx
│   │   │   │   └── OcrStatusChip.jsx
│   │   │   ├── hooks/
│   │   │   │   ├── useReports.js       # useQuery — GET /reports/patient/:id
│   │   │   │   ├── useReport.js        # useQuery — GET /reports/:id
│   │   │   │   ├── useUploadReport.js  # useMutation — POST /reports/upload
│   │   │   │   └── useRunOcr.js        # useMutation — POST /reports/:id/ocr
│   │   │   ├── services/
│   │   │   │   └── reports.service.js
│   │   │   └── types/
│   │   │       └── report.types.js
│   │   │
│   │   ├── insights/
│   │   │   ├── components/
│   │   │   │   ├── ClinicalSummaryPanel.jsx
│   │   │   │   ├── FindingsList.jsx
│   │   │   │   ├── AbnormalitiesList.jsx
│   │   │   │   ├── RecommendationsList.jsx
│   │   │   │   └── ClinicalFlagBadge.jsx
│   │   │   ├── hooks/
│   │   │   │   ├── usePatientInsights.js  # useQuery — GET /patient-insights/:id
│   │   │   │   └── usePatientOverview.js  # useQuery — GET /patient-overview/:id
│   │   │   ├── services/
│   │   │   │   └── insights.service.js
│   │   │   └── types/
│   │   │       └── insight.types.js
│   │   │
│   │   ├── timeline/
│   │   │   ├── components/
│   │   │   │   ├── TimelineChart.jsx
│   │   │   │   └── TimelineEntry.jsx
│   │   │   ├── hooks/
│   │   │   │   └── useTimeline.js      # useQuery — GET /timeline/:id
│   │   │   ├── services/
│   │   │   │   └── timeline.service.js
│   │   │   └── types/
│   │   │       └── timeline.types.js
│   │   │
│   │   ├── comparison/
│   │   │   ├── components/
│   │   │   │   └── ComparisonTable.jsx
│   │   │   ├── hooks/
│   │   │   │   └── useComparison.js    # useQuery — GET /compare/:id
│   │   │   ├── services/
│   │   │   │   └── comparison.service.js
│   │   │   └── types/
│   │   │       └── comparison.types.js
│   │   │
│   │   └── search/
│   │       ├── components/
│   │       │   ├── SearchBar.jsx
│   │       │   └── SearchResultCard.jsx
│   │       ├── hooks/
│   │       │   └── useSearch.js        # useMutation — POST /ask/
│   │       ├── services/
│   │       │   └── search.service.js
│   │       └── types/
│   │           └── search.types.js
│   │
│   ├── components/                     # Shared, domain-agnostic UI primitives
│   │   ├── common/
│   │   │   ├── Button.jsx
│   │   │   ├── Badge.jsx
│   │   │   ├── Card.jsx
│   │   │   ├── Spinner.jsx
│   │   │   ├── ErrorBoundary.jsx
│   │   │   ├── EmptyState.jsx
│   │   │   └── Toast.jsx
│   │   └── layout/
│   │       ├── Sidebar.jsx
│   │       ├── TopBar.jsx
│   │       └── PageShell.jsx
│   │
│   ├── pages/                          # Route-level page compositions
│   │   ├── Dashboard/
│   │   │   ├── DashboardPage.jsx
│   │   │   └── DashboardPage.css
│   │   ├── PatientProfile/
│   │   │   ├── PatientProfilePage.jsx
│   │   │   ├── tabs/
│   │   │   │   ├── OverviewTab.jsx
│   │   │   │   ├── SessionsTab.jsx
│   │   │   │   ├── ReportsTab.jsx
│   │   │   │   ├── InsightsTab.jsx
│   │   │   │   └── TimelineTab.jsx
│   │   │   └── PatientProfilePage.css
│   │   ├── SessionDetail/
│   │   │   ├── SessionDetailPage.jsx
│   │   │   └── SessionDetailPage.css
│   │   ├── Search/
│   │   │   ├── SearchPage.jsx
│   │   │   └── SearchPage.css
│   │   └── NotFound/
│   │       └── NotFoundPage.jsx
│   │
│   ├── store/                          # UI-only global state (not server state)
│   │   ├── AppContext.jsx
│   │   ├── appReducer.js
│   │   └── actions.js
│   │
│   ├── types/                          # Shared / cross-feature TypeScript-style JSDoc types
│   │   ├── patient.types.js
│   │   ├── report.types.js
│   │   ├── insight.types.js
│   │   ├── timeline.types.js
│   │   ├── comparison.types.js
│   │   └── session.types.js
│   │
│   └── utils/
│       ├── formatters.js               # Date, unit, number formatters
│       ├── statusColors.js             # STABLE/WARNING/CRITICAL → CSS class
│       └── constants.js               # QUERY_KEYS, page titles
│
├── vite.config.js
├── package.json
├── .env                                # Development environment variables
├── .env.production                     # Production environment variables
└── .env.example                        # Committed template for onboarding
```

---

## 2. Feature-Based Structure — Internals

Each feature folder under `src/features/<domain>/` is a self-contained vertical slice:

```
features/<domain>/
├── components/     UI widgets owned exclusively by this feature
├── hooks/          Data-fetching hooks (wrap useQuery / useMutation)
├── services/       Raw async API functions (consumed only by hooks)
└── types/          JSDoc @typedef declarations for this domain's shapes
```

### Ownership Rules

| Layer | Responsibility | May import from |
|---|---|---|
| `services/` | HTTP calls via axiosClient | `src/api/axiosClient.js` only |
| `hooks/` | TanStack Query wrappers | Feature's own `services/`, `src/utils/constants.js` (QUERY_KEYS) |
| `components/` | Rendering + interaction | Feature's own `hooks/`, `src/components/common/`, `src/types/` |
| `pages/` | Route composition | Any feature's `components/` and `hooks/` |

**Cross-feature imports are allowed only at the `pages/` level.** Features must not import from each other's `hooks/` or `services/` directly. If two features share a service call (e.g., overview is used by both Dashboard and OverviewTab), the service lives in `insights/services/` and is accessed through its own hook only.

---

## 3. Shared Type System (`src/types/`)

All types are defined using JSDoc `@typedef` for IDE autocompletion without requiring TypeScript compilation. The types in `src/types/` represent the **API response shapes** consumed by the frontend. Feature-local types (e.g., form state shapes) stay in `features/<domain>/types/`.

### 3.1 Patient

```js
// src/types/patient.types.js

/**
 * @typedef {Object} Patient
 * @property {string} id
 * @property {string} name
 * @property {number} age
 * @property {string} gender
 * @property {string} created_at
 */

/**
 * @typedef {Object} PatientOverview
 * @property {string}   patient_id
 * @property {'STABLE'|'WARNING'|'CRITICAL'} status
 * @property {string[]} clinical_flags
 * @property {Object.<string, string>} latest_labs   e.g. { hemoglobin: "9.2 g/dL" }
 * @property {{ type: string, date: string, id: string }} last_activity
 */
```

### 3.2 Session

```js
// src/types/session.types.js

/**
 * @typedef {Object} SessionSummary
 * @property {string}  id
 * @property {string}  session_date
 * @property {boolean} has_note
 * @property {boolean} note_finalized
 */

/**
 * @typedef {Object} SessionDetail
 * @property {string}      id
 * @property {string}      session_date
 * @property {string|null} transcript
 * @property {ClinicalNote|null} note
 * @property {boolean}     note_finalized
 */

/**
 * @typedef {Object} ClinicalNote
 * @property {string}   presenting_complaint
 * @property {string[]} symptoms_mentioned
 * @property {string[]} medications_mentioned
 * @property {string}   sleep
 * @property {string}   mood_in_patient_words
 * @property {string}   social_context
 * @property {string}   plan_discussed
 * @property {string}   flags_for_review
 * @property {string}   confidence
 */
```

### 3.3 Report

```js
// src/types/report.types.js

/**
 * @typedef {Object} ReportSummary
 * @property {string}      id
 * @property {string}      patient_id
 * @property {string}      file_path
 * @property {string|null} original_filename
 * @property {string|null} mime_type
 * @property {string|null} title
 * @property {string|null} report_date
 * @property {'pending'|'ready'|'failed'} ocr_status
 * @property {string|null} created_at
 */

/**
 * @typedef {ReportSummary & { ocr_text: string|null, ocr_error: string|null }} ReportDetail
 */
```

### 3.4 Insight

```js
// src/types/insight.types.js

/**
 * @typedef {Object} PatientInsights
 * @property {string}   patient_id
 * @property {string}   summary
 * @property {string[]} findings
 * @property {string[]} abnormalities
 * @property {string[]} recommendations
 * @property {string[]} clinical_flags
 * @property {string|null} report_date
 * @property {string|null} trend_summary
 */
```

### 3.5 Timeline

```js
// src/types/timeline.types.js

/**
 * @typedef {Object} TimelineEntry
 * @property {string} date
 * @property {string} report_id
 * @property {Object.<string, string>} labs   e.g. { hemoglobin: "9.2", wbc: "14.5" }
 */

/**
 * @typedef {Object} PatientTimeline
 * @property {string}          patient_id
 * @property {string}          patient_name
 * @property {TimelineEntry[]} timeline
 */
```

### 3.6 Comparison

```js
// src/types/comparison.types.js

/**
 * @typedef {Object} ComparisonItem
 * @property {string}      test
 * @property {string|null} previous
 * @property {string|null} current
 * @property {string|null} delta
 * @property {'improving'|'worsening'|'stable'|'new'} trend
 */

/**
 * @typedef {Object} PatientComparison
 * @property {string}           patient_id
 * @property {string}           patient_name
 * @property {ComparisonItem[]} comparison
 */
```

**Ownership rule:** Types in `src/types/` are the single source of truth for API response shapes. Feature-level `types/` files may re-export from here or add form/UI-specific shapes. No component or hook should inline object shapes — always reference a `@typedef`.

---

## 4. Routing Structure

Built with **React Router v6** (`createBrowserRouter`). All non-auth routes are wrapped in `ProtectedRoute`.

| Route | Component | Auth Required | Description |
|---|---|---|---|
| `/login` | `LoginPage` | ✗ | Credential entry |
| `/` | `DashboardPage` | ✓ | Patient list + overview cards |
| `/patients/new` | `DashboardPage` (modal) | ✓ | Create new patient slide-over |
| `/patients/:patientId` | `PatientProfilePage` | ✓ | Tabbed patient detail |
| `/patients/:patientId/overview` | `OverviewTab` | ✓ | Status + flags + latest labs |
| `/patients/:patientId/sessions` | `SessionsTab` | ✓ | Session list + audio upload |
| `/patients/:patientId/sessions/:sessionId` | `SessionDetailPage` | ✓ | Transcript + note editor |
| `/patients/:patientId/reports` | `ReportsTab` | ✓ | Report upload + OCR trigger |
| `/patients/:patientId/insights` | `InsightsTab` | ✓ | Clinical summary, findings |
| `/patients/:patientId/timeline` | `TimelineTab` | ✓ | Lab trend charts + comparison |
| `/search` | `SearchPage` | ✓ | Semantic search (`/ask`) |
| `*` | `NotFoundPage` | — | 404 fallback |

```jsx
// src/App.jsx (simplified)
const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: <ProtectedRoute><PageShell /></ProtectedRoute>,
    children: [
      { index: true, element: <DashboardPage /> },
      {
        path: "patients/:patientId",
        element: <PatientProfilePage />,
        children: [
          { index: true, element: <Navigate to="overview" replace /> },
          { path: "overview",  element: <OverviewTab /> },
          { path: "sessions",  element: <SessionsTab /> },
          { path: "reports",   element: <ReportsTab /> },
          { path: "insights",  element: <InsightsTab /> },
          { path: "timeline",  element: <TimelineTab /> },
        ],
      },
      { path: "patients/:patientId/sessions/:sessionId", element: <SessionDetailPage /> },
      { path: "search", element: <SearchPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
```

---

## 5. Screen → Backend Endpoint Mapping

### 5.1 Dashboard (`/`)

**Purpose:** List all patients with at-a-glance clinical status.

| UI Action | Method | Endpoint | Query Key | Notes |
|---|---|---|---|---|
| Load patient list | `GET` | `/patients/` | `['patients']` | Sorted by `created_at` desc |
| Load status card per patient | `GET` | `/patient-overview/{id}` | `['patient-overview', id]` | Parallel per patient |
| Create new patient | `POST` | `/patients/` | — | Invalidates `['patients']` |
| Delete patient | `DELETE` | `/patients/{id}` | — | Invalidates `['patients']` |

**Data flow (React Query):**
```
DashboardPage
  usePatients()           → useQuery(['patients'])        → GET /patients/
  usePatientOverview(id)  → useQuery(['patient-overview', id])  → per card
  useCreatePatient()      → useMutation → onSuccess: invalidate ['patients']
```

---

### 5.2 Patient Profile — Overview Tab (`/patients/:id/overview`)

**Purpose:** At-a-glance patient summary with clinical flags, latest labs, and last activity.

| UI Action | Method | Endpoint | Query Key | Notes |
|---|---|---|---|---|
| Load overview | `GET` | `/patient-overview/{id}` | `['patient-overview', id]` | Shared with Dashboard cache |
| Load patient metadata | `GET` | `/patients/{id}` | `['patient', id]` | Name, age, gender for header |

**Response shape consumed:** `PatientOverview` type.

---

### 5.3 Patient Profile — Sessions Tab (`/patients/:id/sessions`)

**Purpose:** Manage clinical sessions; create sessions, upload audio.

| UI Action | Method | Endpoint | Query Key | Notes |
|---|---|---|---|---|
| Load sessions | `GET` | `/sessions/patient/{id}` | `['sessions', patientId]` | `has_note`, `note_finalized` |
| Create session | `POST` | `/sessions/` | — | Invalidates `['sessions', patientId]` |
| Upload audio | `POST` | `/upload-audio` | — | FormData: `session_id`, `file` |

---

### 5.4 Session Detail (`/patients/:id/sessions/:sessionId`)

**Purpose:** View transcript, generate AI note, edit, and finalize.

| UI Action | Method | Endpoint | Query Key | Notes |
|---|---|---|---|---|
| Load session | `GET` | `/sessions/{session_id}` | `['session', sessionId]` | transcript + note |
| Generate AI note | `POST` | `/generate-note` | — | Returns `note_id` + `ai_draft` |
| Save/finalize note | `POST` | `/save-note` | — | Invalidates `['session', sessionId]` |
| Embed note (auto) | `POST` | `/embed/note` | — | Chained after save-note succeeds |

**UI state machine:**
```
LOADING → HAS_TRANSCRIPT → GENERATING_NOTE → NOTE_DRAFT → NOTE_SAVING → NOTE_SAVED
```

---

### 5.5 Patient Profile — Reports Tab (`/patients/:id/reports`)

**Purpose:** Upload lab reports, trigger OCR, view status.

| UI Action | Method | Endpoint | Query Key | Notes |
|---|---|---|---|---|
| Load report list | `GET` | `/reports/patient/{id}` | `['reports', patientId]` | ReportSummary list |
| Upload report | `POST` | `/reports/upload` | — | Invalidates `['reports', patientId]` |
| Run OCR | `POST` | `/reports/{id}/ocr` | — | Invalidates `['reports', patientId]`, `['report', id]` |
| View report detail | `GET` | `/reports/{id}` | `['report', reportId]` | Full text + ocr_status |

**OCR status chip mapping:**

| `ocr_status` | UI label | Color |
|---|---|---|
| `pending` | Pending | amber |
| `ready` | Ready | green |
| `failed` | Failed | red |

---

### 5.6 Patient Profile — Insights Tab (`/patients/:id/insights`)

**Purpose:** Display AI-generated clinical summary, findings, abnormalities, recommendations, and clinical flags.

| UI Action | Method | Endpoint | Query Key | Notes |
|---|---|---|---|---|
| Load insights | `GET` | `/patient-insights/{id}` | `['patient-insights', id]` | Full clinical intelligence |

**Response shape consumed:** `PatientInsights` type.

**Component breakdown:**
```
InsightsTab
├── ClinicalSummaryPanel        ← summary text
├── ClinicalFlagBadge[]         ← clinical_flags[]
├── FindingsList                ← findings[]
├── AbnormalitiesList           ← abnormalities[]
└── RecommendationsList         ← recommendations[]
```

---

### 5.7 Patient Profile — Timeline Tab (`/patients/:id/timeline`)

**Purpose:** Visualize lab value trends over time and compare latest vs previous.

| UI Action | Method | Endpoint | Query Key | Notes |
|---|---|---|---|---|
| Load timeline | `GET` | `/timeline/{id}` | `['timeline', patientId]` | Chronological per-test data |
| Load comparison | `GET` | `/compare/{id}` | `['comparison', patientId]` | Delta: prev vs current |

**Component breakdown:**
```
TimelineTab
├── TimelineChart (Recharts)    ← ['timeline', id] data → multi-line chart
│   ├── hemoglobin series
│   ├── wbc series
│   └── platelets series
└── ComparisonTable             ← ['comparison', id] data → delta rows
    └── columns: test | prev | current | delta | trend arrow
```

---

### 5.8 Search Page (`/search`)

**Purpose:** Semantic search across all finalized notes and reports.

| UI Action | Method | Endpoint | Notes |
|---|---|---|---|
| Submit search | `POST` | `/ask/` | `useMutation` — not cached; results are transient |

**Response shape consumed:**
```json
{
  "question": "...",
  "answer": "...",
  "chunks_used": [{ "chunk_text": "...", "source_id": "..." }]
}
```

---

## 6. React Query Strategy

### 6.1 Setup

```js
// src/main.jsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

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
```

Install: `npm install @tanstack/react-query`

### 6.2 Query Key Registry

All query keys are declared in a single constants file to prevent string drift and enable precise invalidation.

```js
// src/utils/constants.js

export const QUERY_KEYS = {
  // Patients
  patients:        () => ['patients'],
  patient:         (id) => ['patient', id],
  patientOverview: (id) => ['patient-overview', id],

  // Sessions
  sessions:        (patientId) => ['sessions', patientId],
  session:         (id) => ['session', id],

  // Reports
  reports:         (patientId) => ['reports', patientId],
  report:          (id) => ['report', id],

  // Insights
  patientInsights: (id) => ['patient-insights', id],

  // Timeline & Comparison
  timeline:        (id) => ['timeline', id],
  comparison:      (id) => ['comparison', id],
};
```

### 6.3 Query Patterns

All `useQuery` hooks follow this standard shape:

```js
// src/features/insights/hooks/usePatientInsights.js
import { useQuery } from "@tanstack/react-query";
import { QUERY_KEYS } from "../../../utils/constants";
import { fetchPatientInsights } from "../services/insights.service";

export function usePatientInsights(patientId) {
  return useQuery({
    queryKey: QUERY_KEYS.patientInsights(patientId),
    queryFn:  () => fetchPatientInsights(patientId),
    enabled:  !!patientId,
  });
}
// Returns: { data, isLoading, isError, error, refetch }
```

### 6.4 Mutation Patterns

All `useMutation` hooks follow this standard shape with cache invalidation in `onSuccess`:

```js
// src/features/reports/hooks/useRunOcr.js
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { QUERY_KEYS } from "../../../utils/constants";
import { runOcr } from "../services/reports.service";

export function useRunOcr(patientId) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reportId) => runOcr(reportId),
    onSuccess: (_, reportId) => {
      // Invalidate the report list (status chip updates)
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.reports(patientId) });
      // Invalidate the specific report detail
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.report(reportId) });
      // Insights and timeline may now have new data
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.patientInsights(patientId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.timeline(patientId) });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.comparison(patientId) });
    },
  });
}
```

### 6.5 Cache Invalidation Strategy

| Trigger | Invalidates |
|---|---|
| `POST /patients/` success | `QUERY_KEYS.patients()` |
| `DELETE /patients/:id` success | `QUERY_KEYS.patients()` |
| `POST /sessions/` success | `QUERY_KEYS.sessions(patientId)` |
| `POST /upload-audio` success | `QUERY_KEYS.sessions(patientId)`, `QUERY_KEYS.session(sessionId)` |
| `POST /save-note` success | `QUERY_KEYS.session(sessionId)` |
| `POST /reports/upload` success | `QUERY_KEYS.reports(patientId)` |
| `POST /reports/:id/ocr` success | `QUERY_KEYS.reports(patientId)`, `QUERY_KEYS.report(id)`, `QUERY_KEYS.patientInsights(patientId)`, `QUERY_KEYS.timeline(patientId)`, `QUERY_KEYS.comparison(patientId)` |

**Rule:** `/ask/` (search) uses `useMutation` instead of `useQuery` — search results are transient and must not be cached between queries.

**Rule:** `patient-overview` and `patient-insights` caches are invalidated together any time a new OCR-ready report is created, since these endpoints depend on the latest report text.

---

## 7. State Management Strategy

### Server State → TanStack Query

All data that originates from the backend is **server state** managed exclusively by TanStack Query. No server state is stored in Context or `useState`.

### UI State → Context + useReducer

Context manages only ephemeral, UI-layer concerns that have no backend representation.

**Global UI state shape:**
```js
{
  selectedPatientId: null,  // Drives Sidebar highlight
  toasts: [],               // Notification queue { id, message, type }
  searchQuery: "",          // Persisted search input across nav
}
```

**What is NOT in global state (fully local):**
- Note editor draft (local to `SessionDetailPage`)
- Audio upload progress percentage (local to `AudioUploader`)
- Report upload file selection (local to `ReportUploader`)
- OCR run loading state (returned by `useRunOcr().isPending`)
- Active tab (driven by URL via React Router)

**Actions:**
```js
// src/store/actions.js
export const SET_SELECTED_PATIENT = "SET_SELECTED_PATIENT";
export const PUSH_TOAST           = "PUSH_TOAST";
export const POP_TOAST            = "POP_TOAST";
export const SET_SEARCH_QUERY     = "SET_SEARCH_QUERY";
```

---

## 8. Component Hierarchy

```
App
└── QueryClientProvider
    └── AuthProvider
        └── AppContextProvider
            └── RouterOutlet
                │
                ├── /login → LoginPage
                │
                └── ProtectedRoute → PageShell
                    ├── Sidebar
                    │   ├── Logo
                    │   ├── PatientList       ← usePatients()
                    │   │   └── PatientCard (compact) × N
                    │   └── NavLink (Search)
                    ├── TopBar
                    │   ├── Breadcrumb
                    │   └── SearchBar (→ /search)
                    └── <Outlet>
                        │
                        ├── [/] DashboardPage
                        │   ├── PatientCard × N         ← usePatientOverview(id)
                        │   └── CreatePatientModal      ← useCreatePatient()
                        │
                        ├── [/patients/:id] PatientProfilePage
                        │   ├── PatientHeader           ← usePatient(id)
                        │   ├── TabNav
                        │   └── <Outlet>
                        │       ├── OverviewTab         ← usePatientOverview(id)
                        │       ├── SessionsTab         ← useSessions(id)
                        │       │   ├── SessionCard × N
                        │       │   ├── CreateSessionButton
                        │       │   └── AudioUploader
                        │       ├── ReportsTab          ← useReports(id)
                        │       │   ├── ReportCard × N
                        │       │   │   ├── OcrStatusChip
                        │       │   │   └── RunOcrButton ← useRunOcr(id)
                        │       │   └── ReportUploader  ← useUploadReport()
                        │       ├── InsightsTab         ← usePatientInsights(id)
                        │       │   ├── ClinicalSummaryPanel
                        │       │   ├── ClinicalFlagBadge × N
                        │       │   ├── FindingsList
                        │       │   ├── AbnormalitiesList
                        │       │   └── RecommendationsList
                        │       └── TimelineTab
                        │           ├── TimelineChart   ← useTimeline(id)
                        │           └── ComparisonTable ← useComparison(id)
                        │
                        ├── [/patients/:id/sessions/:sid] SessionDetailPage
                        │   ├── TranscriptPanel         ← useSession(sid)
                        │   ├── GenerateNoteButton      ← useGenerateNote()
                        │   ├── NoteEditor              ← (local state)
                        │   └── SaveNoteButton          ← useSaveNote() → useEmbedNote()
                        │
                        └── [/search] SearchPage
                            ├── SearchBar               ← useSearch()
                            └── SearchResultCard × N
```

---

## 9. Environment Configuration

### 9.1 Variable Naming

| Variable | Purpose | Required |
|---|---|---|
| `VITE_API_URL` | Backend base URL | ✓ |
| `VITE_APP_TITLE` | Browser tab title | optional |
| `VITE_AUTH_ENABLED` | Enable/disable auth guard (`true`/`false`) | optional, default `true` |

> **Note:** All frontend environment variables **must** be prefixed with `VITE_` to be exposed by Vite's bundler. Variables without this prefix are invisible to browser code.

### 9.2 Environment Files

```
.env              # Local development defaults (committed only as .env.example)
.env.production   # Production overrides (injected by CI/CD)
.env.example      # Committed template — safe for source control
```

```env
# .env.example
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=NeuroScribe
VITE_AUTH_ENABLED=true
```

```env
# .env (local — not committed)
VITE_API_URL=http://localhost:8000
VITE_APP_TITLE=NeuroScribe (Dev)
VITE_AUTH_ENABLED=true
```

```env
# .env.production (injected by CI/CD pipeline)
VITE_API_URL=https://api.neuroscribe.io
VITE_APP_TITLE=NeuroScribe
VITE_AUTH_ENABLED=true
```

### 9.3 API Client Initialization

```js
// src/api/axiosClient.js
import axios from "axios";

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

// ── Request interceptor: attach Bearer token ──────────────────────────────
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("ns_access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ── Response interceptor: normalize errors, handle 401 ───────────────────
client.interceptors.response.use(
  (res) => res.data,
  async (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("ns_access_token");
      window.location.href = "/login";
    }
    const message = err.response?.data?.detail || err.message || "Request failed";
    return Promise.reject(new Error(message));
  }
);

export default client;
```

---

## 10. Authentication Architecture

> **Current backend status:** The FastAPI backend does not yet expose `/auth/login` or `/auth/me` endpoints. The authentication architecture below is the **planned contract** the frontend will implement. `VITE_AUTH_ENABLED=false` can bypass guards during local development until the auth endpoints are live.

### 10.1 Auth Flow Design

```
┌─ Login Page ─────────────────────────────────────────────────────┐
│  User submits email + password                                   │
│  → POST /auth/login  { email, password }                        │
│  ← { access_token: "...", token_type: "bearer" }                │
│  → Store token in localStorage as "ns_access_token"            │
│  → Set AuthContext.user from token payload (JWT decode)         │
│  → Navigate to "/"                                               │
└──────────────────────────────────────────────────────────────────┘

┌─ Authenticated Request ──────────────────────────────────────────┐
│  axiosClient request interceptor                                 │
│  → Reads "ns_access_token" from localStorage                   │
│  → Attaches "Authorization: Bearer <token>" header             │
└──────────────────────────────────────────────────────────────────┘

┌─ 401 Response ───────────────────────────────────────────────────┐
│  axiosClient response interceptor                                │
│  → Removes "ns_access_token" from localStorage                 │
│  → Redirects to "/login"                                        │
└──────────────────────────────────────────────────────────────────┘

┌─ Logout ─────────────────────────────────────────────────────────┐
│  User clicks Logout in Sidebar                                   │
│  → authService.logout() removes token from localStorage        │
│  → Clears AuthContext.user                                      │
│  → queryClient.clear() — wipe all cached server state          │
│  → Navigate to "/login"                                          │
└──────────────────────────────────────────────────────────────────┘
```

### 10.2 Auth Context

```js
// src/auth/AuthContext.jsx
// Shape of AuthContext value:
{
  user: null,           // { id, email, name } decoded from JWT, or null
  isAuthenticated: bool,
  isLoading: bool,      // true while checking stored token on app boot
  login:  async (email, password) => void,
  logout: () => void,
}
```

On app mount, `AuthProvider` checks `localStorage` for `ns_access_token`. If found, it decodes the payload to restore `user` without a network call. If expired, it clears the token and sets `isAuthenticated: false`.

### 10.3 Auth Service

```
// src/auth/authService.js  — planned API surface

login(email, password)
  POST /auth/login
  → stores token, returns decoded user

logout()
  → removes localStorage token (no server call required for JWT)
  → clears queryClient cache

getCurrentUser()
  → decodes "ns_access_token" from localStorage (sync, no fetch)
  → returns null if missing or expired
```

### 10.4 Protected Routes

```js
// src/auth/ProtectedRoute.jsx
// Reads VITE_AUTH_ENABLED from env:
//   false → render children unconditionally (dev bypass)
//   true  → redirect to /login if !isAuthenticated
//           show Spinner while isLoading
```

All routes except `/login` are wrapped in `<ProtectedRoute>` at the router level (see Section 4). The `ProtectedRoute` component reads `isLoading` from `useAuth()` and shows a full-screen spinner while the stored token is being validated on first load, preventing a flash of the login page for already-authenticated users.

### 10.5 Token Persistence

| Concern | Decision | Rationale |
|---|---|---|
| Storage | `localStorage` key `ns_access_token` | Simple; acceptable for internal clinical tool |
| Format | JWT (Bearer) | Stateless; decodable client-side for user display |
| Expiry handling | 401 interceptor → redirect to `/login` | Covers expired tokens without refresh loop |
| Logout | Remove from localStorage + `queryClient.clear()` | Prevents stale patient data from leaking between sessions |
| Security note | HTTPS required in production | Mitigates token interception risk |

### 10.6 Planned Backend Auth Endpoints

When the backend implements authentication, the frontend expects:

| Endpoint | Method | Request | Response |
|---|---|---|---|
| `/auth/login` | POST | `{ email, password }` | `{ access_token, token_type }` |
| `/auth/me` | GET | Bearer token in header | `{ id, email, name }` |

---

## 11. Component Library Strategy

### 11.1 Technology Choices

| Layer | Library | Version | Purpose |
|---|---|---|---|
| CSS utility framework | **TailwindCSS** | v3 | Utility-first styling; replaces hand-written vanilla CSS |
| Component library | **shadcn/ui** | latest | Accessible, unstyled-by-default components built on Radix UI primitives |
| Icon library | **Lucide React** | latest | Consistent, tree-shakeable SVG icon set |
| Charts | **Recharts** | v2 | Declarative data-visualization for lab trend charts |

**Why shadcn/ui over a packaged library (e.g. MUI, Ant Design):**
- Components are copied into `src/components/ui/` at install time — full ownership, no locked-in versions
- Built on Radix UI: keyboard-navigable, ARIA-compliant out of the box (critical for clinical software)
- Styled via TailwindCSS utility classes — matches the TailwindCSS investment directly
- No runtime dependency: tree-shaking eliminates unused components at build time

### 11.2 Project Structure Impact

shadcn/ui components are generated into `src/components/ui/` via the CLI. They are treated as owned source files and can be customized freely.

```
src/
├── components/
│   ├── ui/                     # shadcn/ui generated components (owned)
│   │   ├── button.jsx
│   │   ├── badge.jsx
│   │   ├── card.jsx
│   │   ├── dialog.jsx
│   │   ├── tabs.jsx
│   │   ├── table.jsx
│   │   ├── scroll-area.jsx
│   │   ├── alert.jsx
│   │   ├── textarea.jsx
│   │   ├── select.jsx
│   │   ├── switch.jsx
│   │   ├── separator.jsx
│   │   ├── skeleton.jsx
│   │   └── tooltip.jsx
│   ├── common/                 # NeuroScribe-specific composites (wrap ui/)
│   │   ├── StatusBadge.jsx     # wraps Badge with STABLE/WARNING/CRITICAL colors
│   │   ├── OcrStatusChip.jsx   # wraps Badge with pending/ready/failed colors
│   │   ├── Spinner.jsx         # Lucide Loader2 + animation
│   │   ├── EmptyState.jsx
│   │   ├── ErrorBoundary.jsx
│   │   └── Toast.jsx           # wraps shadcn Toaster
│   └── layout/
│       ├── Sidebar.jsx
│       ├── TopBar.jsx
│       └── PageShell.jsx
```

### 11.3 Icon Usage (Lucide React)

Icons are imported individually to preserve tree-shaking:

```js
// Correct — single named import
import { Activity, FileText, Clock, AlertTriangle, Search } from "lucide-react";
```

**Icon-to-concept mapping:**

| Concept | Lucide Icon |
|---|---|
| Patient status STABLE | `Activity` (green) |
| Patient status WARNING | `AlertTriangle` (amber) |
| Patient status CRITICAL | `AlertOctagon` (red) |
| Lab reports | `FileText` |
| Sessions / audio | `Mic` |
| Clinical insights | `Brain` |
| Timeline / trends | `TrendingUp` / `TrendingDown` |
| Search | `Search` |
| Logout | `LogOut` |
| OCR processing | `ScanText` |
| Delete | `Trash2` |
| Edit / note | `Pencil` |
| Finalized / saved | `CheckCircle2` |

### 11.4 Screen → shadcn/ui Component Mapping

#### Dashboard (`/`)

| shadcn Component | Usage |
|---|---|
| `Card`, `CardHeader`, `CardContent` | Patient overview cards |
| `Badge` | Clinical status chip (STABLE / WARNING / CRITICAL) |
| `Table`, `TableRow`, `TableCell` | Patient list table view |
| `Button` | Create patient, delete patient actions |
| `Dialog`, `DialogContent` | Create patient slide-over / confirm delete |
| `Skeleton` | Loading placeholder while patient overviews fetch |

---

#### Patient Profile — Overview Tab (`/patients/:id/overview`)

| shadcn Component | Usage |
|---|---|
| `Card` | Status summary card, latest labs card, last activity card |
| `Badge` | Clinical flags list (one badge per flag) |
| `Separator` | Visual dividers between card sections |
| `Tooltip` | Hover detail on lab values |

---

#### Patient Profile — Sessions Tab (`/patients/:id/sessions`)

| shadcn Component | Usage |
|---|---|
| `Tabs`, `TabsList`, `TabsTrigger` | Sub-navigation within profile |
| `Card` | Each session entry card |
| `Button` | New session, open session |
| `Badge` | Note status: Draft / Finalized / No Note |

---

#### Session Detail (`/patients/:id/sessions/:sessionId`)

| shadcn Component | Usage |
|---|---|
| `Card` | Transcript panel, note editor panel |
| `Textarea` | Editable note fields (presenting_complaint, plan_discussed, etc.) |
| `Button` | Generate Note, Save Note |
| `Alert`, `AlertDescription` | Flagged phrases warning from AI |
| `Skeleton` | Loading state during note generation |
| `Badge` | Note confidence level |

---

#### Patient Profile — Reports Tab (`/patients/:id/reports`)

| shadcn Component | Usage |
|---|---|
| `Card` | Each report row card |
| `Table`, `TableRow`, `TableCell` | Report list table layout |
| `Badge` | OCR status chip: Pending / Ready / Failed |
| `Button` | Upload Report, Run OCR |
| `ScrollArea` | Scrollable OCR text preview panel |
| `Dialog` | Report detail modal with full OCR text |
| `Skeleton` | Loading placeholder while reports fetch |

---

#### Patient Profile — Insights Tab (`/patients/:id/insights`)

| shadcn Component | Usage |
|---|---|
| `Card`, `CardHeader`, `CardContent` | Summary panel, findings panel, recommendations panel |
| `Badge` | Clinical flags (one badge per flag, color-coded by severity) |
| `Alert`, `AlertTitle`, `AlertDescription` | Abnormality highlight blocks |
| `Separator` | Section dividers |
| `Skeleton` | Loading state while insights fetch |

---

#### Patient Profile — Timeline Tab (`/patients/:id/timeline`)

| shadcn Component | Usage |
|---|---|
| `Card` | Chart container card, comparison table card |
| `Tabs`, `TabsList`, `TabsTrigger` | Switch between Chart view and Table view |
| `Table`, `TableRow`, `TableCell` | Comparison delta table |
| `Badge` | Trend direction: Improving / Worsening / Stable |
| `Select` | Filter: choose which lab test to display on chart |

*Note: Recharts `LineChart`, `XAxis`, `YAxis`, `Tooltip`, `Legend`, `Line` are used inside the chart `Card`, not from shadcn.*

---

#### Search Page (`/search`)

| shadcn Component | Usage |
|---|---|
| `Card` | Each result chunk card |
| `Button` | Submit search |
| `Textarea` | Multi-line question input |
| `Badge` | Source type label on result (note / report) |
| `ScrollArea` | Scrollable results list |
| `Skeleton` | Loading state during answer generation |

---

#### Login Page (`/login`)

| shadcn Component | Usage |
|---|---|
| `Card`, `CardHeader`, `CardContent` | Login form container |
| `Button` | Submit login |
| `Alert`, `AlertDescription` | Auth error display |

---

#### Settings (Future Screen)

| shadcn Component | Usage |
|---|---|
| `Card` | Settings section containers |
| `Switch` | Toggle flags (e.g. notifications, auth enabled) |
| `Select`, `SelectItem` | Dropdown for preference choices |
| `Dialog` | Confirmation dialogs for destructive actions |
| `Separator` | Dividers between settings groups |

### 11.5 TailwindCSS Configuration Notes

- **Dark mode:** `darkMode: "class"` — toggled by adding `dark` class to `<html>`. NeuroScribe defaults to dark mode for clinical readability.
- **Custom colors:** Extend `tailwind.config.js` with NeuroScribe status colors:
  ```js
  // tailwind.config.js — color extensions
  stable:   { DEFAULT: '#22c55e' }   // green-500
  warning:  { DEFAULT: '#f59e0b' }   // amber-500
  critical: { DEFAULT: '#ef4444' }   // red-500
  ```
- **Font:** `Inter` via `@fontsource/inter` — added to `tailwind.config.js` `fontFamily.sans`
- **shadcn/ui CSS variables:** shadcn injects CSS variables (`--background`, `--foreground`, `--primary`, etc.) into `index.css` via `globals.css`. Do not override these manually — use the shadcn theme tokens.

---

## 12. Key Design Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | React + Vite | Fast HMR, modern ES modules, minimal config |
| Routing | React Router v6 | Nested routes map cleanly to tabbed patient profile |
| Server state | TanStack Query v5 | Automatic caching, invalidation, loading/error states — eliminates manual `useEffect` fetch boilerplate |
| UI state | Context + useReducer | Ephemeral UI-only concerns; no Redux overhead needed |
| Code organization | Feature-based (`src/features/`) | Domain colocation; scales as features grow independently |
| Types | JSDoc `@typedef` | IDE autocompletion without TypeScript build step |
| Component library | shadcn/ui | Owned, accessible, Radix-based; no runtime lock-in |
| Styling | TailwindCSS v3 | Utility-first; pairs natively with shadcn/ui token system |
| Icons | Lucide React | Tree-shakeable SVG icons; consistent clinical iconography |
| Charts | Recharts | Declarative, composable, no WebGL overhead |
| API transport | Axios + interceptors | Centralized auth injection + error normalization |
| Forms | Controlled components | Note editor fields map 1:1 to `ClinicalNoteSchema` |
| File uploads | FormData | Required by FastAPI `Form` + `UploadFile` endpoints |
| Auth bypass | `VITE_AUTH_ENABLED=false` | Allows local development before backend auth is implemented |

---

## 13. Development Commands

```bash
# ── Step 1: Scaffold project (run once) ───────────────────────────────────
npx -y create-vite@latest ./ --template react

# ── Step 2: Install core runtime dependencies ─────────────────────────────
npm install react-router-dom axios @tanstack/react-query recharts

# ── Step 3: Install and configure TailwindCSS ─────────────────────────────
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
# Then configure tailwind.config.js content paths and theme extensions

# ── Step 4: Install Lucide React ──────────────────────────────────────────
npm install lucide-react

# ── Step 5: Install Inter font ────────────────────────────────────────────
npm install @fontsource/inter

# ── Step 6: Initialise shadcn/ui (run once, interactive) ──────────────────
npx shadcn@latest init
# Prompts: style=Default, base color=Slate, CSS variables=yes

# ── Step 7: Add shadcn/ui components as needed ────────────────────────────
npx shadcn@latest add button badge card dialog tabs table scroll-area
npx shadcn@latest add alert textarea select switch separator skeleton tooltip

# ── Dev server ────────────────────────────────────────────────────────────
npm run dev

# ── Production build ──────────────────────────────────────────────────────
npm run build

# ── Preview production build locally ──────────────────────────────────────
npm run preview
```

---

## 14. Backend Endpoint Reference

| Endpoint | Method | Router File | Query Key | Used By Screen |
|---|---|---|---|---|
| `/patients/` | GET | `routers/patients.py` | `['patients']` | Dashboard, Sidebar |
| `/patients/` | POST | `routers/patients.py` | mutation | Dashboard (Create Patient) |
| `/patients/{id}` | GET | `routers/patients.py` | `['patient', id]` | PatientProfilePage header |
| `/patients/{id}` | DELETE | `routers/patients.py` | mutation | Dashboard (Delete Patient) |
| `/sessions/patient/{id}` | GET | `routers/sessions.py` | `['sessions', id]` | SessionsTab |
| `/sessions/{id}` | GET | `routers/sessions.py` | `['session', id]` | SessionDetailPage |
| `/sessions/` | POST | `routers/sessions.py` | mutation | SessionsTab (New Session) |
| `/upload-audio` | POST | `routers/audio.py` | mutation | AudioUploader |
| `/generate-note` | POST | `routers/notes.py` | mutation | SessionDetailPage |
| `/save-note` | POST | `routers/notes.py` | mutation | SessionDetailPage |
| `/embed/note` | POST | `routers/embed.py` | mutation | SessionDetailPage (auto) |
| `/reports/patient/{id}` | GET | `routers/reports.py` | `['reports', id]` | ReportsTab |
| `/reports/upload` | POST | `routers/reports.py` | mutation | ReportUploader |
| `/reports/{id}/ocr` | POST | `routers/reports.py` | mutation | ReportsTab (Run OCR) |
| `/reports/{id}` | GET | `routers/reports.py` | `['report', id]` | ReportsTab (Detail) |
| `/timeline/{id}` | GET | `routers/timeline.py` | `['timeline', id]` | TimelineTab (Chart) |
| `/compare/{id}` | GET | `routers/comparison.py` | `['comparison', id]` | TimelineTab (Table) |
| `/patient-insights/{id}` | GET | `patient_insights.py` | `['patient-insights', id]` | InsightsTab |
| `/patient-overview/{id}` | GET | `patient_insights.py` | `['patient-overview', id]` | Dashboard, OverviewTab |
| `/ask/` | POST | `routers/search.py` | mutation (no cache) | SearchPage |
| `/auth/login` *(planned)* | POST | TBD | mutation | LoginPage |
| `/auth/me` *(planned)* | GET | TBD | `['auth-me']` | AuthProvider (boot) |

---

## 15. Frontend Delivery Roadmap

The frontend is built in six sequential phases. Each phase has a clear goal, a set of deliverables, and a definition of done before the next phase begins.

---

### Phase 1 — Project Foundation
**Goal:** Scaffold the project, configure all tooling, and validate the dev pipeline is working end-to-end before any feature code is written.

| Step | Task | Done When |
|---|---|---|
| 1.1 | `npx create-vite` scaffold + commit baseline | `npm run dev` serves blank React page |
| 1.2 | Install and configure TailwindCSS + PostCSS | Tailwind utility classes apply in browser |
| 1.3 | Run `npx shadcn@latest init` | `src/components/ui/` created, CSS variables injected |
| 1.4 | Add all 14 shadcn components (`button`, `badge`, `card`, `dialog`, `tabs`, `table`, `scroll-area`, `alert`, `textarea`, `select`, `switch`, `separator`, `skeleton`, `tooltip`) | All imports resolve without errors |
| 1.5 | Install Lucide React + `@fontsource/inter` | Icons render; Inter loads in browser |
| 1.6 | Install React Router v6 + create `App.jsx` with all named routes (no page content yet) | All routes resolve to placeholder divs |
| 1.7 | Install TanStack Query + wrap `main.jsx` with `QueryClientProvider` | `useQuery` importable in any component |
| 1.8 | Install Axios + create `src/api/axiosClient.js` with `VITE_API_URL` | Axios client exports without error |
| 1.9 | Create `.env`, `.env.example`, `.env.production` | All env vars documented |
| 1.10 | Configure `tailwind.config.js` — content paths, `darkMode: "class"`, status colors, Inter font | Custom colors appear in Tailwind IntelliSense |

**Deliverable:** A running Vite dev server with full toolchain, all routing stubs, and all shadcn components available. No feature code.

---

### Phase 2 — Shared Layout & Auth Shell
**Goal:** Build the persistent shell (Sidebar, TopBar, PageShell) and the auth guard so all subsequent pages can be built inside the correct frame.

| Step | Task | Done When |
|---|---|---|
| 2.1 | Create `src/auth/AuthContext.jsx` + `useAuth.js` | `useAuth()` returns `{ user, isAuthenticated, isLoading }` |
| 2.2 | Create `src/auth/authService.js` — `login()`, `logout()`, `getCurrentUser()` | Functions defined; auth endpoints stubbed |
| 2.3 | Create `src/auth/ProtectedRoute.jsx` with `VITE_AUTH_ENABLED` bypass | Routes redirect to `/login` when unauthenticated |
| 2.4 | Create `LoginPage` — `Card` + email/password fields + `Alert` for errors | Login form renders; submit calls `authService.login()` |
| 2.5 | Create `Sidebar.jsx` — logo, patient list placeholder, Search nav link | Sidebar renders with correct nav structure |
| 2.6 | Create `TopBar.jsx` — breadcrumb + search bar placeholder | TopBar renders in correct position |
| 2.7 | Create `PageShell.jsx` — Sidebar + TopBar + `<Outlet>` | All protected pages render inside the shell |
| 2.8 | Create `AppContext.jsx` + `appReducer.js` — `selectedPatientId`, `toasts`, `searchQuery` | Global UI state readable via `useAppContext()` |
| 2.9 | Create shared `StatusBadge.jsx`, `Spinner.jsx`, `EmptyState.jsx` in `components/common/` | Components render correctly in isolation |

**Deliverable:** Complete shell with working auth bypass (`VITE_AUTH_ENABLED=false`). Any protected page renders inside PageShell. Login redirect works.

---

### Phase 3 — Patient Management (Dashboard + Patient Profile Frame)
**Goal:** Implement the patient list, patient creation, and the patient profile tab container. This unlocks all sub-tabs.

| Step | Task | Done When |
|---|---|---|
| 3.1 | Create `features/patients/services/patients.service.js` — all CRUD functions | Functions call correct endpoints; Axios errors surface |
| 3.2 | Create `features/patients/hooks/usePatients.js` — `useQuery(['patients'])` | `{ data, isLoading, isError }` returned correctly |
| 3.3 | Create `features/patients/hooks/usePatient.js` — single patient | Returns patient by ID |
| 3.4 | Create `features/patients/hooks/useCreatePatient.js` + `useDeletePatient.js` | Mutations invalidate `['patients']` on success |
| 3.5 | Create `PatientCard.jsx` — name, age, status badge, last activity | Card renders with placeholder data |
| 3.6 | Create `PatientForm.jsx` — controlled form for name/age/gender | Form submits; validation messages display |
| 3.7 | Build `DashboardPage` — patient list + `PatientCard` grid + create dialog | Live patient list renders from API |
| 3.8 | Create `features/insights/hooks/usePatientOverview.js` | Overview data populates `PatientCard` status |
| 3.9 | Build `PatientProfilePage` — `PatientHeader` + `TabNav` + `<Outlet>` | Tab navigation renders; routes work |
| 3.10 | Populate `Sidebar` patient list with live `usePatients()` data | Sidebar highlights selected patient |

**Deliverable:** Full patient CRUD on Dashboard. PatientProfilePage renders with tab navigation. Sidebar shows live patients.

---

### Phase 4 — Core Clinical Workflows (Sessions, Notes, Reports)
**Goal:** Implement the three primary data-entry workflows: session creation, audio upload + AI note generation, and lab report upload + OCR.

#### 4A — Sessions & Notes

| Step | Task | Done When |
|---|---|---|
| 4A.1 | Create `sessions.service.js`, `useSessions.js`, `useSession.js`, `useCreateSession.js`, `useUploadAudio.js` | All hooks return correct shapes |
| 4A.2 | Build `SessionsTab` — session list + `SessionCard` + create button + `AudioUploader` | Sessions list renders from API; new session creates |
| 4A.3 | Create `notes.service.js`, `useGenerateNote.js`, `useSaveNote.js`, `useEmbedNote.js` | Mutations call correct endpoints |
| 4A.4 | Build `SessionDetailPage` — `TranscriptPanel` + `GenerateNoteButton` + `NoteEditor` + `SaveNoteButton` | Full note workflow: upload audio → generate → edit → save |
| 4A.5 | Implement note state machine (`LOADING → HAS_TRANSCRIPT → GENERATING_NOTE → NOTE_DRAFT → NOTE_SAVING → NOTE_SAVED`) | UI state transitions correctly at each step |

#### 4B — Reports & OCR

| Step | Task | Done When |
|---|---|---|
| 4B.1 | Create `reports.service.js`, `useReports.js`, `useReport.js`, `useUploadReport.js`, `useRunOcr.js` | All hooks return correct shapes |
| 4B.2 | Build `ReportsTab` — `ReportCard` list + `ReportUploader` drag-drop zone + `OcrStatusChip` | Reports list renders; upload creates DB row |
| 4B.3 | Wire `useRunOcr()` — OCR button triggers extraction; status chip updates live | OCR `ready` status reflects after run |
| 4B.4 | Wire cache invalidation: `useRunOcr.onSuccess` invalidates `['reports', id]`, `['report', id]`, `['patient-insights', id]`, `['timeline', id]`, `['comparison', id]` | Insights + Timeline tabs refresh after OCR |

**Deliverable:** All three data-entry workflows functional end-to-end with real API data.

---

### Phase 5 — Clinical Intelligence UI (Insights + Timeline)
**Goal:** Surface the AI-generated clinical intelligence layer built in Days 21–23.

| Step | Task | Done When |
|---|---|---|
| 5.1 | Create `insights.service.js`, `usePatientInsights.js` | `PatientInsights` type returned correctly |
| 5.2 | Build `InsightsTab` — `ClinicalSummaryPanel` + `ClinicalFlagBadge` list + `FindingsList` + `AbnormalitiesList` + `RecommendationsList` | Full insights panel renders from `/patient-insights/:id` |
| 5.3 | Build `OverviewTab` — status badge + flags + latest labs grid + last activity | Overview populates from `/patient-overview/:id` |
| 5.4 | Create `timeline.service.js`, `useTimeline.js` | `PatientTimeline` type returned correctly |
| 5.5 | Create `comparison.service.js`, `useComparison.js` | `PatientComparison` type returned correctly |
| 5.6 | Build `TimelineChart` (Recharts `LineChart`) — multi-test line chart with `Select` filter | Chart renders hemoglobin, WBC, platelets series |
| 5.7 | Build `ComparisonTable` (shadcn `Table`) — delta rows with trend `Badge` | Table shows prev / current / delta / trend arrow |
| 5.8 | Assemble `TimelineTab` — `Tabs` switching between chart and table views | Both views render correctly with live data |

**Deliverable:** Complete AI Insights and Timeline/Comparison screens operational.

---

### Phase 6 — Search, Polish & Deployment
**Goal:** Complete the semantic search screen, harden the UI, and prepare for production.

| Step | Task | Done When |
|---|---|---|
| 6.1 | Create `search.service.js`, `useSearch.js` (useMutation on `/ask/`) | Search returns structured answer + chunks |
| 6.2 | Build `SearchPage` — `Textarea` input + `Button` + `SearchResultCard` list + `ScrollArea` | Full search workflow renders |
| 6.3 | Wire `Toaster` — success/error toasts on all mutations | All mutations show user feedback |
| 6.4 | Implement `ErrorBoundary` at route level | Unhandled errors render fallback UI |
| 6.5 | Add `Skeleton` loading states to all tabs that use `useQuery` | No raw loading spinners remain |
| 6.6 | Responsive layout audit — Sidebar collapse on mobile, fluid grid | No horizontal overflow on ≥375px viewport |
| 6.7 | Accessibility audit — keyboard navigation, ARIA labels on all interactive elements | All interactive elements accessible by keyboard |
| 6.8 | Wire `VITE_AUTH_ENABLED=true` and test full auth flow | Login → protected route → logout cycle works |
| 6.9 | Set `VITE_API_URL` to production backend URL in `.env.production` | Production build hits deployed FastAPI |
| 6.10 | `npm run build` — validate bundle, fix any dead imports | Build completes with no warnings |

**Deliverable:** Production-ready SPA deployable behind the NeuroScribe backend.

---

### Phase Summary

| Phase | Focus | Key Output |
|---|---|---|
| 1 | Project Foundation | Toolchain, routing stubs, all dependencies |
| 2 | Layout & Auth Shell | PageShell, ProtectedRoute, AuthContext, LoginPage |
| 3 | Patient Management | Dashboard, PatientCard, PatientProfilePage frame |
| 4 | Clinical Workflows | Sessions, Notes, Audio upload, Reports, OCR |
| 5 | Clinical Intelligence | InsightsTab, OverviewTab, TimelineTab |
| 6 | Search + Polish + Deploy | Search, toasts, a11y, responsive, production build |

> **Build Order Rule:** Each phase depends on the previous. Do not begin Phase 4 before Phase 3's PatientProfilePage tab container is stable — all sub-tabs mount inside it.

---

## 16. Component Reuse Matrix

This matrix documents which screens each shared component appears in. **Every component must be implemented exactly once** in the location shown — no screen-specific duplicates.

### 16.1 Implementation Ownership

| Component | Lives In | Exports | Rule |
|---|---|---|---|
| `PageShell` | `src/components/layout/` | Default export | Mounted once at the router root; never duplicated |
| `Sidebar` | `src/components/layout/` | Default export | Child of PageShell only |
| `TopBar` | `src/components/layout/` | Default export | Child of PageShell only |
| `PatientStatusBadge` | `src/components/common/` | Named export | Wraps shadcn `Badge`; accepts `status: 'STABLE'\|'WARNING'\|'CRITICAL'` |
| `ClinicalFlagCard` | `src/features/insights/components/` | Named export | Renders a single clinical flag string; maps to `clinical_flags[]` entries |
| `ConfidenceBadge` | `src/features/notes/components/` | Named export | Wraps shadcn `Badge`; accepts `confidence: string` from AI draft |
| `ReportCard` | `src/features/reports/components/` | Named export | Renders one `ReportSummary`; includes `OcrStatusChip` |
| `TimelineChart` | `src/features/timeline/components/` | Named export | Recharts `LineChart`; accepts `PatientTimeline` data prop |
| `RecommendationCard` | `src/features/insights/components/` | Named export | Renders a single recommendation string from `recommendations[]` |
| `SessionCard` | `src/features/sessions/components/` | Named export | Renders one `SessionSummary`; includes note status badge |

### 16.2 Screen Usage Matrix

| Component | Dashboard | Overview Tab | Sessions Tab | Session Detail | Reports Tab | Insights Tab | Timeline Tab | Search | Login |
|---|---|---|---|---|---|---|---|---|---|
| `PageShell` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| `Sidebar` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| `TopBar` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| `PatientStatusBadge` | ✓ | ✓ | — | — | — | — | — | — | — |
| `ClinicalFlagCard` | — | ✓ | — | — | — | ✓ | — | — | — |
| `ConfidenceBadge` | — | — | — | ✓ | — | — | — | — | — |
| `ReportCard` | — | — | — | — | ✓ | — | — | — | — |
| `TimelineChart` | — | — | — | — | — | — | ✓ | — | — |
| `RecommendationCard` | — | — | — | — | — | ✓ | — | — | — |
| `SessionCard` | — | — | ✓ | — | — | — | — | — | — |

### 16.3 Shared Infrastructure Components (Used Everywhere)

These components are not domain-specific and must be importable from any feature or page:

| Component | Lives In | Used In |
|---|---|---|
| `Spinner` | `src/components/common/` | All tabs while `isLoading` is true |
| `EmptyState` | `src/components/common/` | All list views when API returns `[]` |
| `ErrorBoundary` | `src/components/common/` | Wraps every route-level page |
| `OcrStatusChip` | `src/components/common/` | `ReportCard`, Reports Tab |
| shadcn `Skeleton` | `src/components/ui/` | All tabs during initial data fetch |
| shadcn `Toaster` | `src/components/ui/` | Mounted once in `PageShell` |

### 16.4 Reuse Rules

1. **No inline duplication.** If two screens need the same UI shape, create the shared component first and import it — do not copy JSX between files.
2. **Feature components are feature-private.** `ReportCard` lives in `features/reports/components/` and is only imported from `ReportsTab` (a page), not from other feature components.
3. **Common components are globally importable.** `PatientStatusBadge`, `Spinner`, `EmptyState`, `OcrStatusChip` may be imported by any page, feature component, or layout component.
4. **Layout components mount once.** `PageShell`, `Sidebar`, `TopBar` are instantiated once at the router root. No page component renders its own sidebar or topbar.
5. **shadcn `ui/` components are the atomic layer.** All NeuroScribe components consume `ui/` primitives — they never re-implement a button, badge, or card from scratch.
6. **Recharts lives inside `TimelineChart` only.** No other component imports Recharts directly. If a second chart is added in future, extract a shared `LabChart` wrapper — still a single file.
