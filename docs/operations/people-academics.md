# People And Academic Operations

Milestone 2 provides school-scoped academic configuration, staff organization,
learner admissions, guardian links, medical summaries, enrollment history, and
transfers.

## Access

- School Admin, Principal, and Deputy Principal configure academic structures.
- School Admin, Principal, Deputy Principal, and Department Head administer
  staff profiles, departments, assignments, and workloads.
- Teaching and leadership roles can search learner records.
- School Admin, Principal, and Deputy Principal complete admissions and
  transfers.
- Medical summaries are restricted to leadership, School Admin, Guidance &
  Counselling, and the learner's actively assigned Class Teacher.

Every page and form resolves the active school from the request hostname.
Relation choices and object lookups are constrained to that school.

## Academic Structure

Configure academic years and terms before creating enrollment records. Grades
and streams are school-owned and reusable across academic years. Learning
areas, strands, sub-strands, outcomes, and competencies use stable
school-scoped codes so later assessments can reference them safely.

## Admissions

An admission transaction creates:

1. The admitted application state.
2. A learner with a school/year sequence number such as `2026-0001`.
3. Guardian records and relationship links.
4. One current medical summary.
5. The initial grade and stream enrollment.
6. An admission audit event.

If any referenced grade, stream, year, guardian, or learner relationship is
invalid, the entire transaction rolls back.

## Transfers

A completed transfer closes the active enrollment, changes the learner
lifecycle status to transferred, stores destination and export metadata, and
records an audit event. Historical enrollments and completed transfers use
protected relationships and must not be deleted to correct data. Record a new
authorized lifecycle action instead.

## Staff Assignments

Teacher profiles require active memberships from the same school. Department
heads and assignment references must also belong to that school. Assignment
creation rejects overlapping duplicates and records an audit event. Weekly
workload is the sum of current dated assignments.

## Demo Data

`manage.py seed_demo` creates Green Hills Academy and Sunrise Academy with role
accounts, calendars, grades, streams, CBC curriculum records, staff, learners,
guardians, medical summaries, and enrollments. It is idempotent and enabled
only in local and test settings. Production settings reject the command unless
`ALLOW_DEMO_SEED` is deliberately enabled.

## Recovery

- A failed admission or transfer leaves no partial lifecycle records.
- Review `AuditLog` using the action prefixes `learners.*` and `staff.*`.
- Verify school context before correcting data.
- Never edit settled enrollment history to simulate a transfer.
