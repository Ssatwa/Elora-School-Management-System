# Elora Milestone 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver school-scoped people records, admissions, staff organization, enrollment history, transfers, and configurable Kenyan CBC academic structures.

**Architecture:** Add three bounded Django apps: `academics` owns calendars, classes, curriculum, outcomes, and competencies; `staff` owns teacher profiles, departments, and assignments; `learners` owns learner, guardian, medical, admission, enrollment, and transfer records. Multi-record workflows live in transactional services, all tenant-owned models require a school and tenant manager, and restricted operations produce audit events.

**Tech Stack:** Python 3.13, Django 5.2, PostgreSQL/SQLite, Tailwind CSS, HTMX, pytest, factory-boy

---

## Model Map

### `apps/academics`

- `AcademicYear`: school, name, dates, lifecycle status
- `Term`: school, academic year, name, sequence, dates
- `Grade`: school, code, name, education level, order
- `Stream`: school, grade, code, name, active status
- `LearningArea`: school, code, name, active status
- `Strand`: school, learning area, code, name
- `SubStrand`: school, strand, code, name
- `LearningOutcome`: school, sub-strand, code, description
- `Competency`: school, code, name, description
- `OutcomeCompetency`: school-scoped outcome-to-competency link

### `apps/staff`

- `TeacherProfile`: school, membership, employee number, TSC number, contact and employment state
- `Department`: school, code, name, optional department head
- `StaffAssignment`: school, teacher, department, learning area, grade, stream, assignment role, dates, weekly lessons

### `apps/learners`

- `Learner`: school, admission number, identity, demographics, admission date, status
- `Guardian`: school, optional membership, identity and contacts
- `LearnerGuardian`: school, learner, guardian, relationship and permissions
- `MedicalRecord`: school, learner, blood group, allergies, conditions, medication and notes
- `AdmissionApplication`: school, applicant details, desired grade, status and submitted date
- `AdmissionSequence`: school and year-specific admission-number counter
- `Enrollment`: school, learner, academic year, grade, stream, start/end dates and status
- `TransferRecord`: school, learner, destination, dates, reason, status and export metadata

## Task 1: Register Domain Apps

**Files:**
- Create: `apps/academics/apps.py`
- Create: `apps/staff/apps.py`
- Create: `apps/learners/apps.py`
- Modify: `config/settings/base.py`
- Test: `tests/test_project_bootstrap.py`

- [ ] Write a failing test asserting all three app configs are installed.
- [ ] Add package modules and app configs.
- [ ] Register apps in dependency order: academics, staff, learners.
- [ ] Run the focused bootstrap test and commit.

## Task 2: Academic Calendar And Class Structure

**Files:**
- Create: `apps/academics/models.py`
- Create: `apps/academics/migrations/0001_initial.py`
- Create: `apps/academics/tests/test_models.py`
- Modify: `tests/factories.py`

- [ ] Write model tests for school-scoped uniqueness, date validation, term ordering, and cross-school queryset isolation.
- [ ] Implement `AcademicYear`, `Term`, `Grade`, and `Stream` with UUIDs, timestamps, tenant managers, indexes, and constraints.
- [ ] Add factories for two-school isolation tests.
- [ ] Generate migrations, run focused tests, and commit.

## Task 3: CBC Curriculum Taxonomy

**Files:**
- Modify: `apps/academics/models.py`
- Create: `apps/academics/tests/test_curriculum.py`
- Modify: `tests/factories.py`

- [ ] Write failing tests for learning-area, strand, sub-strand, outcome, competency, and link invariants.
- [ ] Implement curriculum models with stable school-scoped codes and explicit parent relationships.
- [ ] Reject cross-school relationships in model validation and service/form inputs.
- [ ] Generate migrations, run focused tests, and commit.

## Task 4: Academic Administration

