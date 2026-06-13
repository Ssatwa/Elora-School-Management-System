# Elora Milestone 5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver auditable school finance workflows and relationship-scoped parent and learner portal views.

**Architecture:** Add a tenant-owned `finance` domain with immutable invoices, payments, allocations, receipts, and service-layer transactions. Reuse existing learner, enrollment, guardian, membership, attendance, assessment, and report-card records for portal aggregation.

**Tech Stack:** Django 5.2, PostgreSQL/SQLite, Tailwind templates, pytest, Celery-ready services.

---

### Task 1: Finance Domain

- [ ] Write failing model and service tests for fee structures, invoice runs, payment allocation, balances, receipts, and reversals.
- [ ] Implement tenant-scoped finance models, validation, services, migrations, and admin.
- [ ] Verify finance tests and migration consistency.

### Task 2: Finance And Portal Interfaces

- [ ] Write failing view tests for accountant access, parent relationship scoping, and cross-school denial.
- [ ] Implement finance dashboard, learner statements, receipt downloads, URLs, navigation, and role permissions.
- [ ] Add deterministic finance seed records for both demo schools.

### Task 3: Hardening And Exit Workflow

- [ ] Add PostgreSQL RLS coverage for every finance table.
- [ ] Add an exit test covering invoice, payment, receipt, and parent visibility.
- [ ] Run pytest, ruff, mypy, Django checks, and migration drift checks.
- [ ] Commit, merge, migrate, seed, and refresh the browser preview.
