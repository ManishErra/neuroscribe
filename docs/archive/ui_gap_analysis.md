# NeuroScribe UI Gap Analysis & Redesign Specification

## A. Current Prototype Screenshots
Here is the visual evidence of the current prototype UI captured directly from the local development server:

* **Login Page:**
![Login Prototype](/C:/Users/Manish/.gemini/antigravity-ide/brain/ea2482f1-4c5e-4c48-a263-88501b559686/login_page_1781957909336.png)
* **Dashboard:**
![Dashboard Prototype](/C:/Users/Manish/.gemini/antigravity-ide/brain/ea2482f1-4c5e-4c48-a263-88501b559686/dashboard_page_1781957995561.png)
* **Patient Directory:**
![Patient Directory Prototype](/C:/Users/Manish/.gemini/antigravity-ide/brain/ea2482f1-4c5e-4c48-a263-88501b559686/patient_directory_1781958012479.png)
* **Search Workspace:**
![Search Prototype](/C:/Users/Manish/.gemini/antigravity-ide/brain/ea2482f1-4c5e-4c48-a263-88501b559686/search_page_1781958038961.png)
* **Settings:**
![Settings Prototype](/C:/Users/Manish/.gemini/antigravity-ide/brain/ea2482f1-4c5e-4c48-a263-88501b559686/settings_page_1781958048791.png)

---

## B. Current Design Style Identity
* **Dashboard Style:** Metric-heavy B2B Administration (KPI cards, total counts).
* **Layout Style:** Traditional "SaaS Control Panel" (Fixed left sidebar, top header, massive empty central content areas).
* **Navigation Style:** IT Directory layout (lists of "users" instead of active "clinical cases").
* **Visual Identity:** A developer-centric dark mode that emphasizes stark contrast and neon borders rather than calm, focused clinical documentation.

## C. Why It Fails as a Clinical Tool (The Admin Trap)
The current UI appears as a generic admin dashboard because it prioritizes **data management** over **patient engagement**. 
* **Wrong Focus:** A psychiatrist doesn't log in to look at a KPI card showing "14 Finalized Sessions." They log in to immediately resume their active patient's chart. 
* **Wasted Space:** The "Patient Directory" grid treats patients like inventory items.
* **Lack of Focus:** The layout forces the doctor to click through 3-4 layers (Directory -> Profile -> Tab -> Action) just to start a consultation or read a chart, destroying clinical flow. 

---

## D. Revised Interface Proposal (The Clinical Workspace)

**Vision:** A modern, minimal healthcare SaaS designed exclusively around the **Psychiatrist's clinical documentation workflow**. 
* **Focus:** Deep, distraction-free charting spaces.
* **Palette:** Extremely calm, high-contrast light mode (or extremely muted dark mode) utilizing the Sage Green brand strictly for primary clinical actions (e.g., "Start Recording").
* **Hierarchy:** Flatten the architecture. The dashboard *is* the active patient list. A patient workspace *is* the session timeline.

---

## E. Screen-by-Screen Redesign Wireframes

### 1. Login (Secure & Calm)
*A minimal, focused authentication gate.*
```text
[   NeuroScribe: AI Clinical Memory   ]
-----------------------------------------
|                                       |
|          Sign In to Practice          |
|                                       |
|  [ Email Address                  ]   |
|  [ Password                       ]   |
|                                       |
|  [       Secure Login ->          ]   |
|                                       |
|  *HIPAA & BAA Compliant Workspace     |
-----------------------------------------
```

### 2. Clinical Dashboard (The Day View)
*No KPI metrics. Just today's work and immediate access to patients.*
```text
[ Sidebar ]  | [ Header: Tuesday, June 20 - Morning Shift ]
[ Search  ]  | 
[ Queue   ]  |  [+ Start Walk-in Consultation]  [Import Lab Report]
[ Archive ]  | 
             |  RECENT PATIENTS (Jump back in)
             |  ----------------------------------------------------
             |  [ Radhika E. ] - Critical Alert - Last seen 2d ago
             |  [ Johny D.   ] - Stable       - Last seen 1w ago
             |  [ Jane S.    ] - Monitor      - Pending lab review
             |  ----------------------------------------------------
```

### 3. Unified Patient Workspace
*Merging profile, history, and actions into a single high-density medical chart.*
```text
[ <- Back ]  [ Patient: Radhika Erra ]  [ Age: 34 ]  [ Status: CRITICAL ]
-------------------------------------------------------------------------
[ ACTIVE CHART ]          |  [ CLINICAL TIMELINE ]
                          |
[ Start New Session  ]    |  * Yesterday: Lab Report Uploaded
[ Upload Lab Report  ]    |    - AI Flag: Hemoglobin Low (8.2)
[ Ask Medical Memory ]    | 
                          |  * June 14: Psychiatry Consultation
[ Patient Vitals ]        |    - Dx: Severe Insomnia
                          |    - Rx: Melatonin 5mg
```

### 4. Session Workspace (The Core Feature)
*A dual-pane, distraction-free environment for audio ingestion and SOAP drafting.*
```text
[ Session: June 20 Follow-up ]              [ End Consultation ]
-----------------------------------------------------------------
[ AUDIO INGESTION ]         |  [ AI SOAP NOTE DRAFT ]
                            |
 (   Waveform Animation  )  |  [ Subjective ]
    [ RECORDING 12:04 ]     |  Patient reports 3 hours of sleep...
                            |
 [ Pause ] [ Stop & Sync ]  |  [ Objective ]
                            |  Restless affect. Speech pressured...
                            |
* Whisper transcription     |  [ Assessment ]
  running in background...  |  Acute exacerbation of anxiety...
                            |
                            |  [ Plan ]
                            |  Increase dosage. Follow up 2 wks.
```

### 5. Reports Workspace (Document Ingestion)
*Split view: Original document vs AI extraction.*
```text
[ Report: Complete Blood Count - June 19 ]
-----------------------------------------------------------------
[ ORIGINAL PDF VIEWER ]     |  [ OCR & AI EXTRACTION ]
                            |  
                            |  [ EXTRACTING TEXT... (Spinner) ]
[      PDF PAGE 1     ]     |  
[      RENDERING      ]     |  [ EXTRACTED LABS ]
[         HERE        ]     |  - Hemoglobin: 8.2 (Low)
                            |  - WBC: 5.4 (Normal)
                            |  
                            |  [ Add to Patient Semantic Memory ]
```

### 6. Semantic Search Workspace (RAG Hub)
*A clinical search engine, not a generic database query.*
```text
[ AI CLINICAL MEMORY SEARCH ]
-----------------------------------------------------------------
"When did Radhika first report insomnia?"               [ Ask ]

[ AI INSIGHT ]
Based on the clinical history, Radhika first reported severe 
insomnia during her consultation on June 14, stating she was 
getting "less than 3 hours of sleep."

[ CITED SOURCES ]
- Session Transcript (June 14): "I haven't slept since Monday..."
- Assessment Note (June 14): "Dx: Severe Insomnia"
-----------------------------------------------------------------
```

> [!IMPORTANT]
> The current React prototype code will remain untouched. I await your approval on this redesigned UX Architecture before replacing the generic admin UI with this streamlined Clinical Workspace.
