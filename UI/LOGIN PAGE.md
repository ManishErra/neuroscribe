---
name: NeuroScribe Clinical Intelligence
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
  on-surface-variant: '#434652'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#747783'
  outline-variant: '#c3c6d6'
  surface-tint: '#2f59b7'
  primary: '#00296d'
  on-primary: '#ffffff'
  primary-container: '#003d9b'
  on-primary-container: '#91afff'
  inverse-primary: '#b2c5ff'
  secondary: '#505f76'
  on-secondary: '#ffffff'
  secondary-container: '#d4e3ff'
  on-secondary-container: '#56657c'
  tertiary: '#252d41'
  on-tertiary: '#ffffff'
  tertiary-container: '#3b4358'
  on-tertiary-container: '#a8b0c9'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2ff'
  primary-fixed-dim: '#b2c5ff'
  on-primary-fixed: '#001848'
  on-primary-fixed-variant: '#08409e'
  secondary-fixed: '#d4e3ff'
  secondary-fixed-dim: '#b8c7e2'
  on-secondary-fixed: '#0c1c30'
  on-secondary-fixed-variant: '#39485e'
  tertiary-fixed: '#dae2fc'
  tertiary-fixed-dim: '#bec6e0'
  on-tertiary-fixed: '#131b2e'
  on-tertiary-fixed-variant: '#3e465c'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
  medical-blue-dark: '#001848'
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
    letterSpacing: 0.05em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 32px
  container-max: 1440px
---

## Brand & Style
NeuroScribe embodies a **Corporate Modern** aesthetic tailored for the high-stakes healthcare environment. The brand personality is professional, precise, and reassuringly technical—designed to act as a "silent partner" for clinicians. 

The visual style prioritizes **Clinical Clarity** through a minimalist approach: high-density information is balanced by generous whitespace and a sophisticated, cool-toned palette. It avoids unnecessary ornamentation in favor of functional elegance, utilizing sharp typography and subtle tonal layering to establish an environment of trust and HIPAA-compliant security.

## Colors
The color strategy uses a **Deep Clinical Blue** as the primary anchor, symbolizing authority and intelligence. 
- **Primary Palette:** Built around `#003d9b`, transitioning to a darker `#001848` for high-contrast interactions and states.
- **Neutral Foundation:** The system relies heavily on "Surface" tones (`#f8f9fa`) and "Surface Container Lowest" (`#ffffff`) to create a sterile yet welcoming environment.
- **Functional Accents:** Secondary and tertiary grays provide hierarchical depth without introducing visual noise.
- **Contrast:** High-contrast text (`#191c1d`) ensures maximum legibility for clinical documentation.

## Typography
The system uses **Inter** exclusively to leverage its utilitarian, highly readable nature. 
- **Headlines:** Feature tight letter-spacing and semi-bold weights (`600`) to create a structured, professional hierarchy.
- **Body Text:** Standardizes on `14px` for density and `16px` for readability in focused tasks.
- **Labels:** Small caps or slightly tracked-out labels are used for secondary metadata (like "HIPAA Compliant") to differentiate from actionable content.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid** model. Large-scale layouts utilize a 50/50 split-screen approach on desktop to balance evocative brand imagery with functional utility.
- **Grid:** Based on an 8px rhythmic unit.
- **Margins:** 32px standard desktop margins, scaling down to 16px on mobile devices.
- **Form Layout:** Components are stacked with 20px - 24px gaps (Gutter) to maintain a sense of openness and reduce cognitive load during data entry.

## Elevation & Depth
Depth is communicated through **Tonal Layering** and **Soft Ambient Shadows** rather than heavy borders.
- **Surfaces:** Backgrounds use `#f8f9fa`, while interactive containers use `#ffffff`.
- **Shadows:** A very subtle `shadow-sm` or a wide-spread, low-opacity directional shadow (e.g., `shadow-[-20px_0_40px_rgba(0,0,0,0.02)]`) is used on the primary interaction panel to create a sense of the panel floating above the background.
- **Interaction:** Focus states are high-contrast, using a 1px primary-colored ring to indicate active input fields.

## Shapes
The shape language is **Rounded**, striking a balance between the sterile precision of medicine and the approachability of modern AI software.
- **Core Elements:** Buttons and Input fields use a standard 0.5rem (`8px`) corner radius.
- **Small Elements:** Checkboxes use a tighter `4px` radius.
- **Brand Elements:** Icons and Logos utilize a `rounded-lg` (16px) radius to stand out as distinct objects.

## Components
- **Buttons:** Primary buttons are high-saturation (`#003d9b`) with white text and `label-md` typography. Hover states darken to `#001848`. They should always include a trailing icon (e.g., `arrow_forward`) to imply progression.
- **Input Fields:** Utilize "Surface Container Lowest" (`#ffffff`) as a base with a subtle `#c3c6d6` border. Leading icons (20px) are mandatory for quick visual scanning.
- **Checkboxes:** Small, 16px squares with primary-color fills when active, paired with `body-md` labels.
- **Logos:** Presented in a container with a 1px border (`outline-variant/30`) to ensure visibility against varied backgrounds.
- **Iconography:** Use Material Symbols (Outlined) with a consistent 20px optical size and `#737685` color for non-active states.