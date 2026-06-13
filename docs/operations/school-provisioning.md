# School Provisioning

1. Create the `School` record with a unique slug and confirmed timezone.
2. Create a primary `SchoolDomain` such as `schoolname.elora.co.ke`.
3. Confirm wildcard DNS and TLS cover the hostname.
4. Create the School Admin user and one active membership.
5. Attach the `school_admin` role to the membership.
6. Verify login, dashboard access, and cross-school denial tests.
7. Record the provisioning action in `AuditLog`.

Suspending a school sets `School.is_active` to false. Tenant middleware then
returns a neutral not-found response and background tasks reject the school.
