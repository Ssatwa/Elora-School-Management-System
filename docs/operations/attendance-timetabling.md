# Attendance And Timetabling Operations

Milestone 3 provides learner and staff attendance cycles, audited corrections,
absence follow-up, CSV reporting, conflict-aware timetable planning, and
published class and teacher schedules.

## Access

- School Admin, Principal, Deputy Principal, teachers, Class Teachers,
  Department Heads, and Guidance & Counselling can view attendance.
- School Admin, Principal, Deputy Principal, and Class Teachers complete
  learner registers.
- School Admin, Principal, and Deputy Principal complete staff registers and
  correct settled entries.
- Teaching and leadership roles can view published timetables.
- School Admin, Principal, and Deputy Principal create and publish timetable
  versions.

All forms, object lookups, reports, exports, and schedule queries use the school
resolved from the request hostname.

## Daily Attendance

A register is unique by school, date, session, target type, and learner stream.
Bulk submission is atomic: one invalid or cross-school row rolls back the
register and every entry. A completed register stores its marking actor and
completion timestamp.

Absent entries create one pending `AbsenceAlert`. Learner alerts use the
primary communication guardian where available; staff alerts use the teacher
contact summary. Message delivery is intentionally represented as persistent
queue state so later communication workers can send through email, SMS, or
other configured channels without changing attendance history.

## Corrections

Never edit attendance history directly. The correction service:

1. Locks the current entry.
2. Records immutable before and after status, arrival time, note, reason, and
   correcting actor.
3. Updates the operational entry.
4. Creates or removes its absence alert as appropriate.
5. Records an `attendance.entry.corrected` audit event.

## Reports And Exports

Attendance summaries count present, absent, late, and excused entries for a
selected date range and target type. CSV exports include learner and staff
rows for the active school only. Treat exported files as personal data and
store or share them according to school policy.

## Timetable Publication

Rooms, periods, and timetable versions are school-owned. Only draft versions
can be edited. Entry creation checks the selected period for:

- Teacher conflicts
- Room conflicts
- Stream conflicts
- Duplicate learning-area allocation for the same stream

Publication requires at least one lesson and reruns the complete conflict
engine. A successful publication stores actor and timestamp and records a
`timetabling.timetable.published` audit event. Published versions are
read-only; create a new draft to revise a schedule.

## Demo Review

`manage.py seed_demo` creates two attendance registers, an absence alert, two
rooms, three Monday periods, and a published two-lesson timetable for both
Green Hills Academy and Sunrise Academy.

Review Green Hills at:

- `/attendance/`
- `/attendance/register/learners/`
- `/attendance/register/staff/`
- `/timetables/`
- `/timetables/mine/`

## Recovery

- Duplicate registers are rejected rather than merged.
- Failed bulk marking leaves no partial register.
- Failed timetable publication leaves the draft unchanged.
- Review `AuditLog` using the `attendance.*` and `timetabling.*` prefixes.
- PostgreSQL row-level security protects all Milestone 3 tenant tables in
  addition to application-level school scoping.
