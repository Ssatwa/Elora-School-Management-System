# Elora Platform Design

**Product:** Elora School Management System  
**Tagline:** Powering Modern Education  
**Date:** 2026-06-12  
**Status:** Approved design

## 1. Product Goal

Elora is a production-ready, multi-school SaaS platform for Kenyan competency-based education schools. It combines academic, operational, financial, communication, and learner-support workflows in one responsive Django application.

The product must feel credible as a commercial daily-use platform. It must prioritize tenant isolation, reliable school records, accessible mobile workflows, clear role boundaries, and configurable curriculum structures.

## 2. Delivery Scope

The first production release uses a depth-based scope.

### Full-depth core modules

- Accounts, authentication, RBAC, profiles, and audit logs
- School and tenant administration
- Learners, admissions, guardians, medical summaries, and transfers
- Teachers, assignments, departments, workloads, and performance summaries
- Academic years, terms, grades, streams, learning areas, strands, sub-strands, outcomes, and competencies
- Learner and teacher attendance with alerts and reports
- CBC assessments, rubrics, evidence, moderation, portfolios, and competency ratings
- Versioned CBC report cards and PDF generation
- Timetables with teacher, room, and class conflict detection
- Finance, including fees, invoices, payments, allocations, receipts, balances, and statements
- Parent portal for linked learners
- Role-specific dashboards and analytics

### Usable extension modules

These modules receive complete tenant scoping, permissions, CRUD workflows, search, filtering, audit history, and baseline reporting:

- Learning assignments, submissions, resources, notes, videos, and feedback
- Announcements, notifications, and parent-teacher messaging
- Library catalogue, borrowing, returns, and fines
- Discipline, positive conduct, and counselling records
- Clubs, sports, arts, leadership, and community service

The architecture preserves clear domain boundaries so extension modules can deepen without splitting the system into distributed services.

## 3. Architecture

Elora is a modular Django monolith deployed as one web application with background workers.

### Runtime components

- Django 5.2 or a later compatible Django 5 release
- Python 3.13 or later
- PostgreSQL as the authoritative data store
- Redis for cache, task broker, and short-lived coordination
- Celery workers for asynchronous jobs
- Celery Beat for scheduled jobs
- Django templates with Tailwind CSS
- HTMX for server-rendered partial updates
- Alpine.js for local interface state
- Chart.js for analytics visualizations
- ASGI application server behind a reverse proxy

### Django application boundaries

- `core`: shared model primitives, utilities, health checks, and common UI
- `tenancy`: schools, domains, branding, settings, and tenant resolution
- `accounts`: custom users, memberships, roles, permissions, profiles, sessions, and audits
- `learners`: learners, guardians, admissions, medical records, and transfers
- `staff`: teachers, departments, assignments, workloads, and staff attendance links
- `academics`: academic calendars, classes, curriculum structures, and competencies
- `attendance`: learner and staff attendance, alerts, summaries, and reports
- `assessments`: assessment definitions, rubrics, evidence, results, moderation, and portfolios
- `reports`: report-card snapshots, comments, approvals, publication, and PDF generation
- `timetable`: timetable entries, rooms, constraints, and conflict checks
- `learning`: assignments, submissions, resources, and feedback
- `finance`: fee structures, invoices, payments, allocations, receipts, and statements
- `communications`: announcements, messages, notifications, and delivery records
- `library`: books, copies, loans, returns, and fines
- `wellbeing`: discipline, positive conduct, counselling, and restricted notes
- `activities`: clubs and participation
- `analytics`: dashboard queries, aggregates, trends, and exports

Domain logic belongs in focused services and query APIs rather than large views, templates, model signals, or cross-application imports.

## 4. Multi-Tenancy

Schools access Elora through subdomains such as `schoolname.elora.co.ke`.

### Tenant resolution

1. Host validation rejects unknown or malformed hosts.
2. Tenant middleware resolves the active school from the subdomain.
3. Suspended or inactive schools receive a controlled unavailable response.
4. The active school is attached to the request and database session.
5. Authentication verifies that the user has an active membership in that school.

### Isolation strategy

Elora uses a shared PostgreSQL database and schema. Every tenant-owned record has a required `school_id` foreign key.

Isolation is enforced through:

- Tenant-aware queryset managers
- Service methods that require an explicit school
- School-scoped forms and choice querysets
- View permission checks
- Unique constraints that include `school_id`
- PostgreSQL row-level security policies
- Tests that attempt cross-school reads and writes

Platform-owned tables, such as global users and platform audit records, are explicitly identified and do not inherit the tenant model base.

Background tasks always receive a school identifier and establish tenant context before accessing tenant-owned data.

## 5. Identity And Access

Elora uses a custom email-based Django user model from the first migration.

### Identity structure

- A user is a global identity.
- A school membership links a user to a school.
- A membership may carry multiple roles.
- A person may belong to more than one school.
- Learner, parent, and staff profiles link to the appropriate membership or user.

### Roles

