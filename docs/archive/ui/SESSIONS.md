---
name: Clinical Sage
colors:
  surface: '#faf9f6'
  surface-dim: '#dadad7'
  surface-bright: '#faf9f6'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f4f0'
  surface-container: '#eeeeeb'
  surface-container-high: '#e8e8e5'
  surface-container-highest: '#e3e3df'
  on-surface: '#1a1c1a'
  on-surface-variant: '#424843'
  inverse-surface: '#2f312f'
  inverse-on-surface: '#f1f1ed'
  outline: '#727972'
  outline-variant: '#c2c8c1'
  surface-tint: '#466551'
  primary: '#466551'
  on-primary: '#ffffff'
  primary-container: '#7c9d86'
  on-primary-container: '#153422'
  inverse-primary: '#accfb6'
  secondary: '#556158'
  on-secondary: '#ffffff'
  secondary-container: '#d5e3d7'
  on-secondary-container: '#59665c'
  tertiary: '#7d5357'
  on-tertiary: '#ffffff'
  tertiary-container: '#ba898d'
  on-tertiary-container: '#462428'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c8ebd1'
  primary-fixed-dim: '#accfb6'
  on-primary-fixed: '#022111'
  on-primary-fixed-variant: '#2f4d3a'
  secondary-fixed: '#d8e6da'
  secondary-fixed-dim: '#bccabe'
  on-secondary-fixed: '#131e17'
  on-secondary-fixed-variant: '#3d4a41'
  tertiary-fixed: '#ffdadc'
  tertiary-fixed-dim: '#efb9bd'
  on-tertiary-fixed: '#301216'
  on-tertiary-fixed-variant: '#633c40'
  background: '#faf9f6'
  on-background: '#1a1c1a'
  surface-variant: '#e3e3df'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '600'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '500'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 40px
  gutter: 24px
  margin: 32px
---

## Brand & Style
The design system moves away from traditional sterile blues toward a more organic, calming, and "Medical Sage" aesthetic. It centers on **Clinical Precision**—a design philosophy that balances high-end healthcare professionalism with a humanist, approachable touch.

The style is a refined **Minimalism** with subtle **Tonal Layering**. It prioritizes extreme legibility, intentional whitespace, and a sophisticated color palette that reduces cognitive load for practitioners and researchers. The emotional response should be one of "quiet confidence"—intelligent, focused, and profoundly trustworthy.

## Colors
The palette is grounded in "Medical Sage" and "Polar Off-White," creating a soft-contrast environment that prevents eye fatigue.

- **Primary (Medical Sage):** Used for primary actions, active states, and brand identifiers.
- **Primary Dark:** Used for hover states and high-emphasis typography on light backgrounds.
- **Background (Polar Off-White):** A cool, organic off-white that distinguishes the application from generic web platforms.
- **Surface:** Pure white is reserved for cards, modals, and input areas to create a clear "layer" above the background.
- **Status Colors:** Standardized traffic light indicators (Green, Yellow, Red) are utilized for clinical monitoring, but applied with slightly desaturated tones to remain cohesive with the Sage aesthetic.

## Typography
This design system utilizes **Inter** exclusively for its systematic, utilitarian, and highly legible characteristics. 

- **Display & Headlines:** Use tighter letter-spacing and semi-bold weights to convey authority and precision.
- **Body Text:** Standard weight (400) with generous line heights (1.5x) to ensure clinical data is easily scannable.
- **Labels:** Small caps or uppercase labels with increased letter-spacing are used for table headers and metadata to provide clear structural hierarchy.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid** model. Dashboards utilize a 12-column grid with a max-width of 1440px to ensure data density remains manageable.

- **Vertical Rhythm:** Built on an 8px base unit.
- **Grid:** 24px gutters provide significant breathing room between data modules.
- **Responsive Behavior:** On mobile, margins reduce to 16px and the grid collapses to a single column. On tablet, a 6-column grid is preferred for split-view clinical workflows.

## Elevation & Depth
Depth is achieved through **Tonal Layering** and **Soft Ambient Shadows**. 

- **Level 0 (Background):** Polar Off-White (#F8F9F7).
- **Level 1 (Surface):** White (#FFFFFF) cards with a 1px stroke of #E2E8E4 (a sage-tinted neutral) instead of heavy shadows.
- **Level 2 (Popovers/Modals):** Use a very diffused shadow (0px 8px 24px rgba(124, 157, 134, 0.08)) to suggest lifting without feeling disconnected from the UI.
- **Active States:** Subtle inner shadows or a 2px Medical Sage border indicate focus and interaction.

## Shapes
In alignment with the "Round 8" requirement, the design system utilizes a consistent **8px (0.5rem)** corner radius for all primary UI components.

- **Standard (8px):** Buttons, Input Fields, and Checkboxes.
- **Large (16px):** Main content cards and Modals.
- **Pill:** Reserved exclusively for status tags and "Chips" to distinguish them from actionable buttons.

## Components

- **Buttons:** Primary buttons use a solid Medical Sage fill with white text. Secondary buttons use a transparent background with a 1px Sage border.
- **Input Fields:** High-precision styling with 1px #E2E8E4 borders that transition to #7C9D86 on focus. Labels sit 4px above the field in `label-md` style.
- **Status Chips:** Small, pill-shaped indicators. For example, "Normal" uses a light green background with a dark green dot and text.
- **Data Cards:** Content is housed in white cards with 8px radius. Titles are `headline-md` in Primary Dark for clear section definition.
- **Navigation:** Side-navigation uses a "Ghost" style for inactive items, with a subtle Sage vertical bar and soft background tint for the active state.
- **Lists:** Clean rows separated by 1px #F0F2F0 dividers. High-density data should use 48px row heights, while standard lists use 56px.