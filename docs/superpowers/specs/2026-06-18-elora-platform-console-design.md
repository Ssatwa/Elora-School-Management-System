# Elora Platform Console Design

## Goal

Build a dedicated Elora super-admin console at `/platform/` so platform operators
can manage schools, users, memberships, and predefined roles without using
Django Admin.

The console will reuse Elora's existing application shell, visual language, and
responsive behavior while remaining clearly separated from every school
workspace.

## Scope

The first release provides:

- A platform overview showing school, user, membership, and active-account
  totals.
- School creation and editing, including primary domains and active status.
- User creation and editing, including names, email, temporary password, and
  active status.
- Membership creation and editing to connect one user to one school and assign
  one or more predefined school roles.
- A read-only role catalogue showing the seeded Elora roles.
- Audit events for platform changes.

The first release does not provide custom roles, individual permission editing,
email invitations, password-expiry enforcement, school impersonation, bulk
imports, hard deletion, or access to Django Admin from the platform console.

## Access and Routing

The console lives under `/platform/` and has a dedicated login at
`/platform/login/`.

Only authenticated users with Django's `is_superuser=True` flag may access
platform pages. School roles, including `school_admin`, never grant platform
access. An authenticated non-superuser receives HTTP 403 rather than being
silently redirected into the console.

The platform console does not require a school hostname or active school
membership. It may be reached through any configured local hostname, but all
platform links remain under `/platform/`.

Successful platform login redirects to `/platform/`. Logging out returns the
operator to `/platform/login/`.

## Information Architecture

The platform navigation contains:

- Overview
- Schools
- Users
- Memberships
- Roles

The top bar identifies the workspace as `Elora Platform` and shows the signed-in
operator. School-specific modules such as learners, attendance, finance, and
staff are not shown.

## Overview

The overview displays:

- Total schools
- Active schools
- Total users
- Active users
- Total memberships

It also shows recent platform audit events and quick actions for creating a
school, user, or membership.

## School Management

The school list supports search by name, slug, and hostname. Each row shows the
school name, slug, primary domain, active status, membership count, and an edit
action.

Creating a school requires:

- Name
- Unique slug
- Unique primary hostname
- Active status

Editing permits changes to the name, slug, primary hostname, and active status.
The operation updates the school and primary domain atomically. Validation
errors leave both records unchanged.

Schools are deactivated rather than deleted. Deactivation does not remove users,
memberships, or school records.

## User Management

The user list supports search by email, first name, and last name. Each row shows
the user's display name, email, active status, superuser status, membership
count, and edit action.

Creating a user requires:

- Unique email
- First name
- Last name
- Temporary password
- Temporary password confirmation
- Active status

The password is stored only through Django's password hashing API and is never
written to an audit event. The operator communicates the temporary password
outside Elora. Forced password change is deferred until a later release.

Editing permits changes to names, email, and active status. Password reset is a
separate explicit action requiring a new password and confirmation.

The currently signed-in operator cannot deactivate their own account or remove
their own superuser access through this console. The first release does not
provide controls for granting or revoking superuser status.

Users are deactivated rather than deleted.

## Membership Management

A membership connects one global user to one school. The existing uniqueness
rule of one membership per user and school remains authoritative.

The membership list supports filtering by school, role, and active status, plus
search by user email or name. Each row shows the user, school, assigned roles,
active status, and edit action.

Creating or editing a membership requires:

- User
- School
- One or more predefined non-platform roles
- Active status

The `super_admin` platform role is excluded because platform access is governed
by `User.is_superuser`, not school membership. Assigning teaching roles makes
the membership available to the existing teacher-profile workflow, but does not
automatically create a teacher profile.

Memberships are deactivated rather than deleted. Removing all roles is invalid;
an active membership must have at least one school role.

## Role Catalogue

The roles page is read-only. It displays each seeded role's name, code, scope,
and membership count.

Platform roles and school roles are visually distinguished. Custom role
creation, role renaming, and permission editing are outside this release.

## Architecture

A new `apps.platform_admin` Django app owns the console's URLs, access
decorators, forms, services, views, and tests. It operates on the existing
`School`, `SchoolDomain`, `User`, `Membership`, `Role`, and `AuditLog` models
rather than introducing duplicate platform models.

Mutating workflows live in transaction-backed services:

- `create_school` and `update_school`
- `create_platform_user`, `update_platform_user`, and `reset_user_password`
- `create_membership` and `update_membership`

Forms handle input normalization and user-facing validation. Services enforce
cross-record invariants, perform atomic writes, and record audit events.

Platform templates use a dedicated platform layout composed from the same
Elora CSS tokens and interaction patterns as the school dashboard. The platform
sidebar is separate from the school sidebar to prevent navigation leakage
between contexts.

## Audit Trail

Successful mutations create immutable `AuditLog` entries with these action
names:

- `platform.school.created`
- `platform.school.updated`
- `platform.user.created`
- `platform.user.updated`
- `platform.user.password_reset`
- `platform.membership.created`
- `platform.membership.updated`

Metadata may include changed non-sensitive fields, school identifiers, role
codes, and active-state transitions. It must never include passwords or password
hashes.

## Error Handling

- Duplicate emails, slugs, hostnames, and memberships produce field-level form
  errors.
- Password mismatch and password-validator failures produce field-level errors.
- Cross-record writes are atomic and roll back completely on failure.
- Missing records return HTTP 404.
- Unauthorized platform access returns HTTP 403.
- Successful mutations redirect to the relevant list or detail page and display
  an Elora success message.

## Testing

Automated tests cover:

- Dedicated platform login and logout behavior.
- Superuser access to every platform page.
- Anonymous redirects to platform login.
- School admins and other non-superusers receiving HTTP 403.
- Overview metrics.
- School creation, editing, uniqueness validation, and atomic domain updates.
- User creation with a hashed password, editing, password reset, and
  self-deactivation prevention.
- Membership creation and editing, tenant uniqueness, role filtering, and
  active-membership role requirements.
- Read-only role catalogue behavior.
- Audit event creation and password exclusion.
- Platform navigation isolation from school modules.

Browser verification covers the desktop and mobile layouts, form errors,
successful workflows, and the existing teacher-profile dropdown receiving a
newly created teaching membership.

## Success Criteria

The feature is complete when a superuser can sign in at `/platform/login/`,
create a school user with a temporary password, assign that user a teacher role
at Green Hills Academy, and then see that membership as a selectable teacher
account in the existing school staff workflow—without visiting Django Admin.
