# Elora Milestone 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver audited learner and staff attendance cycles plus conflict-free, publishable school timetables with class and teacher schedule views.

**Architecture:** Add two bounded Django apps. `attendance` owns daily registers, entries, corrections, absence alerts, summaries, and CSV exports; `timetabling` owns rooms, teaching periods, timetable versions, entries, conflict validation, and publication. All records are school-scoped through `TenantManager`, cross-school references fail validation, workflow mutations are transactional services, and privileged operations create audit events.

**Tech Stack:** Python 3.13, Django 5.2, PostgreSQL/SQLite, Tailwind CSS, HTMX, pytest, factory-boy

---

## Model Map

### `apps/attendance`

- `AttendanceRegister`: school, date, session, subject type, stream, status, marked-by metadata
- `LearnerAttendanceEntry`: register, learner, status, arrival time, note
- `StaffAttendanceEntry`: register, teacher, status, arrival time, note
- `AttendanceCorrection`: immutable before/after values, reason, requested/applied actor
- `AbsenceAlert`: learner or teacher target, attendance date, status, recipient summary

### `apps/timetabling`

- `Room`: school, code, name, capacity, active status
- `TimetablePeriod`: school, weekday, sequence, start/end time, break status
- `Timetable`: school, academic year, term, name, status, publication metadata
- `TimetableEntry`: timetable, period, stream, learning area, teacher, room

## Roles

- Attendance view: school admin, principal, deputy principal, teacher, class teacher, department head, guidance counsellor
- Learner register entry: school admin, principal, deputy principal, class teacher
- Staff register entry and corrections: school admin, principal, deputy principal
- Timetable view: school admin, principal, deputy principal, teacher, class teacher, department head
- Timetable administration/publication: school admin, principal, deputy principal

## Task 1: Attendance Domain

**Files:**
- Create: `apps/attendance/models.py`
- Create: `apps/attendance/admin.py`
- Create: `apps/attendance/tests/test_models.py`
- Modify: `config/settings/base.py`

- [ ] Write failing model tests for school isolation, one register per date/session/subject, one learner or teacher entry per register, valid target type, and immutable correction history.
- [ ] Run `..\..\.venv\Scripts\python.exe -m pytest apps/attendance/tests/test_models.py -q` and confirm collection/model failures.
- [ ] Implement the minimum models, constraints, indexes, validation, tenant managers, and admin registrations.
- [ ] Generate migrations and rerun the focused tests.
- [ ] Commit with `feat: add attendance domain models`.

## Task 2: Attendance Workflows

**Files:**
- Create: `apps/attendance/services.py`
- Create: `apps/attendance/exports.py`
- Create: `apps/attendance/tests/test_services.py`
- Create: `apps/attendance/tests/test_exports.py`

- [ ] Write failing tests for atomic bulk learner and staff marking, duplicate prevention, audited correction, absence alert creation, summary totals, and tenant-scoped CSV output.
- [ ] Confirm the tests fail because the workflow APIs do not exist.
- [ ] Implement `mark_learner_attendance`, `mark_staff_attendance`, `correct_attendance`, `attendance_summary`, and `attendance_csv`.
- [ ] Ensure invalid rows roll back the entire register and alert records are idempotent.
- [ ] Rerun focused tests and commit with `feat: add audited attendance workflows`.

## Task 3: Timetable Domain And Conflict Engine

**Files:**
- Create: `apps/timetabling/models.py`
- Create: `apps/timetabling/services.py`
- Create: `apps/timetabling/admin.py`
- Create: `apps/timetabling/tests/test_models.py`
- Create: `apps/timetabling/tests/test_services.py`
- Modify: `config/settings/base.py`

- [ ] Write failing tests for school isolation, valid periods, term/year consistency, draft-only editing, and teacher, room, stream, and duplicate learning-area conflicts.
- [ ] Confirm failures before implementation.
- [ ] Implement models plus transactional `add_timetable_entry`, `validate_timetable`, and `publish_timetable` services.
- [ ] Publication must reject conflicts, require at least one entry, timestamp the version, and record an audit event.
- [ ] Generate migrations, rerun focused tests, and commit with `feat: add conflict-aware timetables`.

## Task 4: Role-Aware Attendance Interface

**Files:**
- Create: `apps/attendance/forms.py`
- Create: `apps/attendance/views.py`
- Create: `apps/attendance/urls.py`
- Create: `apps/attendance/templates/attendance/*.html`
- Create: `apps/attendance/tests/test_views.py`
- Modify: `config/urls.py`
- Modify: `apps/accounts/context_processors.py`
- Modify: `templates/components/sidebar.html`

- [ ] Write failing view tests for role gates, tenant isolation, bulk entry, correction, summary, and CSV responses.
- [ ] Implement school-scoped forms and responsive dashboard, register, correction, alert, and report screens.
- [ ] Use HTMX for register filtering and row updates while retaining full-page POST fallbacks.
- [ ] Add role-aware navigation and rerun focused tests.
- [ ] Commit with `feat: add attendance administration UI`.

## Task 5: Role-Aware Timetable Interface

**Files:**
- Create: `apps/timetabling/forms.py`
- Create: `apps/timetabling/views.py`
- Create: `apps/timetabling/urls.py`
- Create: `apps/timetabling/templates/timetabling/*.html`
- Create: `apps/timetabling/tests/test_views.py`
- Modify: `config/urls.py`
- Modify: `apps/accounts/context_processors.py`
- Modify: `templates/components/sidebar.html`

- [ ] Write failing tests for role gates, tenant isolation, draft creation, entry conflict feedback, publication, class schedule, and teacher schedule.
- [ ] Implement responsive timetable builder and published schedule views.
- [ ] Show actionable conflict messages and prevent post-publication edits.
- [ ] Rerun focused tests and commit with `feat: add timetable planning UI`.

## Task 6: Seed, RLS, Operations, And Exit Workflow

**Files:**
- Modify: `apps/core/management/commands/seed_demo.py`
- Create: `apps/tenancy/migrations/0004_milestone_3_rls.py`
- Modify: `apps/tenancy/tests/test_rls.py`
- Create: `apps/attendance/tests/test_exit_workflow.py`
- Create: `docs/operations/attendance-timetabling.md`
- Modify: `README.md`

- [ ] Write failing tests for deterministic two-school attendance/timetable seed data and PostgreSQL RLS coverage for every new tenant table.
- [ ] Add realistic Green Hills and Sunrise registers, rooms, periods, draft/published schedules, and alerts.
- [ ] Add RLS policies using the established `app.current_school` policy pattern.
- [ ] Exercise the exit workflow: publish a conflict-free timetable, complete a learner attendance register, correct an entry, generate an alert, and export the summary.
- [ ] Build CSS and run migrations, `check`, full pytest, Ruff, mypy, production deploy checks, and dependency audits.
- [ ] Commit with `feat: seed and harden milestone 3 operations`.

## Completion Evidence

- Full suite passes under SQLite; PostgreSQL-only RLS tests are explicitly identified if PostgreSQL is unavailable.
- `makemigrations --check --dry-run`, Django system checks, Ruff, and mypy pass.
- Fresh migration and deterministic seed succeed.
- Attendance and timetable pages return successful responses for authorized users and deny unauthorized roles.
- Browser review remains available from the stable `main` preview until the verified milestone is merged.