- Super Admin: platform-wide provisioning, support, configuration, and platform audit
- School Admin: tenant configuration and broad school operations
- Principal: school oversight, approvals, reports, and analytics
- Deputy Principal: delegated administration, discipline, attendance, and academic oversight
- Teacher: assigned classes, attendance, learning, and assessments
- Class Teacher: teacher permissions plus assigned-stream pastoral and report responsibilities
- Department Head: department curriculum, staff, moderation, and performance oversight
- Parent: records for explicitly linked learners only
- Learner: own learning, attendance, results, reports, and communication only
- Accountant: finance workflows and financial reporting
- Librarian: catalogue and circulation workflows
- Guidance & Counselling Officer: authorized wellbeing workflows with restricted confidentiality

Super Admin is platform-scoped. Every other role is school-scoped.

### Authorization

Roles provide permission bundles, but permissions are checked at action and object level. Duties such as class teaching, department leadership, learner guardianship, and counselling authorization further constrain access.

Sensitive records, including medical, financial, counselling, and safeguarding information, receive narrower permissions and dedicated audit events.

Each tenant has a branded login page. Successful authentication redirects users to the dashboard appropriate to their active school and role set.

## 6. Shared Data Conventions

Tenant-owned domain models use:

- UUID primary keys
- Required `school_id`
- Created and updated timestamps
- Creator and updater references where operationally important
- Active or lifecycle status
- Database indexes for school, status, date, and common lookup fields
- Explicit uniqueness constraints within each school

Operational records are archived or transitioned through statuses instead of being deleted when deletion would damage auditability.

Amounts use fixed-precision decimals and an explicit currency. Dates and times are timezone-aware. Human-facing identifiers such as admission numbers, invoice numbers, and receipt numbers use school-scoped sequences.

## 7. Academic And CBC Model

### Academic organization

- Academic Year contains Terms.
- Grade belongs to a school and education level.
- Stream belongs to a Grade and academic context.
- Enrollment records preserve a learner's grade and stream history.

### Curriculum organization

- Learning Area
- Strand
- Sub-Strand
- Learning Outcome
- Competency

Competencies are reusable and can link to learning outcomes, rubric criteria, assessment results, evidence, and report-card sections.

Curriculum names, grade structures, rating scales, and templates are configurable per school. Seed data provides sensible Kenyan CBC defaults without making regulatory terminology immutable.

### Assessment workflow

1. Authorized staff create formative or summative assessments.
2. Assessments target a class, learning area, outcomes, and term.
3. Rubric criteria define scoring or competency-rating expectations.
4. Teachers enter results and optional evidence.
5. Validation detects incomplete or invalid entries.
6. Department Heads or authorized leaders moderate results where configured.
7. Results are published to learners and parents only after approval.

The default competency ratings are:

- Exceeding Expectation
- Meeting Expectation
- Approaching Expectation
- Below Expectation

Schools may customize labels and presentation while preserving stable internal codes.

### Report cards

Report cards are immutable versioned snapshots created from approved results, attendance summaries, competencies, comments, and principal remarks. Reissuing a report creates a new version and records the reason, approver, and timestamp.

PDF generation runs asynchronously and stores a controlled artifact. Parents and learners can only access published versions.

## 8. Core Workflows

### Admissions

Application, learner creation, guardian linking, document capture, medical summary, admission-number allocation, class placement, and enrollment complete as one validated workflow.

### Transfers

Transfers preserve historical enrollment and school records. Export packages include only approved data and record who generated them.

### Attendance

Authorized staff can mark attendance in bulk for a date and session. Duplicate registers are prevented. Absence rules produce alerts and summaries. Corrections retain an audit trail.

### Timetables

Timetable creation checks overlapping teacher, stream, room, and subject assignments. Published schedules are separately visible by class and teacher.

### Finance

Fee structures generate invoices by academic context. Payments are immutable transactions allocated to invoices. Corrections use reversals or adjustments rather than editing settled records. Receipt numbers are school-scoped and non-reusable.

### Parent portal

Parents see only linked learners. The portal provides attendance, assessments, published reports, fee balances, receipts, announcements, and authorized messaging.

## 9. Interface System

The interface uses a modern, professional education SaaS style with Inter typography.

### Application shell

- School identity and branding
- Responsive collapsible navigation
- Role-aware module links
- Global search
- Notifications
- User and school switchers where applicable
- Contextual quick actions
- Breadcrumbs and page-level actions

### Dashboard patterns

Dashboards combine:

- Key metric cards
- Trend charts
- Pending tasks and approvals
- Alerts and exceptions
- Recent activity
- Compact operational tables
- Quick actions

Each role receives a focused dashboard rather than a generic menu of every module.

### Interaction rules

- Server-rendered HTML remains the default.
- HTMX updates tables, forms, filters, modals, and status panels.
- Alpine.js controls purely local states such as navigation, disclosure, and menus.
- Full page transitions remain functional without client-side routing.
- Forms provide field-level and summary validation.
- Destructive or irreversible operations require explicit confirmation.
- Tables collapse into usable mobile cards or horizontally scroll where appropriate.

Charts include adjacent summaries or accessible data tables. Keyboard navigation, focus indicators, labels, contrast, reduced-motion preferences, and semantic HTML are required.

## 10. Background Processing

