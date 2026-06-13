# Elora UI/UX Redesign

**Product:** Elora School Management System
**Date:** 2026-06-13
**Status:** Approved design
**Direction:** Premium Executive

## 1. Goal

Redesign every user-facing Elora page as one coherent, commercial school
management product. The interface must be polished enough for daily use by
Kenyan CBC schools while preserving the existing Django workflows, RBAC,
tenant isolation, URLs, forms, and data behavior.

The redesign is visual and interaction-focused. It does not replace existing
domain logic or expand the platform's functional scope.

## 2. Approved Direction

Elora will use the Premium Executive direction:

- A deep navy application sidebar with refined blue and gold accents
- A soft neutral canvas with crisp white surfaces in light mode
- Balanced spacing: information-dense without feeling compressed
- Clear typographic hierarchy using Inter
- Light mode as the default
- A persistent user-controlled dark mode
- A collapsible icon sidebar on desktop
- A slide-out sidebar with backdrop on mobile

The visual language should communicate trust, competence, and calm rather than
feel playful or consumer-oriented.

## 3. Shared Application Shell

### Desktop

The shell contains a collapsible left sidebar, a compact top bar, and a
responsive main content area.

The sidebar contains the Elora identity, grouped navigation, active states, and
the signed-in user's compact profile. Expanded mode shows icons and labels.
Collapsed mode retains recognizable icons and accessible tooltips. Navigation
items remain governed by the existing RBAC rules.

The top bar contains:

- Mobile navigation trigger
- Current school context
- Global search
- Notifications
- Light/dark theme control
- User profile menu

The main content area uses a consistent page header with breadcrumb, title,
supporting text, primary action, and optional secondary actions or filters.

### Mobile

The sidebar becomes an off-canvas panel. It opens from a clearly labeled menu
button, traps focus while open, closes with Escape or backdrop selection, and
uses large touch targets. The main content remains full width.

## 4. Design System

### Color

Light mode uses a pale neutral background, white panels, navy text, muted slate
secondary text, blue primary actions, and restrained gold highlights.

Dark mode uses a near-navy canvas, slightly lighter panels, high-contrast text,
and adjusted blue and gold accents. Dark mode must not be a simple inversion.

Semantic colors are reserved for meaning:

- Green: success, paid, present, positive conduct
- Amber: warning, approaching expectation, pending
- Red: error, overdue, absent, below expectation
- Blue: information, primary actions, meeting expectation
- Violet: exceeding expectation and selected competency highlights

### Type And Spacing

Inter remains the product font. Page titles, section headings, labels, body
text, metadata, and table content use a documented scale. Spacing follows a
small reusable scale so that cards, forms, tables, and dashboards align across
modules.

### Reusable Components

The redesign will establish shared templates and styles for:

- Page headers and breadcrumbs
- Metric cards and trend indicators
- Content panels and chart cards
- Data tables and mobile record cards
- Search, filters, and pagination
- Buttons, badges, alerts, and empty states
- Tabs, dropdowns, drawers, and modals
- Form fields, validation, help text, and action bars
- Activity feeds, timelines, and notification items
- Loading indicators and skeleton states

Components should accept content and variants without duplicating module logic.

## 5. Page Patterns

### Dashboards

Role dashboards use a responsive grid containing:

- Four primary KPI cards
- One prominent analytics chart
- Attendance or competency visualization
- Calendar and upcoming events
- Priority actions and alerts
- Recent finance or operational activity
- Contextual shortcuts based on role

Dashboard content remains driven by existing view data and permissions.

### Index And Record Pages

Learners, staff, finance, attendance, assessments, learning, library,
communication, wellbeing, activities, reports, academics, and timetabling use a
common record-page structure:

- Page header and primary action
- Search and module-specific filters
- Result summary and bulk actions where supported
- Desktop data table
- Mobile-friendly card representation or controlled horizontal table
- Pagination and clear empty states

### Detail Pages

Detail pages use a summary header, key facts, status, contextual actions, and
tabbed or sectioned content. Learner and staff profiles prioritize identity,
relationships, attendance, academic or workload information, documents, and
history.

### Forms

Forms group related fields into labeled sections. Required fields, help text,
errors, and disabled states are explicit. The primary save action remains easy
to find, and destructive actions are visually separated.

### Reports And Printable Pages

Report cards, receipts, and statements retain print-specific layouts. Screen
views adopt the shared shell and provide clear print or download actions.

## 6. Interaction Model

Alpine.js manages local interface state such as sidebar expansion, mobile
navigation, dropdowns, tabs, and the theme preference.

HTMX continues to provide partial updates for existing filters, tables, forms,
and counters. Every asynchronous action must provide:

- A visible loading state
- Duplicate-submission protection
- Clear success or error feedback
- Focus management when content changes
- A usable non-JavaScript fallback where the existing workflow supports it

Chart.js charts use dedicated responsive containers, theme-aware colors, and
readable labels. Charts summarize information rather than replace accessible
text or tables.

## 7. Responsive Behavior

The interface will be verified at representative mobile, tablet, laptop, and
wide desktop widths.

- Dashboard columns stack in priority order on narrow screens
- Filters wrap or move into a compact filter panel
- Tables switch to record cards when dense horizontal data would become
  unreadable
- Primary actions remain visible without crowding titles
- Charts maintain usable height and labels
- Touch targets remain at least comfortably finger-sized

## 8. Accessibility

The redesign targets WCAG 2.2 AA:

- Semantic landmarks and heading order
- Keyboard-operable navigation and controls
- Visible focus states
- Skip-to-content link
- Accessible labels for icon-only controls
- Sufficient text and component contrast in both themes
- Reduced-motion support
- Status communication that does not depend on color alone
- Accessible modal and drawer focus behavior

## 9. Error And Empty States

All modules receive consistent loading, empty, permission-denied, validation,
not-found, and server-error states. Empty states explain what is missing and,
when permitted, provide the next useful action. Error messages avoid exposing
internal details and preserve user-entered form data.

## 10. Architecture

The existing Django application structure remains in place. The redesign will
be implemented through:

- Shared shell templates in `templates/layouts/`
- Reusable presentational components in `templates/components/`
- Module templates that compose those components
- Central Tailwind design tokens and component styles
- Small Alpine stores or controllers for persistent shell state
- Existing Django context and permission checks

View and model changes are only introduced when a page requires already
available data to be exposed cleanly. No parallel frontend framework or second
design system will be added.

## 11. Verification

Automated coverage will verify:

- Authenticated shell rendering
- RBAC-controlled navigation and actions
- Critical page and form rendering
- Existing HTMX partial behavior
- Theme and sidebar controls where practical
- No regressions in existing Django tests

Browser verification will cover every major module in light mode, representative
pages in dark mode, desktop and mobile navigation, charts, tables, forms, empty
states, and print views. The redesign is complete only when the browser preview
shows the new shell and page system consistently across the application.

## 12. References

- Tailwind CSS dark mode: https://tailwindcss.com/docs/dark-mode
- Alpine.js global state: https://alpinejs.dev/magics/store
- Chart.js responsive charts:
  https://www.chartjs.org/docs/latest/configuration/responsive.html
- HTMX documentation: https://htmx.org/docs/
- WCAG 2.2 quick reference: https://www.w3.org/WAI/WCAG22/quickref/
