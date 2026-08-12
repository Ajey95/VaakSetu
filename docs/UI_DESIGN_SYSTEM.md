# UI Design System

**Accepted concept:** `docs/design/ai-sales-coach-primary.png` (1536 x 1024)

## Copy lock

Above the fold may contain the product and workflow copy defined by SSOT sections 16 and 41: AI SALES COACH; CALL & PROFILE; LIVE CONVERSATION; AI COACH; the five provider health labels; call controls; speaker labels; profile categories; stage, temperature, confidence, next-best action, why, evidence, and feedback labels. Data values come from live state and are not marketing claims.

## Tokens

- Canvas: true white `#ffffff`; alternate transcript rail `#f7f9fb`; cool chrome `#f2f5f8`.
- Ink: `#10213f`; muted ink `#5b6b82`; border `#cad5e1`.
- Live/accent: `#11884f`; soft live `#e8f7ee`.
- Evidence/warning: `#e8950b`; soft evidence `#fff6e5`.
- Destructive: `#d93f3f`; soft destructive `#fff0f0`.
- Radius: 8px controls, 10px priority/evidence regions. Shadow is absent except a subtle focus elevation.
- Spacing: 4, 8, 12, 16, 24, 32px.
- Motion: 140ms state transitions; a restrained 1.6s status pulse; disabled under reduced motion.

## Typography

Use Inter/Geist-like system sans fallbacks. Product title is 24px/700 with tracking. Panel titles are 15px/700 uppercase. Micro-labels are 11-12px/700 uppercase with 0.08em tracking. Body and transcript copy are 14-16px with 1.45-1.55 line height. The next action is 20-22px/700. Every input and button sets an explicit 14-16px weight and line height.

## Container and component rules

The application is a full-height workbench divided by hairline rules, not a dashboard of floating cards. Reusable families are health items, call controls, definition rows, signal lists, transcript rows, recommendation status, evidence definition lists, and feedback controls. Only the next action, sensitive warning, and evidence detail receive purposeful bordered emphasis.

Desktop columns are approximately 26% / 41% / 33%. Mobile order is health, call/profile, coach, transcript, evidence/summary. Primary controls and status never disappear. No raster asset is shipped in the application; the concept remains QA evidence only.

## Icon inventory

Use consistent 1.75px round-line inline SVG icons for phone, hang-up, currency, shield, location, bed, calendar, warning, useful, and not-useful. Status indicators are 8px filled circles. Icons use `currentColor`, 20-22px optical size, and align to the first text baseline. Do not use text glyphs or emoji.
