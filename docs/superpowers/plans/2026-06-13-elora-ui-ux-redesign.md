# Elora UI/UX Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign every Elora page with the approved Premium Executive shell, reusable page components, light and dark themes, balanced responsive layouts, and accessible interactions without changing existing business workflows.

**Architecture:** Keep Django templates as the rendering layer and introduce a small shared component system under `templates/components/`. Tailwind owns visual tokens and component classes, Alpine.js owns local shell state and theme persistence, HTMX keeps existing partial-update behavior, and Chart.js renders theme-aware dashboard visuals from server-provided JSON.

**Tech Stack:** Django 5.2, Python 3.13, Tailwind CSS 4, Alpine.js 3, HTMX 2, Chart.js 4, pytest-django

---

## File Structure

### Shared foundation

- Modify `templates/layouts/app.html`: initialize theme and navigation state, render overlays, and define the shared content frame.
- Modify `templates/layouts/public.html`: align public/login styling with the new tokens.
- Modify `templates/components/sidebar.html`: grouped RBAC navigation, active states, collapse behavior, and user footer.
- Modify `templates/components/topbar.html`: search, school context, notifications, theme control, and profile menu.
- Modify `templates/components/messages.html`: accessible success, warning, and error alerts.
- Create `templates/components/page_header.html`: standard breadcrumb, title, description, and action slots.
- Create `templates/components/metric_card.html`: common KPI presentation.
- Create `templates/components/empty_state.html`: common empty-result presentation.
- Create `templates/components/table_shell.html`: common table title and responsive container.
- Modify `assets/css/input.css`: design tokens, theme variables, reusable component classes, and reduced-motion rules.
- Modify `static/js/app.js`: Alpine shell store, theme persistence, HTMX states, and Chart.js theme synchronization.

### Dashboard and modules

- Modify `apps/analytics/views.py`: expose dashboard trend, attendance, event, finance, and activity data.
- Modify `templates/analytics/dashboard.html`: Premium Executive dashboard composition.
- Modify `templates/analytics/partials/metric_card.html`: delegate to the shared metric component or remove duplication.
- Modify all module templates under `templates/{academics,activities,assessments,attendance,communication,finance,learners,learning,library,reports,staff,timetabling,wellbeing}/`: adopt shared page, panel, table, form, status, and empty-state patterns.
- Modify record partials under the same module folders: responsive table/card behavior and HTMX loading states.
- Modify `templates/accounts/login.html`: branded responsive login experience.
- Modify `templates/403.html`, `templates/404.html`, and `templates/500.html`: consistent application error states.

### Tests

- Create `apps/core/tests/test_ui_shell.py`: shared shell, theme controls, navigation semantics, and mobile controls.
- Modify `apps/analytics/tests/test_dashboards.py`: dashboard sections, chart payloads, and RBAC shortcuts.
- Modify each module's existing `test_views.py` or workflow test: page-header, action visibility, table, form, and empty-state assertions.

## Task 1: Establish The Theme And Shell Contract

**Files:**
- Create: `apps/core/tests/test_ui_shell.py`
- Modify: `templates/layouts/app.html`
- Modify: `assets/css/input.css`
- Modify: `static/js/app.js`

- [ ] **Step 1: Write failing shell tests**

Add tests that authenticate a school administrator and assert the shared shell
contains the theme bootstrap, skip link, collapsible navigation state, mobile
dialog trigger, and main landmark:

```python
@pytest.mark.django_db
def test_authenticated_pages_render_premium_shell(client, school_admin):
    client.force_login(school_admin.user)
    response = client.get(
        reverse("analytics:dashboard"),
        HTTP_HOST=school_admin.domain.hostname,
    )
    content = response.content.decode()

    assert response.status_code == 200
    assert 'data-elora-shell' in content
    assert 'href="#main-content"' in content
    assert 'x-data="eloraShell"' in content
    assert 'data-theme-toggle' in content
    assert 'aria-controls="primary-navigation"' in content
    assert 'id="main-content"' in content
```

- [ ] **Step 2: Run the shell test and verify failure**

Run:

```powershell
python -m pytest apps/core/tests/test_ui_shell.py -v
```

Expected: FAIL because the new shell markers and controls do not exist.

- [ ] **Step 3: Implement the shell state and early theme bootstrap**

Update `templates/layouts/app.html` to initialize `eloraShell`, apply the saved
theme before paint, expose an accessible skip link, and wrap content in
`data-elora-shell`. Add an inline head bootstrap equivalent to:

```html
<script>
  (() => {
    const savedTheme = localStorage.getItem("elora-theme");
    document.documentElement.dataset.theme = savedTheme === "dark" ? "dark" : "light";
  })();
</script>
```

In `static/js/app.js`, register:

```javascript
document.addEventListener("alpine:init", () => {
  Alpine.data("eloraShell", () => ({
    sidebarOpen: false,
    sidebarCollapsed: localStorage.getItem("elora-sidebar") === "collapsed",
    theme: document.documentElement.dataset.theme || "light",
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed;
      localStorage.setItem(
        "elora-sidebar",
        this.sidebarCollapsed ? "collapsed" : "expanded",
      );
    },
    toggleTheme() {
      this.theme = this.theme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = this.theme;
      localStorage.setItem("elora-theme", this.theme);
      window.dispatchEvent(new CustomEvent("elora:theme-change"));
    },
  }));
});
```

- [ ] **Step 4: Add Tailwind theme tokens**

Define semantic custom properties for canvas, surface, border, primary,
secondary text, success, warning, and danger in light and dark modes. Apply
those tokens to `body`, form controls, focus states, and reduced motion:

```css
@layer base {
  :root {
    --elora-canvas: #f4f7fb;
    --elora-surface: #ffffff;
    --elora-text: #0f172a;
    --elora-muted: #64748b;
    --elora-border: #dbe3ee;
    color-scheme: light;
  }

  [data-theme="dark"] {
    --elora-canvas: #07111f;
    --elora-surface: #0f1b2d;
    --elora-text: #e8eef8;
    --elora-muted: #94a3b8;
    --elora-border: #22324a;
    color-scheme: dark;
  }
}
```

- [ ] **Step 5: Build CSS and rerun tests**

Run:

```powershell
$env:Path = "C:\Program Files\nodejs;$env:Path"
& "C:\Program Files\nodejs\npm.cmd" run css:build
python -m pytest apps/core/tests/test_ui_shell.py -v
```

Expected: CSS build succeeds and shell tests PASS.

- [ ] **Step 6: Commit the foundation**

```powershell
& "C:\Program Files\Git\cmd\git.exe" add templates/layouts/app.html assets/css/input.css static/css/app.css static/js/app.js apps/core/tests/test_ui_shell.py
& "C:\Program Files\Git\cmd\git.exe" commit -m "feat: add premium application shell foundation"
```

## Task 2: Build The Responsive Navigation And Top Bar

**Files:**
- Modify: `apps/core/tests/test_ui_shell.py`
- Modify: `apps/analytics/tests/test_dashboards.py`
- Modify: `templates/components/sidebar.html`
- Modify: `templates/components/topbar.html`
- Modify: `templates/layouts/app.html`
- Modify: `assets/css/input.css`

- [ ] **Step 1: Add failing navigation tests**

Assert that authorized modules still render, unauthorized modules remain
absent, the current route receives `aria-current="page"`, and mobile navigation
has dialog semantics:

```python
assert 'id="primary-navigation"' in content
assert 'aria-label="Primary navigation"' in content
assert 'aria-current="page"' in content
assert 'data-mobile-sidebar' in content
assert 'data-sidebar-collapse' in content
assert "Academic structure" not in teacher_content
```

- [ ] **Step 2: Run focused tests and verify failure**

```powershell
python -m pytest apps/core/tests/test_ui_shell.py apps/analytics/tests/test_dashboards.py -v
```

Expected: FAIL on the new navigation structure.

- [ ] **Step 3: Rebuild the sidebar**

Group navigation into `Overview`, `People`, `Learning`, and `Operations`.
Retain every existing permission conditional. Use `request.resolver_match`
namespaces to mark active links. Add inline SVG icons with `aria-hidden="true"`
and visible labels that collapse only on desktop.

