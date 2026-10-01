---
name: Clinical Precision
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#434654'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#737685'
  outline-variant: '#c3c6d6'
  surface-tint: '#0c56d0'
  primary: '#003d9b'
  on-primary: '#ffffff'
  primary-container: '#0052cc'
  on-primary-container: '#c4d2ff'
  inverse-primary: '#b2c5ff'
  secondary: '#505f76'
  on-secondary: '#ffffff'
  secondary-container: '#d0e1fb'
  on-secondary-container: '#54647a'
  tertiary: '#3b4358'
  on-tertiary: '#ffffff'
  tertiary-container: '#535a70'
  on-tertiary-container: '#cbd2ec'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2ff'
  primary-fixed-dim: '#b2c5ff'
  on-primary-fixed: '#001848'
  on-primary-fixed-variant: '#0040a2'
  secondary-fixed: '#d3e4fe'
  secondary-fixed-dim: '#b7c8e1'
  on-secondary-fixed: '#0b1c30'
  on-secondary-fixed-variant: '#38485d'
  tertiary-fixed: '#dae2fd'
  tertiary-fixed-dim: '#bec6e0'
  on-tertiary-fixed: '#131b2e'
  on-tertiary-fixed-variant: '#3f465c'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 32px
  container-max: 1440px
---

## Brand & Style
The design system is engineered for the high-stakes environment of clinical intelligence. It prioritizes cognitive ease, professional reliability, and data clarity above all else. The brand personality is that of a "Silent Partner"—efficient, precise, and unobtrusive.

The visual style is a refined **Minimalism** blended with **Modern Corporate** sensibilities. It draws inspiration from high-productivity tools like Linear and Stripe to create a workspace that feels like a modern operating system for healthcare. The interface utilizes generous whitespace to reduce clinician burnout and clear structural hierarchies to ensure critical patient data is never missed. No decorative elements are permitted unless they serve a functional purpose in data visualization or status indication.

## Colors
The palette is rooted in medical tradition but executed with modern digital standards.
- **Primary (Medical Blue):** Used for primary actions, active states, and essential navigational markers. It conveys authority and trust.
- **Neutral (Surface):** The background (#F9FAFB) provides a soft, low-glare canvas for long-term use.
- **Semantic Colors:** Critical for clinical safety. Success (Emerald 600), Warning (Amber 500), and Destructive (Rose 600) must be used sparingly and only for relevant status changes or alerts.
- **Typography Colors:** Use a deep slate (#1E293B) for primary text to ensure high contrast against white cards without the harshness of pure black.

## Typography
**Inter** is the sole typeface for this design system, chosen for its exceptional legibility in technical contexts and its robust support for numerical data. 

- **Clinical Data:** Patient vitals and time-stamped logs should use `body-md` with a medium weight to ensure glanceability.
- **Hierarchy:** Use `label-sm` in all-caps for metadata headers (e.g., "PATIENT ID", "VISIT DATE") to distinguish labels from user-generated medical notes.
- **Line Height:** Tight line heights are avoided to ensure that dense medical paragraphs remain readable during rapid review.

## Layout & Spacing
The system utilizes a strict **8px grid** to ensure mathematical harmony across all components. 

- **Layout Model:** A **Fixed Grid** approach is preferred for the main content area (max-width 1440px) to prevent line lengths from becoming unreadable on ultra-wide monitors. 
- **Sidebars:** Use fixed-width left navigation (240px) to maintain a persistent anchor for the doctor's workflow.
- **Density:** Clinical dashboards should utilize "Compact" spacing (8px-12px) between related data points, while editorial views (like AI-generated summaries) should use "Spacious" padding (24px+) to encourage focus.

## Elevation & Depth
Depth is conveyed through **Tonal Layers** and **Low-Contrast Outlines** rather than aggressive shadows.

1.  **Level 0 (Background):** #F9FAFB. The base canvas.
2.  **Level 1 (Cards/Surface):** #FFFFFF with a 1px border (#E2E8F0). This is the primary container for all patient information.
3.  **Level 2 (Overlays):** Dropdowns and Modals use a sophisticated multi-layered shadow: `0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)`.

Avoid any "floating" elements that do not have a subtle border; borders provide the necessary definition in high-brightness clinical environments.

## Shapes
The shape language is **Soft** and professional. 
- **Standard Radius:** 4px (0.25rem) is used for inputs, buttons, and secondary cards. This creates a crisp, precise feel.
- **Large Radius:** 8px (0.5rem) is reserved for primary content containers and modals.
- **Interactive Elements:** Checkboxes use a 2px radius to maintain a distinct square-ish profile that implies "selection," while avatars remain fully circular.

## Components
- **Buttons:** Primary buttons use the Medical Blue background with white text. Ghost buttons use the primary blue for text with no background until hover.
- **Cards:** The workhorse of the system. Every card must have a white background, a 1px #E2E8F0 border, and `rounded-lg` (8px) corners.
- **Input Fields:** Use a 1px neutral border that thickens and changes to Medical Blue on focus. Labels must always be visible (never use placeholder-only labels).
- **Status Chips:** Use subtle background tints (e.g., 10% opacity of the semantic color) with high-contrast text for status indicators like "Stable," "Critical," or "Pending."
- **Data Tables:** Use zebra-striping with #F9FAFB and ensure cell padding is at least 12px vertically to maintain touch-targets for tablet-using clinicians.
- **AI Insight Highlight:** Any content generated by the AI should be subtly demarcated with a left-accent border in Primary Blue or a very soft blue gradient background to indicate its origin.