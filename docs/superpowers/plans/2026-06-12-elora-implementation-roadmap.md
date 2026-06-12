# Elora Implementation Roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver Elora as a sequence of production-shaped, testable increments that collectively satisfy the approved platform design.

**Architecture:** Elora is a modular Django monolith with PostgreSQL tenant isolation, Redis and Celery for background work, server-rendered Tailwind/HTMX interfaces, and domain apps under `apps/`. Each milestone leaves the application runnable and adds one coherent group of business workflows without weakening the tenant and permission foundation.

**Tech Stack:** Python 3.13, Django 5.2, PostgreSQL, Redis, Celery, Tailwind CSS, HTMX, Alpine.js, Chart.js, pytest, Playwright, Docker Compose

---

## Repository Map

```text
Elora/
├── apps/
│   ├── core/
│   ├── tenancy/
│   ├── accounts/
│   ├── learners/
│   ├── staff/
│   ├── academics/
│   ├── attendance/
│   ├── assessments/
│   ├── reports/
│   ├── timetable/
│   ├── learning/
│   ├── finance/
│   ├── communications/
│   ├── library/
│   ├── wellbeing/
│   ├── activities/
│   └── analytics/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   ├── test.py
│   │   └── production.py
│   ├── asgi.py
│   ├── celery.py
│   ├── urls.py
│   └── wsgi.py
├── templates/
├── static/
├── assets/
├── tests/
├── docker/
├── docs/
├── manage.py
├── pyproject.toml
├── package.json
├── Dockerfile
└── compose.yaml
```

## Milestone Order

### Milestone 1: Platform Foundation

Detailed plan: `docs/superpowers/plans/2026-06-12-elora-foundation.md`

Delivers:

- Django project, locked tooling, Docker development stack, and CI
- School, domain, global user, membership, role, and audit models
- Subdomain tenant resolution and defense-in-depth school scoping
- Branded login, role-aware navigation, and dashboard routing
- Base Tailwind/HTMX/Alpine interface
- Seeded schools and users for every requested role

Exit test: two schools can use the same deployment without reading or mutating each other's data, and every role reaches an authorized dashboard.

### Milestone 2: People And Academic Structure

Delivers:

- Learners, parents, guardians, teachers, departments, and staff assignments
- Admissions, enrollment history, medical summaries, and transfers
- Academic years, terms, grades, streams, learning areas, strands, sub-strands, outcomes, and competencies
- School-scoped forms, tables, search, filters, admin, and imports

Exit test: a school can admit a learner, link guardians, assign staff, configure a CBC structure, enroll the learner, and transfer the learner while preserving history.

### Milestone 3: Attendance And Timetabling

Delivers:

- Learner and staff attendance registers
- Bulk entry, corrections, absence alerts, summaries, and exports
- Rooms, timetable slots, class and teacher schedules
- Teacher, room, stream, and learning-area conflict detection

Exit test: staff can publish a conflict-free timetable and complete a daily attendance cycle with audited corrections and alerts.

### Milestone 4: Assessments And Report Cards

Delivers:

- Formative and summative assessments
- Rubrics, learning outcomes, competencies, evidence, portfolios, and four default ratings
- Result entry, completeness validation, moderation, approval, and publication
- Immutable report snapshots, comments, principal remarks, attendance summaries, and asynchronous PDF generation

Exit test: a teacher records CBC evidence, a Department Head moderates it, a Principal approves it, and a parent downloads the authorized published report.

### Milestone 5: Finance And Parent/Learner Portals

Delivers:

- Fee structures, invoice runs, payments, allocations, reversals, receipts, balances, and statements
- Parent and learner dashboards with strict relationship scoping
- Linked attendance, academic, report, finance, and notification views

Exit test: an accountant invoices a class, allocates payment, issues a receipt, and the correct parent sees the updated statement without seeing another learner.

### Milestone 6: Learning And Communication

Delivers:

- Assignments, submissions, resources, notes, videos, and feedback
- Announcements, notifications, delivery records, and parent-teacher messaging
- Email-ready asynchronous delivery architecture

Exit test: a teacher publishes an assignment and announcement, a learner submits work, and an authorized parent receives the related notification.

### Milestone 7: Library, Wellbeing, And Activities

Delivers:

- Books, copies, loans, returns, overdue handling, and fines
- Discipline, positive conduct, counselling, and restricted records
- Clubs and activity participation
- Baseline search, reporting, permissions, and audit workflows

Exit test: each extension module supports an authorized daily workflow and rejects unauthorized or cross-school access.

### Milestone 8: Analytics And Production Hardening

Delivers:

- Role-focused dashboards and accessible Chart.js analytics
- Aggregation tasks and exports
- Production settings, health/readiness checks, structured logging, and monitoring hooks
- Upload hardening, authentication rate limits, RLS rollout, backup/restore procedures, and operator guides
- Browser smoke tests, accessibility checks, dependency audit, and deployment verification

Exit test: CI passes, `manage.py check --deploy` passes against production settings, backups restore successfully in a documented rehearsal, and critical browser journeys pass on mobile and desktop viewports.

## Cross-Milestone Rules

Every milestone must:

1. Start with failing tests for the behavior it introduces.
2. Scope all tenant-owned records by an explicit `School`.
3. Add object-level authorization tests for affected roles.
4. Add admin configuration and deterministic seed coverage for new models.
5. Preserve full-page behavior when HTMX is unavailable.
6. Add audit events for sensitive state changes.
7. Run the complete test suite before completion.
8. Update the README and operator documentation when setup or operations change.

## Release Gate

The first production release is complete only after all eight milestone exit tests pass and every acceptance criterion in `docs/superpowers/specs/2026-06-12-elora-platform-design.md` has a corresponding automated test or documented operational verification.
