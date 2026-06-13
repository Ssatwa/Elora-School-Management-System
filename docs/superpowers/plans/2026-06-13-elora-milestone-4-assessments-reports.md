# Elora Milestone 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver complete CBC assessment, moderation, approval, immutable report-card snapshot, PDF generation, publication, and authorized parent download workflows.

**Architecture:** Add `assessments` for school-owned rating levels, rubrics, criteria, assessments, learner results, criterion ratings, evidence, and workflow history. Add `reports` for immutable term snapshots, generation jobs, ReportLab PDFs, publication, and relationship-scoped downloads. All mutations use transactional services, enforce school boundaries and role ownership, and create audit events.

**Tech Stack:** Python 3.13, Django 5.2, Celery 5.6, ReportLab 4.5.1, Tailwind CSS, HTMX, pytest

---

## Task 1: CBC Assessment Domain

**Files:**
- Create: `apps/assessments/models.py`
- Create: `apps/assessments/admin.py`
- Create: `apps/assessments/tests/test_models.py`
- Modify: `config/settings/base.py`

- [ ] Write failing tests for four default rating codes, school isolation, rubric/outcome relationships, unique learner results, criterion ratings, evidence metadata, and protected history.
- [ ] Implement `RatingLevel`, `Rubric`, `RubricCriterion`, `Assessment`, `AssessmentResult`, `CriterionRating`, `Evidence`, and `AssessmentWorkflowEvent`.
- [ ] Generate migrations, rerun focused tests, and commit.

## Task 2: Result And Approval Workflow

**Files:**
- Create: `apps/assessments/services.py`
- Create: `apps/assessments/permissions.py`
- Create: `apps/assessments/tests/test_services.py`

- [ ] Write failing tests for teacher result entry, evidence, completeness validation, Department Head moderation, Principal approval, invalid transitions, rollback, and audit history.
- [ ] Implement transactional `record_result`, `submit_assessment`, `moderate_assessment`, and `approve_assessment`.
- [ ] Require results for every active learner and criterion before submission.
- [ ] Commit after focused tests pass.

## Task 3: Immutable Reports And PDF Jobs

**Files:**
- Create: `apps/reports/models.py`
- Create: `apps/reports/services.py`
- Create: `apps/reports/pdf.py`
- Create: `apps/reports/tasks.py`
- Create: `apps/reports/tests/test_reports.py`
- Modify: `config/settings/base.py`
- Modify: `pyproject.toml`

- [ ] Write failing tests for snapshot contents, attendance totals, immutability, idempotent generation jobs, valid PDF output, checksum, publication, and retry state.
- [ ] Implement `ReportCard` and `ReportGenerationJob`.
- [ ] Build snapshots only from approved assessments and current term attendance.
- [ ] Generate professional CBC PDFs with learner details, ratings, comments, competencies, attendance, and principal remarks.
- [ ] Commit after focused tests pass.

## Task 4: Assessment And Report Interfaces

**Files:**
- Create: `apps/assessments/forms.py`
- Create: `apps/assessments/views.py`
- Create: `apps/assessments/urls.py`
- Create: `templates/assessments/*.html`
- Create: `apps/assessments/tests/test_views.py`
- Create: `apps/reports/views.py`
- Create: `apps/reports/urls.py`
- Create: `templates/reports/*.html`
- Create: `apps/reports/tests/test_views.py`
- Modify: `config/urls.py`
- Modify: `apps/accounts/context_processors.py`
- Modify: `templates/components/sidebar.html`

- [ ] Write failing tests for RBAC, tenant isolation, entry, moderation, approval, publication, parent relationship scoping, and PDF download.
- [ ] Build responsive role-aware assessment queues, result entry, moderation panels, report lists, generation state, and downloads.
- [ ] Commit after focused tests pass.

## Task 5: Seed, RLS, Operations, And Exit Workflow

**Files:**
- Modify: `apps/core/management/commands/seed_demo.py`
- Create: `apps/tenancy/migrations/0005_milestone_4_rls.py`
- Modify: `apps/tenancy/tests/test_rls.py`
- Create: `apps/reports/tests/test_exit_workflow.py`
- Create: `docs/operations/assessments-report-cards.md`
- Modify: `README.md`

- [ ] Seed deterministic ratings, rubric, approved assessment, learner result, evidence metadata, published report, and PDF for both demo schools.
- [ ] Add PostgreSQL RLS to every new tenant table.
- [ ] Verify the exit workflow from teacher evidence through Department Head moderation, Principal approval, report publication, and authorized parent download.
- [ ] Run full pytest, migrations, checks, Ruff, mypy, CSS build, production checks, dependency audits, fresh migration/seed, and browser smoke tests.
- [ ] Commit and merge only after every gate passes.