The mobile panel must use:

```html
<aside
  id="primary-navigation"
  data-mobile-sidebar
  :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
  @keydown.escape.window="sidebarOpen = false"
>
```

Add a backdrop button that closes the panel and never renders above the sidebar.

- [ ] **Step 4: Rebuild the top bar**

Add a mobile menu button, school identity, non-submitting global search field,
notifications button, theme toggle, and profile dropdown. Icon-only controls
must have `aria-label` and visible focus styles.

- [ ] **Step 5: Compile and verify**

```powershell
$env:Path = "C:\Program Files\nodejs;$env:Path"
& "C:\Program Files\nodejs\npm.cmd" run css:build
python -m pytest apps/core/tests/test_ui_shell.py apps/analytics/tests/test_dashboards.py -v
```

Expected: PASS.

- [ ] **Step 6: Browser-check shell states**

Open `http://green-hills.localhost:56273/dashboard/`. Verify expanded and
collapsed desktop navigation, mobile drawer, active route, profile menu, theme
toggle, keyboard Escape behavior, and persistence after reload.

- [ ] **Step 7: Commit navigation**

```powershell
& "C:\Program Files\Git\cmd\git.exe" add templates/components/sidebar.html templates/components/topbar.html templates/layouts/app.html assets/css/input.css static/css/app.css apps/core/tests/test_ui_shell.py apps/analytics/tests/test_dashboards.py
& "C:\Program Files\Git\cmd\git.exe" commit -m "feat: redesign responsive navigation"
```

## Task 3: Create The Shared Page Component System

**Files:**
- Create: `templates/components/page_header.html`
- Create: `templates/components/metric_card.html`
- Create: `templates/components/empty_state.html`
- Create: `templates/components/table_shell.html`
- Modify: `templates/components/messages.html`
- Modify: `assets/css/input.css`
- Modify: `apps/core/tests/test_ui_shell.py`

- [ ] **Step 1: Write failing component rendering tests**

Use Django's template engine to render each component and assert stable semantic
markers:

```python
template = engines["django"].from_string(
    '{% include "components/page_header.html" with eyebrow="People" title="Learners" %}'
)
content = template.render({})
assert 'data-page-header' in content
assert "<h1" in content
assert "Learners" in content
```

Add equivalent assertions for `data-metric-card`, `data-empty-state`,
`data-table-shell`, and `role="alert"`.

- [ ] **Step 2: Run component tests and verify failure**

```powershell
python -m pytest apps/core/tests/test_ui_shell.py -v
```

Expected: FAIL because the component files do not exist.

- [ ] **Step 3: Add reusable components**

Create focused include templates. `page_header.html` accepts `eyebrow`, `title`,
`description`, `breadcrumbs`, and optional `action_template`.
`metric_card.html` accepts `label`, `value`, `tone`, `trend`, and `icon`.
`empty_state.html` accepts `title`, `description`, and optional action values.
`table_shell.html` wraps a caller-provided table include with heading and
description.

- [ ] **Step 4: Add component classes and accessible messages**

Create `.elora-panel`, `.elora-card`, `.elora-button-primary`,
`.elora-button-secondary`, `.elora-badge-*`, `.elora-table`, and
`.elora-form-section` classes in `assets/css/input.css`. Update message markup
to use `role="alert"` for errors and `role="status"` for success.

- [ ] **Step 5: Build and test**