**Files:**
- Create: `apps/academics/admin.py`
- Create: `apps/academics/forms.py`
- Create: `apps/academics/views.py`
- Create: `apps/academics/urls.py`
- Create: `templates/academics/structure.html`
- Create: `templates/academics/partials/structure_tables.html`
- Create: `apps/academics/tests/test_views.py`
- Modify: `config/urls.py`
- Modify: `templates/components/sidebar.html`

- [ ] Write authorization tests for School Admin, Principal, Deputy Principal, Teacher, and cross-school object IDs.
- [ ] Add school-scoped forms whose relation querysets are constrained to `request.school`.
- [ ] Add searchable full-page and HTMX structure views.
- [ ] Add accessible tables and navigation for authorized roles.
- [ ] Run focused tests and commit.

## Task 5: Teacher Profiles And Departments

**Files:**
- Create: `apps/staff/models.py`
- Create: `apps/staff/migrations/0001_initial.py`
- Create: `apps/staff/tests/test_models.py`
- Modify: `tests/factories.py`

- [ ] Write tests for active school membership, employee-number uniqueness, department-head membership, and tenant isolation.
- [ ] Implement `TeacherProfile` and `Department`.
- [ ] Enforce same-school memberships through validation and service/form boundaries.
- [ ] Generate migrations, run focused tests, and commit.

## Task 6: Staff Assignments And Workloads

**Files:**
- Modify: `apps/staff/models.py`
- Create: `apps/staff/services.py`
- Create: `apps/staff/tests/test_assignments.py`
- Modify: `tests/factories.py`

- [ ] Write tests for assignment date ranges, same-school academic references, workload totals, and duplicate active assignments.
- [ ] Implement `StaffAssignment` and workload query helpers.
- [ ] Add a transactional assignment service that records an audit event.
- [ ] Generate migrations, run focused tests, and commit.

## Task 7: Staff Administration UI

**Files:**
- Create: `apps/staff/admin.py`
- Create: `apps/staff/forms.py`
- Create: `apps/staff/views.py`
- Create: `apps/staff/urls.py`
- Create: `templates/staff/index.html`
- Create: `templates/staff/partials/staff_tables.html`
- Create: `apps/staff/tests/test_views.py`
- Modify: `config/urls.py`
- Modify: `templates/components/sidebar.html`

- [ ] Write role and object-level authorization tests.
- [ ] Implement school-scoped profile, department, and assignment forms.
- [ ] Implement searchable tables and workload summary cards with HTMX partial responses.
- [ ] Run focused tests and commit.

## Task 8: Learners And Guardians

**Files:**
- Create: `apps/learners/models.py`
- Create: `apps/learners/migrations/0001_initial.py`
- Create: `apps/learners/tests/test_models.py`
- Modify: `tests/factories.py`

- [ ] Write tests for admission-number uniqueness, lifecycle status, guardian links, primary guardian rules, and tenant isolation.
- [ ] Implement `Learner`, `Guardian`, and `LearnerGuardian`.
- [ ] Keep guardian identity usable with or without a parent portal membership.
- [ ] Generate migrations, run focused tests, and commit.

## Task 9: Medical Records And Restricted Access

**Files:**
- Modify: `apps/learners/models.py`
- Create: `apps/learners/permissions.py`
- Create: `apps/learners/tests/test_medical_records.py`

- [ ] Write tests proving medical records are limited to school leadership, authorized administrators, guidance officers, and explicitly assigned class teachers.
- [ ] Implement one current medical summary per learner with school ownership.
- [ ] Add object-level permission helpers and audit restricted reads/changes.
- [ ] Generate migrations, run focused tests, and commit.

## Task 10: Transactional Admissions

**Files:**
- Modify: `apps/learners/models.py`
- Create: `apps/learners/services/admissions.py`
- Create: `apps/learners/tests/test_admissions.py`

- [ ] Write a failing exit-workflow test covering application, learner, guardians, medical summary, admission number, placement, enrollment, and audit log.
- [ ] Implement `AdmissionApplication`, `AdmissionSequence`, and `Enrollment`.
- [ ] Allocate `YYYY-NNNN` admission numbers under a locked school/year sequence.
- [ ] Implement an atomic admission service that validates every referenced object belongs to the school.
- [ ] Prove rollback leaves no partial learner when any step fails.
- [ ] Generate migrations, run focused tests, and commit.