Celery handles:

- PDF report generation
- Bulk invoice generation
- Email and notification delivery
- Absence alerts
- Data exports
- Analytics aggregation
- Scheduled reminders

Jobs are idempotent where retries are possible. Job records capture state, attempts, errors, and relevant school context. User-facing screens display pending, completed, or failed states without blocking web requests.

## 11. Security

- Production is HTTPS-only.
- `DEBUG` is disabled outside development.
- Secrets are loaded from environment variables.
- Host validation supports only known platform and tenant domains.
- Session and CSRF cookies are secure in production.
- Authentication is rate limited.
- Password reset tokens and sessions follow Django security guidance.
- Django template auto-escaping remains enabled.
- User uploads are validated for type and size and stored outside executable paths.
- Permission checks protect both pages and HTMX endpoints.
- Sensitive fields are excluded from logs.
- Audit logs record authentication, authorization-sensitive changes, exports, approvals, publication, reversals, and access to restricted records.
- MFA can be enabled without replacing the user or membership model.

PostgreSQL row-level security is a defense-in-depth layer and not a substitute for application authorization.

## 12. Reliability And Error Handling

Admissions, transfers, report publication, invoice generation, payment allocation, and other multi-record operations use database transactions.

Expected user errors return clear validation messages. Authorization failures return controlled 403 responses. Unknown tenants return a neutral tenant-not-found page. Unexpected exceptions are logged with request and tenant correlation identifiers without exposing sensitive information.

Custom 400, 403, 404, 429, and 500 templates match the Elora interface.

## 13. Deployment

The repository includes:

- Multi-stage production Dockerfile
- Docker Compose development environment
- PostgreSQL, Redis, web, worker, scheduler, and asset services
- Non-root production runtime
- Health and readiness checks
- Startup migration and static-collection guidance
- Environment variable example file without secrets
- Persistent media and database volume guidance
- Reverse proxy and wildcard TLS guidance
- Backup and restore documentation

Static assets are built and fingerprinted. User media can use local development storage and an S3-compatible production backend.

## 14. Observability

- Structured application logs
- Request and tenant correlation identifiers
- Health and readiness endpoints
- Error-monitoring integration hooks
- Celery task monitoring hooks
- Audit-log search and export for authorized users
- Documented database and media backup verification

## 15. Testing And Quality

### Automated tests

- Model invariants and constraints
- Tenant isolation across querysets, forms, services, views, and tasks
- Role and object-level permissions
- Admissions, attendance, assessment, reporting, timetable, and finance workflows
- HTMX partial and full-page responses
- PDF content and access rules
- Dashboard visibility by role
- Background-job idempotency and failure handling
- Critical browser journeys

Factories create at least two schools in isolation tests. Cross-tenant access attempts must fail even when object identifiers are known.

### Continuous integration

CI runs:

- Dependency installation from locked requirements
- Formatting and lint checks
- Static type checks
- Migration consistency checks
- Unit and integration tests
- Coverage reporting
- Dependency vulnerability checks
- Production settings checks with `manage.py check --deploy`

## 16. Seed Data

Development seed data creates:

- Multiple sample schools
- Users for every role
- Academic years and terms
- Grades and streams
- CBC learning areas, strands, sub-strands, outcomes, and competencies
- Learners, guardians, and staff
- Attendance history
- Assessments and results across all rating levels
- Report cards
- Fee structures, invoices, and payments
- Announcements, books, discipline records, clubs, and participation

Seed data is deterministic, safe to rerun in development, and prohibited in production unless explicitly enabled.

## 17. Documentation

The README documents local setup, Docker setup, environment variables, migrations, asset builds, seed data, tests, common management commands, tenant domains, and production deployment.

Additional operator documentation covers:

- School provisioning
- Role and permission management
- Backup and restore
- Report and invoice job recovery
- Audit review
- Email and storage configuration

## 18. Acceptance Criteria

Elora is ready for the first production release when:

1. All listed models and domain modules exist with migrations and admin configuration.
2. Every tenant-owned query is school-scoped and cross-tenant security tests pass.
3. Each requested role can authenticate and receives an appropriate dashboard.
4. Core workflows operate end to end with validation, permissions, and audit events.
5. Extension modules provide usable authorized CRUD, search, filtering, and baseline reports.
6. CBC assessments support the four default ratings, rubrics, evidence, moderation, and publication.
7. Versioned PDF report cards include results, competencies, attendance, comments, and principal remarks.
8. Finance produces auditable invoices, payments, allocations, receipts, balances, and statements.
9. Parent and learner portals expose only authorized records.
10. The interface is responsive and usable on common mobile and desktop sizes.
11. Docker development startup, tests, seed data, and production checks are documented and reproducible.
12. CI passes all quality and security checks.

## 19. Explicit Non-Goals For The First Release

- Microservices
- Native mobile applications
- Payroll and full human-resource management
- Government-system integration without an approved external API contract
- Online payment-gateway integration without a selected provider
- Real-time video conferencing
- Custom-domain support
- Per-school databases or schemas

These capabilities may be added later without changing the approved modular-monolith and tenant-membership foundations.