```powershell
$env:Path = "C:\Program Files\nodejs;$env:Path"
& "C:\Program Files\nodejs\npm.cmd" run css:build
python -m pytest apps/core/tests/test_ui_shell.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit components**

```powershell
& "C:\Program Files\Git\cmd\git.exe" add templates/components assets/css/input.css static/css/app.css apps/core/tests/test_ui_shell.py
& "C:\Program Files\Git\cmd\git.exe" commit -m "feat: add shared UI component system"
```

## Task 4: Redesign The Role Dashboard

**Files:**
- Modify: `apps/analytics/views.py`
- Modify: `apps/analytics/tests/test_dashboards.py`
- Modify: `templates/analytics/dashboard.html`
- Modify: `templates/analytics/partials/metric_card.html`
- Modify: `static/js/app.js`

- [ ] **Step 1: Add failing dashboard data tests**

Extend the seeded dashboard test to require:

```python
assert "Performance overview" in content
assert "Upcoming events" in content
assert "Attendance overview" in content
assert "Recent activity" in content
assert 'id="dashboard-performance-chart"' in content
assert 'id="dashboard-attendance-chart"' in content
assert 'data-dashboard-chart' in content
```

Add assertions that parent and learner dashboards do not expose administrator
shortcuts.

- [ ] **Step 2: Run dashboard tests and verify failure**

```powershell
python -m pytest apps/analytics/tests/test_dashboards.py -v
```

Expected: FAIL on the new dashboard sections.

- [ ] **Step 3: Extend dashboard context**

Keep `_visible_learners()` as the tenant and role boundary. Add small helper
functions for:

- Summary metrics and trend labels
- Attendance present/absent/late values
- Calendar items from current term dates and announcements
- Recent finance, report, and borrowing activity
- Role-appropriate shortcuts

Return JSON-safe dictionaries and lists. Do not query across
`request.school`.

- [ ] **Step 4: Compose the Premium Executive dashboard**

Use the shared page header and metric cards. Create a responsive
`xl:grid-cols-[minmax(0,2fr)_minmax(18rem,0.85fr)]` layout containing the
performance chart, events, recent fee activity, attendance doughnut, priority
actions, and recent activity.

Keep accessible data tables or text summaries adjacent to both charts.

- [ ] **Step 5: Move chart initialization into `app.js`**

Read JSON script elements, initialize charts by `data-dashboard-chart`, and
recompute chart colors when `elora:theme-change` fires. If Chart.js is
unavailable, leave the accessible summaries visible without throwing.

- [ ] **Step 6: Test, compile, and browser-check**

```powershell
$env:Path = "C:\Program Files\nodejs;$env:Path"
& "C:\Program Files\nodejs\npm.cmd" run css:build
python -m pytest apps/analytics/tests/test_dashboards.py -v
```

Open the dashboard in both themes and at desktop and mobile widths. Verify no
chart overflow, unreadable labels, or permission leaks.

- [ ] **Step 7: Commit dashboard**

```powershell
& "C:\Program Files\Git\cmd\git.exe" add apps/analytics templates/analytics static/js/app.js
& "C:\Program Files\Git\cmd\git.exe" commit -m "feat: redesign role dashboards"
```

## Task 5: Redesign People And Academic Administration

**Files:**
- Modify: `templates/learners/index.html`
- Modify: `templates/learners/detail.html`
- Modify: `templates/learners/admit.html`
- Modify: `templates/learners/transfer.html`
- Modify: `templates/learners/partials/learner_table.html`
- Modify: `templates/staff/index.html`
- Modify: `templates/staff/partials/create_card.html`
- Modify: `templates/staff/partials/staff_tables.html`
- Modify: `templates/academics/structure.html`
- Modify: `templates/academics/partials/create_card.html`
- Modify: `templates/academics/partials/structure_tables.html`
- Modify: `apps/learners/tests/test_views.py`
- Modify: `apps/staff/tests/test_views.py`
- Modify: `apps/academics/tests/test_views.py`

- [ ] **Step 1: Add failing page-pattern tests**

For each module, assert the page header, search/filter area, permission-aware
primary action, panel or table shell, and module-specific empty state:

```python
assert 'data-page-header' in content
assert 'data-record-table' in content
assert 'data-empty-state' in empty_content
assert "Admit learner" in admin_content
assert "Admit learner" not in teacher_content
```

- [ ] **Step 2: Run focused tests and verify failure**

```powershell
python -m pytest apps/learners/tests/test_views.py apps/staff/tests/test_views.py apps/academics/tests/test_views.py -v
```

- [ ] **Step 3: Apply the record-page system**

Replace duplicated headers and card markup with shared components. Keep all
existing form actions, HTMX attributes, URL names, permission checks, field
names, and pagination parameters unchanged.

- [ ] **Step 4: Make tables responsive**

Desktop tables use sticky headers where useful and semantic status badges.
Learner and staff lists render a mobile card representation below `md`, while
the full table remains available from `md` upward. Both representations use the
same queryset and links.

- [ ] **Step 5: Redesign detail and form screens**

Use summary cards and section navigation on learner details. Group admission,
transfer, staff, and academic forms into `.elora-form-section` panels with a
sticky desktop action area and a normal-flow mobile action area.

- [ ] **Step 6: Build, test, and browser-check**

```powershell
$env:Path = "C:\Program Files\nodejs;$env:Path"
& "C:\Program Files\nodejs\npm.cmd" run css:build
python -m pytest apps/learners apps/staff apps/academics -v
```

Verify list, empty, search, detail, and form states in the browser.

- [ ] **Step 7: Commit people and academics**

```powershell
& "C:\Program Files\Git\cmd\git.exe" add templates/learners templates/staff templates/academics apps/learners/tests/test_views.py apps/staff/tests/test_views.py apps/academics/tests/test_views.py
& "C:\Program Files\Git\cmd\git.exe" commit -m "feat: redesign people and academic pages"
```

## Task 6: Redesign Daily Academic Workflows

**Files:**
- Modify: `templates/attendance/index.html`
- Modify: `templates/attendance/learner_register.html`
- Modify: `templates/attendance/staff_register.html`
- Modify: `templates/attendance/correct.html`
- Modify: `templates/attendance/partials/register_table.html`
- Modify: `templates/assessments/index.html`
- Modify: `templates/learning/index.html`
- Modify: `templates/timetabling/index.html`
- Modify: `templates/timetabling/detail.html`
- Modify: `templates/timetabling/schedule.html`
- Modify: `templates/reports/index.html`
- Modify: corresponding tests under `apps/attendance/tests/`, `apps/assessments/tests/`, `apps/learning/tests/`, `apps/timetabling/tests/`, and `apps/reports/tests/`

- [ ] **Step 1: Add failing workflow UI assertions**

Assert shared headers, KPI components, status legends, visible form labels,
HTMX indicators, empty states, and permission-aware actions. Preserve existing
behavior assertions.

- [ ] **Step 2: Run focused workflow tests**

```powershell
python -m pytest apps/attendance apps/assessments apps/learning apps/timetabling apps/reports -v
```

Expected: new UI assertions FAIL; existing behavioral assertions remain PASS.

- [ ] **Step 3: Apply shared layouts**

Use page headers, metric cards, panel shells, filters, and empty states.
Attendance registers prioritize fast status entry. Assessments show the four CBC
rating tones consistently. Timetables prioritize conflict visibility. Reports
prioritize publishing state and download actions.

- [ ] **Step 4: Add HTMX loading and error feedback**

Mark asynchronous regions with `aria-busy` during requests, display scoped
indicators, disable the initiating submit control until completion, and focus
the updated heading or error summary after a swap.

- [ ] **Step 5: Build, test, and browser-check**

```powershell
$env:Path = "C:\Program Files\nodejs;$env:Path"
& "C:\Program Files\nodejs\npm.cmd" run css:build
python -m pytest apps/attendance apps/assessments apps/learning apps/timetabling apps/reports -v
```

Verify register entry, assessment listing, assignment workflow, timetable
schedule, and report-card listing on desktop and mobile.

- [ ] **Step 6: Commit academic workflows**

```powershell
& "C:\Program Files\Git\cmd\git.exe" add templates/attendance templates/assessments templates/learning templates/timetabling templates/reports apps/attendance/tests apps/assessments/tests apps/learning/tests apps/timetabling/tests apps/reports/tests static/js/app.js
& "C:\Program Files\Git\cmd\git.exe" commit -m "feat: redesign daily academic workflows"
```

## Task 7: Redesign Operations And Engagement Modules

**Files:**
- Modify: `templates/finance/index.html`
- Modify: `templates/finance/receipt.html`
- Modify: `templates/finance/statement.html`
- Modify: `templates/communication/index.html`
- Modify: `templates/library/index.html`
- Modify: `templates/wellbeing/index.html`
- Modify: `templates/activities/index.html`
- Modify: corresponding tests under `apps/finance/tests/`, `apps/communication/tests/`, `apps/library/tests/`, `apps/wellbeing/tests/`, and `apps/activities/tests/`

- [ ] **Step 1: Add failing module UI tests**

Require shared page markers, finance KPI cards, semantic payment statuses,
communication activity states, borrowing status, wellbeing privacy cues, and
activity participation states.

- [ ] **Step 2: Run focused tests and verify failure**

```powershell
python -m pytest apps/finance apps/communication apps/library apps/wellbeing apps/activities -v
```

- [ ] **Step 3: Apply the shared component system**

Finance uses strong numeric hierarchy, KES formatting, and status badges.
Communication uses tabs or sections for announcements, messages, and
notifications. Library uses availability and overdue states. Wellbeing uses
restrained privacy-aware styling. Activities uses participation cards and
status filters.

- [ ] **Step 4: Preserve print views**

Keep receipt and statement print output free from the application sidebar. Add
screen-only action bars and explicit `@media print` rules that hide navigation
and controls.

- [ ] **Step 5: Build, test, and browser-check**

```powershell
$env:Path = "C:\Program Files\nodejs;$env:Path"
& "C:\Program Files\nodejs\npm.cmd" run css:build
python -m pytest apps/finance apps/communication apps/library apps/wellbeing apps/activities -v
```

Verify finance, receipt print preview, communication, library, wellbeing, and
activities in both themes.

- [ ] **Step 6: Commit operations modules**

```powershell
& "C:\Program Files\Git\cmd\git.exe" add templates/finance templates/communication templates/library templates/wellbeing templates/activities apps/finance/tests apps/communication/tests apps/library/tests apps/wellbeing/tests apps/activities/tests
& "C:\Program Files\Git\cmd\git.exe" commit -m "feat: redesign operations and engagement pages"
```

## Task 8: Finish Public, Error, Empty, And Permission States

**Files:**
- Modify: `templates/layouts/public.html`
- Modify: `templates/accounts/login.html`
- Modify: `templates/403.html`
- Modify: `templates/404.html`
- Modify: `templates/500.html`
- Modify: `apps/accounts/tests/test_auth_views.py`
- Modify: `apps/core/tests/test_ui_shell.py`

- [ ] **Step 1: Add failing public-state tests**

Assert branded identity, form labels, error summary, password field attributes,
and consistent error-page actions:

```python
assert "Powering Modern Education" in content
assert 'autocomplete="current-password"' in content
assert 'data-public-shell' in content
assert "Return to dashboard" in forbidden_content
```

- [ ] **Step 2: Run tests and verify failure**

```powershell
python -m pytest apps/accounts/tests/test_auth_views.py apps/core/tests/test_ui_shell.py -v
```

- [ ] **Step 3: Redesign public and error pages**

Create a two-panel desktop login layout that collapses to one column on mobile.
Keep authentication behavior unchanged. Give 403, 404, and 500 pages concise
messages, branded illustration-free layouts, and safe navigation actions.

- [ ] **Step 4: Test and browser-check**

```powershell
$env:Path = "C:\Program Files\nodejs;$env:Path"
& "C:\Program Files\nodejs\npm.cmd" run css:build
python -m pytest apps/accounts/tests/test_auth_views.py apps/core/tests/test_ui_shell.py -v
```

Verify login errors, mobile login, 403, and 404 in both themes where applicable.

- [ ] **Step 5: Commit public states**

```powershell
& "C:\Program Files\Git\cmd\git.exe" add templates/layouts/public.html templates/accounts templates/403.html templates/404.html templates/500.html apps/accounts/tests/test_auth_views.py apps/core/tests/test_ui_shell.py
& "C:\Program Files\Git\cmd\git.exe" commit -m "feat: redesign authentication and error states"
```

## Task 9: Accessibility And Responsive Audit

**Files:**
- Modify: `assets/css/input.css`
- Modify: `static/js/app.js`
- Modify: affected templates discovered by the audit
- Modify: `apps/core/tests/test_ui_shell.py`

- [ ] **Step 1: Add regression assertions**

Assert one `main` landmark, one page `h1`, labeled icon controls, dialog labels,
skip link, no duplicate navigation IDs, and table captions or accessible names
on representative pages.

- [ ] **Step 2: Run the shell and representative module tests**

```powershell
python -m pytest apps/core/tests/test_ui_shell.py apps/analytics/tests/test_dashboards.py apps/learners/tests/test_views.py apps/attendance/tests/test_views.py apps/finance/tests/test_views.py -v
```

- [ ] **Step 3: Audit browser interactions**

At 390x844, 768x1024, 1366x768, and 1536x960:

- Navigate with keyboard only
- Verify focus visibility and logical order
- Open and close sidebar, dropdowns, and any modal with keyboard
- Verify light and dark contrast
- Check reduced-motion behavior
- Check table/card transformations and chart containment
- Confirm no horizontal page overflow

- [ ] **Step 4: Fix discovered issues**

Limit edits to concrete audit findings. Add missing labels, focus return, color
adjustments, overflow containment, or responsive breakpoints, then rebuild CSS.

- [ ] **Step 5: Rerun focused tests**

```powershell
$env:Path = "C:\Program Files\nodejs;$env:Path"
& "C:\Program Files\nodejs\npm.cmd" run css:build
python -m pytest apps/core/tests/test_ui_shell.py apps/analytics/tests/test_dashboards.py apps/learners/tests/test_views.py apps/attendance/tests/test_views.py apps/finance/tests/test_views.py -v
```

- [ ] **Step 6: Commit audit fixes**

```powershell
& "C:\Program Files\Git\cmd\git.exe" add templates assets/css/input.css static/css/app.css static/js/app.js apps/core/tests/test_ui_shell.py
& "C:\Program Files\Git\cmd\git.exe" commit -m "fix: complete responsive accessibility audit"
```

## Task 10: Full Verification And Preview Handoff

**Files:**
- Modify only files required by verified regressions

- [ ] **Step 1: Run formatting and static checks**

```powershell
python -m ruff check .
python -m mypy apps
```

Expected: both commands exit successfully.

- [ ] **Step 2: Run the complete test suite**

```powershell
python -m pytest -v
```

Expected: all tests PASS.

- [ ] **Step 3: Rebuild production CSS**

```powershell
$env:Path = "C:\Program Files\nodejs;$env:Path"
& "C:\Program Files\nodejs\npm.cmd" run css:build
```

Expected: minified `static/css/app.css` is generated successfully.

- [ ] **Step 4: Run Django deployment checks**

```powershell
python manage.py check
python manage.py check --deploy --settings=config.settings.production
```

Expected: local check passes; deployment check contains no unaddressed project
configuration errors.

- [ ] **Step 5: Complete browser route matrix**

Using the seeded school administrator, inspect:

```text
/dashboard/
/academics/
/staff/
/learners/
/attendance/
/timetables/
/assessments/
/reports/
/finance/
/learning/
/communication/
/library/
/wellbeing/
/activities/
```

For each route verify the shared shell, active navigation, page header, content
panels, empty or populated state, dark mode, mobile layout, and absence of
console errors.

- [ ] **Step 6: Verify representative roles**

Sign in as teacher, parent, learner, accountant, librarian, and guidance
counsellor demo users. Confirm role dashboards and sidebar links do not expose
unauthorized modules or actions.

- [ ] **Step 7: Commit final verified corrections**

```powershell
& "C:\Program Files\Git\cmd\git.exe" add -u
& "C:\Program Files\Git\cmd\git.exe" commit -m "fix: finalize Elora UI redesign"
```

Skip this commit only when verification required no corrections.

- [ ] **Step 8: Leave the preview open**

Keep the local server running and navigate the in-app browser to:

```text
http://green-hills.localhost:56273/dashboard/
```

Provide a concise completion summary with test results and the preview URL.