## Task 11: Enrollment History And Transfers

**Files:**
- Modify: `apps/learners/models.py`
- Create: `apps/learners/services/transfers.py`
- Create: `apps/learners/tests/test_transfers.py`

- [ ] Write tests for closing an active enrollment, preserving history, learner status transition, export metadata, audit logging, and rollback.
- [ ] Implement `TransferRecord`.
- [ ] Implement atomic transfer initiation and completion services.
- [ ] Prevent destructive deletion of historical enrollment and completed transfer records.
- [ ] Generate migrations, run focused tests, and commit.

## Task 12: Learner Administration UI

**Files:**
- Create: `apps/learners/admin.py`
- Create: `apps/learners/forms.py`
- Create: `apps/learners/views.py`
- Create: `apps/learners/urls.py`
- Create: `templates/learners/index.html`
- Create: `templates/learners/detail.html`
- Create: `templates/learners/admit.html`
- Create: `templates/learners/transfer.html`
- Create: `templates/learners/partials/learner_table.html`
- Create: `apps/learners/tests/test_views.py`
- Modify: `config/urls.py`
- Modify: `templates/components/sidebar.html`

- [ ] Write tests for searchable lists, full-page/HTMX parity, admission form behavior, transfer workflow, restricted medical sections, and cross-school IDs.
- [ ] Implement school-scoped forms and formsets for guardian and medical data.
- [ ] Implement role-protected list, detail, admission, and transfer views.
- [ ] Add responsive cards, filters, tables, status badges, and empty states.
- [ ] Run focused tests and commit.

## Task 13: Admin, Seed Data, And RLS

**Files:**
- Modify: `apps/academics/admin.py`
- Modify: `apps/staff/admin.py`
- Modify: `apps/learners/admin.py`
- Modify: `apps/core/management/commands/seed_demo.py`
- Create: `apps/core/tests/test_milestone_2_seed.py`
- Create: `apps/tenancy/migrations/0003_milestone_2_rls.py`
- Modify: `apps/tenancy/tests/test_rls.py`

- [ ] Register all models with useful search, filters, readonly timestamps, and safe relation widgets.
- [ ] Seed deterministic academic years, terms, grades, streams, CBC structures, departments, staff, learners, guardians, and enrollments for each demo school.
- [ ] Make seed reruns idempotent.
- [ ] Add PostgreSQL RLS policies for every new tenant-owned table and integration tests when PostgreSQL is available.
- [ ] Run seed and RLS tests, then commit.

## Task 14: Exit Workflow And Documentation

**Files:**
- Create: `tests/test_milestone_2_exit_workflow.py`
- Modify: `README.md`
- Create: `docs/operations/people-academics.md`

- [ ] Add an end-to-end service/view test that admits a learner, links guardians, assigns staff, configures CBC structures, enrolls the learner, and transfers the learner while retaining history.
- [ ] Document permissions, identifiers, lifecycle transitions, imports, and operator recovery.
- [ ] Run migrations from an empty SQLite database, seed demo data, and exercise browser review pages.
- [ ] Run full pytest, coverage, Ruff, mypy, migration drift, dependency audit, production checks, Tailwind build, and Compose validation.
- [ ] Commit the completed milestone and use the branch-finishing workflow.

## Acceptance Evidence

- Every tenant-owned model has a required school, tenant manager, indexes, and school-scoped constraints.
- Two-school tests reject cross-school reads and writes through models, forms, services, views, and known object IDs.
- Admissions and transfers are atomic and audited.
- Enrollment history remains queryable after transfers.
- Medical data is excluded from ordinary teacher and parent access unless explicitly authorized.
- School administrators can configure CBC structures and manage people through responsive full-page and HTMX interfaces.
- Demo data gives every requested role a meaningful Milestone 2 review path.
