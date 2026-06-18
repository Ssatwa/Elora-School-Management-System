# Elora Platform Console Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated `/platform/` console where Elora superusers manage schools, users, memberships, and predefined roles without Django Admin.

**Architecture:** Add a focused `apps.platform_admin` Django app that reuses existing domain models and Elora UI tokens. Platform routes bypass tenant hostname scoping, use superuser-only access checks, and delegate all multi-record mutations to atomic service functions that write immutable audit events.

**Tech Stack:** Django 5.2, Django templates, pytest-django, HTMX-compatible server rendering, Alpine.js, existing Elora CSS components.

---

## File Structure

- `apps/platform_admin/apps.py`: Django app configuration.
- `apps/platform_admin/decorators.py`: superuser-only view access.
- `apps/platform_admin/forms.py`: school, user, password, and membership input validation.
- `apps/platform_admin/services.py`: atomic writes and audit events.
- `apps/platform_admin/views.py`: login, overview, list, create, and edit pages.
- `apps/platform_admin/urls.py`: `/platform/` route names.
- `apps/platform_admin/tests/`: access, service, form, view, and workflow tests.
- `templates/layouts/platform.html`: platform shell using existing Elora assets.
- `templates/platform/components/`: isolated sidebar and top bar.
- `templates/platform/`: login, overview, list, and form pages.
- `apps/tenancy/middleware.py`: skip tenant/RLS scoping for `/platform/`.
- `config/settings/base.py`, `config/urls.py`: register the app and routes.
- `docs/operations/platform-console.md`: operator workflow and safety notes.

### Task 1: Platform Routing, Tenant Bypass, and Access Control

**Files:**
- Create: `apps/platform_admin/__init__.py`
- Create: `apps/platform_admin/apps.py`
- Create: `apps/platform_admin/decorators.py`
- Create: `apps/platform_admin/forms.py`
- Create: `apps/platform_admin/urls.py`
- Create: `apps/platform_admin/views.py`
- Create: `apps/platform_admin/tests/__init__.py`
- Create: `apps/platform_admin/tests/test_access.py`
- Modify: `apps/tenancy/middleware.py`
- Modify: `config/settings/base.py`
- Modify: `config/urls.py`

- [ ] **Step 1: Write failing route and tenant-bypass tests**

```python
# apps/platform_admin/tests/test_access.py
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.tenancy.models import School, SchoolDomain

pytestmark = pytest.mark.django_db


def test_platform_login_is_available_on_school_hostname(client):
    school = School.objects.create(name="Green Hills", slug="green-hills")
    SchoolDomain.objects.create(
        school=school,
        hostname="green-hills.localhost",
        is_primary=True,
    )

    response = client.get(
        reverse("platform_admin:login"),
        HTTP_HOST="green-hills.localhost",
    )

    assert response.status_code == 200
    assert response.wsgi_request.school is None


def test_anonymous_platform_request_redirects_to_platform_login(client):
    response = client.get(reverse("platform_admin:overview"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("platform_admin:login"))


def test_school_admin_cannot_access_platform_console(client):
    user = get_user_model().objects.create_user("admin@example.test")
    client.force_login(user)

    response = client.get(reverse("platform_admin:overview"))

    assert response.status_code == 403


def test_superuser_can_access_platform_console(client):
    user = get_user_model().objects.create_superuser(
        "root@example.test",
        password="StrongPassword123!",
    )
    client.force_login(user)

    response = client.get(reverse("platform_admin:overview"))

    assert response.status_code == 200


def test_non_superuser_cannot_sign_in_to_platform_console(client):
    get_user_model().objects.create_user(
        "member@example.test",
        password="MemberPassword123!",
    )

    response = client.post(
        reverse("platform_admin:login"),
        {"username": "member@example.test", "password": "MemberPassword123!"},
    )

    assert response.status_code == 200
    assert "not authorized" in response.content.decode().lower()
    assert "_auth_user_id" not in client.session
```

- [ ] **Step 2: Run the tests and confirm missing routes fail**

Run: `pytest apps/platform_admin/tests/test_access.py -v`

Expected: collection/import failure because `apps.platform_admin` and its URL namespace do not exist.

- [ ] **Step 3: Add the app, route namespace, tenant bypass, and decorator**

```python
# apps/platform_admin/apps.py
from django.apps import AppConfig


class PlatformAdminConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.platform_admin"
```

```python
# apps/platform_admin/decorators.py
from functools import wraps

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse


def platform_superuser_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse("platform_admin:login")
            return redirect(f"{login_url}?next={request.get_full_path()}")
        if not request.user.is_superuser:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapped
```

```python
# apps/platform_admin/urls.py
from django.urls import path

from apps.platform_admin import views

app_name = "platform_admin"

urlpatterns = [
    path("", views.overview, name="overview"),
    path("login/", views.PlatformLoginView.as_view(), name="login"),
    path("logout/", views.PlatformLogoutView.as_view(), name="logout"),
]
```

```python
# apps/platform_admin/views.py
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render
from django.urls import reverse_lazy

from apps.platform_admin.decorators import platform_superuser_required
from apps.platform_admin.forms import PlatformAuthenticationForm


class PlatformLoginView(LoginView):
    template_name = "platform/login.html"
    authentication_form = PlatformAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy("platform_admin:overview")


class PlatformLogoutView(LogoutView):
    next_page = reverse_lazy("platform_admin:login")


@platform_superuser_required
def overview(request):
    return render(request, "platform/overview.html")
```

Modify `TenantMiddleware.__call__` before hostname resolution:

```python
request.school = None
token = current_school.set(None)
is_platform_path = request.path == "/platform" or request.path.startswith("/platform/")
try:
    if not is_platform_path and host not in self.platform_hosts:
        # retain the existing SchoolDomain lookup and RLS setup
```

Register `"apps.platform_admin"` in `INSTALLED_APPS` and add this before the Django Admin route:

```python
path("platform/", include("apps.platform_admin.urls")),
```

Create minimal `templates/platform/login.html` and `templates/platform/overview.html` so the route tests render.

```python
# apps/platform_admin/forms.py
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError


class PlatformAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_superuser:
            raise ValidationError(
                "This account is not authorized for the Elora platform console.",
                code="not_platform_superuser",
            )
```

- [ ] **Step 4: Run access tests**

Run: `pytest apps/platform_admin/tests/test_access.py apps/tenancy/tests/test_middleware.py -v`

Expected: all tests pass, including existing tenant resolution tests.

- [ ] **Step 5: Commit**

```bash
git add apps/platform_admin apps/tenancy/middleware.py config/settings/base.py config/urls.py templates/platform
git commit -m "feat: add protected platform console routes"
```

### Task 2: Atomic Platform Services and Audit Events

**Files:**
- Create: `apps/platform_admin/services.py`
- Create: `apps/platform_admin/tests/test_services.py`

- [ ] **Step 1: Write failing service tests**

```python
# apps/platform_admin/tests/test_services.py
import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import AuditLog, Membership, Role
from apps.platform_admin.services import (
    create_membership,
    create_platform_user,
    create_school,
    reset_user_password,
    update_platform_user,
)

pytestmark = pytest.mark.django_db


def make_actor():
    return get_user_model().objects.create_superuser("root@example.test")


def test_create_school_creates_primary_domain_and_audit_event():
    actor = make_actor()
    school = create_school(
        actor=actor,
        request_id="req-1",
        name="Sunrise Academy",
        slug="sunrise",
        hostname="sunrise.localhost",
        is_active=True,
    )

    assert school.domains.get(is_primary=True).hostname == "sunrise.localhost"
    event = AuditLog.objects.get(action="platform.school.created")
    assert event.actor == actor
    assert event.metadata == {"hostname": "sunrise.localhost", "is_active": True}


def test_create_platform_user_hashes_password_and_never_audits_it():
    actor = make_actor()
    user = create_platform_user(
        actor=actor,
        request_id="req-2",
        email="teacher@example.test",
        first_name="Terry",
        last_name="Teacher",
        password="TemporaryPass123!",
        is_active=True,
    )

    assert user.check_password("TemporaryPass123!")
    event = AuditLog.objects.get(action="platform.user.created")
    assert "password" not in str(event.metadata).lower()


def test_actor_cannot_deactivate_self():
    actor = make_actor()

    with pytest.raises(ValueError, match="own account"):
        update_platform_user(
            actor=actor,
            user=actor,
            request_id="req-3",
            email=actor.email,
            first_name="",
            last_name="",
            is_active=False,
        )


def test_create_membership_rejects_platform_roles():
    actor = make_actor()
    user = get_user_model().objects.create_user("teacher@example.test")
    school = create_school(
        actor=actor,
        request_id="req-4",
        name="Green Hills",
        slug="green-hills",
        hostname="green-hills.localhost",
        is_active=True,
    )
    role = Role.objects.create(
        code="super_admin",
        name="Super Admin",
        is_platform_role=True,
    )

    with pytest.raises(ValueError, match="school roles"):
        create_membership(
            actor=actor,
            request_id="req-5",
            user=user,
            school=school,
            roles=[role],
            is_active=True,
        )


def test_reset_password_records_no_secret():
    actor = make_actor()
    user = get_user_model().objects.create_user("member@example.test")

    reset_user_password(
        actor=actor,
        user=user,
        request_id="req-6",
        password="ReplacementPass123!",
    )

    assert user.check_password("ReplacementPass123!")
    assert "ReplacementPass123!" not in str(
        AuditLog.objects.get(action="platform.user.password_reset").metadata
    )
```

- [ ] **Step 2: Run the tests and verify service imports fail**

Run: `pytest apps/platform_admin/tests/test_services.py -v`

Expected: FAIL because `apps.platform_admin.services` does not exist.

- [ ] **Step 3: Implement transaction-backed services**

Implement these exact public signatures in `services.py`:

```python
from django.db import transaction

from apps.accounts.audit import record_audit_event
from apps.accounts.models import Membership
from apps.tenancy.models import School, SchoolDomain


@transaction.atomic
def create_school(*, actor, request_id, name, slug, hostname, is_active):
    school = School.objects.create(name=name, slug=slug, is_active=is_active)
    SchoolDomain.objects.create(
        school=school,
        hostname=hostname.lower(),
        is_primary=True,
    )
    record_audit_event(
        school=school,
        actor=actor,
        action="platform.school.created",
        target_type="School",
        target_id=school.pk,
        request_id=request_id,
        metadata={"hostname": hostname.lower(), "is_active": is_active},
    )
    return school


@transaction.atomic
def update_school(*, actor, school, request_id, name, slug, hostname, is_active):
    previous_active = school.is_active
    school.name = name
    school.slug = slug
    school.is_active = is_active
    school.save(update_fields=["name", "slug", "is_active", "updated_at"])
    domain, _ = SchoolDomain.objects.get_or_create(
        school=school,
        is_primary=True,
        defaults={"hostname": hostname.lower()},
    )
    domain.hostname = hostname.lower()
    domain.save(update_fields=["hostname", "updated_at"])
    record_audit_event(
        school=school,
        actor=actor,
        action="platform.school.updated",
        target_type="School",
        target_id=school.pk,
        request_id=request_id,
        metadata={
            "hostname": hostname.lower(),
            "active_from": previous_active,
            "active_to": is_active,
        },
    )
    return school
```

Also implement:

```python
create_platform_user(
    *, actor, request_id, email, first_name, last_name, password, is_active
)
update_platform_user(
    *, actor, user, request_id, email, first_name, last_name, is_active
)
reset_user_password(*, actor, user, request_id, password)
create_membership(*, actor, request_id, user, school, roles, is_active)
update_membership(
    *, actor, membership, request_id, user, school, roles, is_active
)
```

Use `User.objects.create_user`, `user.set_password`, `membership.roles.set(roles)`,
and `ValueError` for service invariants. Reject empty role collections for active
memberships and reject every role where `is_platform_role=True`. Audit metadata
contains IDs, role codes, and active transitions only.

- [ ] **Step 4: Run service and audit tests**

Run: `pytest apps/platform_admin/tests/test_services.py apps/accounts/tests/test_audit.py -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add apps/platform_admin/services.py apps/platform_admin/tests/test_services.py
git commit -m "feat: add audited platform management services"
```

### Task 3: Validated Platform Forms

**Files:**
- Modify: `apps/platform_admin/forms.py`
- Create: `apps/platform_admin/tests/test_forms.py`

- [ ] **Step 1: Write failing form tests**

```python
# apps/platform_admin/tests/test_forms.py
import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import Role
from apps.platform_admin.forms import (
    MembershipForm,
    PlatformUserCreateForm,
    SchoolForm,
)
from apps.tenancy.models import School, SchoolDomain

pytestmark = pytest.mark.django_db


def test_school_form_reports_duplicate_hostname():
    school = School.objects.create(name="Existing", slug="existing")
    SchoolDomain.objects.create(
        school=school,
        hostname="existing.localhost",
        is_primary=True,
    )
    form = SchoolForm(
        data={
            "name": "Other",
            "slug": "other",
            "hostname": "existing.localhost",
            "is_active": True,
        }
    )

    assert not form.is_valid()
    assert "hostname" in form.errors


def test_user_create_form_requires_matching_passwords():
    form = PlatformUserCreateForm(
        data={
            "email": "person@example.test",
            "first_name": "Pat",
            "last_name": "Person",
            "password1": "TemporaryPass123!",
            "password2": "DifferentPass123!",
            "is_active": True,
        }
    )

    assert not form.is_valid()
    assert "password2" in form.errors


def test_membership_form_excludes_platform_roles():
    Role.objects.create(code="super_admin", name="Super Admin", is_platform_role=True)
    Role.objects.create(code="teacher", name="Teacher", is_platform_role=False)

    form = MembershipForm()

    assert list(form.fields["roles"].queryset.values_list("code", flat=True)) == [
        "teacher"
    ]
```

- [ ] **Step 2: Run tests and verify the forms are missing**

Run: `pytest apps/platform_admin/tests/test_forms.py -v`

Expected: FAIL because the management form classes do not exist.

- [ ] **Step 3: Implement forms**

Create:

```python
class SchoolForm(forms.Form):
    name = forms.CharField(max_length=200)
    slug = forms.SlugField(max_length=80)
    hostname = forms.CharField(max_length=253)
    is_active = forms.BooleanField(required=False, initial=True)


class PlatformUserCreateForm(forms.Form):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    is_active = forms.BooleanField(required=False, initial=True)


class PlatformUserUpdateForm(forms.Form):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    is_active = forms.BooleanField(required=False)


class PasswordResetForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)


class MembershipForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.order_by("email"))
    school = forms.ModelChoiceField(queryset=School.objects.order_by("name"))
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.filter(is_platform_role=False).order_by("name"),
        widget=forms.CheckboxSelectMultiple,
    )
    is_active = forms.BooleanField(required=False, initial=True)
```

Normalize hostnames and emails to lowercase. Add instance-aware uniqueness checks
for school slug, hostname, user email, and `(user, school)` membership. Validate
matching passwords and call `validate_password(password1)`. Require roles when
`is_active` is true.

- [ ] **Step 4: Run form tests**

Run: `pytest apps/platform_admin/tests/test_forms.py -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add apps/platform_admin/forms.py apps/platform_admin/tests/test_forms.py
git commit -m "feat: validate platform administration forms"
```

### Task 4: Platform Shell, Login, and Overview

**Files:**
- Create: `templates/layouts/platform.html`
- Create: `templates/platform/components/sidebar.html`
- Create: `templates/platform/components/topbar.html`
- Modify: `templates/platform/login.html`
- Modify: `templates/platform/overview.html`
- Modify: `apps/platform_admin/views.py`
- Create: `apps/platform_admin/tests/test_overview.py`

- [ ] **Step 1: Write failing shell and metric tests**

```python
# apps/platform_admin/tests/test_overview.py
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import Membership
from tests.factories import MembershipFactory, SchoolFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_overview_shows_platform_metrics_and_isolated_navigation(client):
    root = get_user_model().objects.create_superuser("root@example.test")
    active_school = SchoolFactory()
    SchoolFactory(is_active=False)
    UserFactory(is_active=True)
    UserFactory(is_active=False)
    MembershipFactory(school=active_school, role_code="teacher")
    client.force_login(root)

    response = client.get(reverse("platform_admin:overview"))
    content = response.content.decode()

    assert response.status_code == 200
    assert "Elora Platform" in content
    assert "Total schools" in content
    assert "Total users" in content
    assert "Total memberships" in content
    assert 'href="/platform/schools/"' in content
    assert 'href="/platform/users/"' in content
    assert 'href="/platform/memberships/"' in content
    assert 'href="/learners/"' not in content
    assert 'href="/staff/"' not in content
```

- [ ] **Step 2: Run the overview test and confirm missing metrics fail**

Run: `pytest apps/platform_admin/tests/test_overview.py -v`

Expected: FAIL because the minimal overview has no metrics or platform shell.

- [ ] **Step 3: Build the isolated shell and overview query**

Use the existing theme bootstrap, `eloraShell` Alpine state, skip link, messages,
and CSS/JS assets in `templates/layouts/platform.html`. Include only platform
components.

The sidebar links to:

```django
{% url "platform_admin:overview" %}
{% url "platform_admin:schools" %}
{% url "platform_admin:users" %}
{% url "platform_admin:memberships" %}
{% url "platform_admin:roles" %}
```

The top bar text is `Elora Platform`, its subtitle is `Platform workspace`, and
its sign-out form posts to `platform_admin:logout`.

Update `overview`:

```python
@platform_superuser_required
def overview(request):
    context = {
        "total_schools": School.objects.count(),
        "active_schools": School.objects.filter(is_active=True).count(),
        "total_users": User.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "total_memberships": Membership.objects.count(),
        "recent_events": AuditLog.objects.filter(
            action__startswith="platform."
        ).select_related("actor", "school")[:8],
    }
    return render(request, "platform/overview.html", context)
```

Render five existing `components/metric_card.html` components and three quick
action links.

- [ ] **Step 4: Run overview and UI shell tests**

Run: `pytest apps/platform_admin/tests/test_overview.py apps/core/tests/test_ui_shell.py -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add templates/layouts/platform.html templates/platform apps/platform_admin/views.py apps/platform_admin/tests/test_overview.py
git commit -m "feat: build Elora platform overview shell"
```

### Task 5: School and User Management Pages

**Files:**
- Modify: `apps/platform_admin/urls.py`
- Modify: `apps/platform_admin/views.py`
- Create: `apps/platform_admin/tests/test_school_views.py`
- Create: `apps/platform_admin/tests/test_user_views.py`
- Create: `templates/platform/schools/list.html`
- Create: `templates/platform/schools/form.html`
- Create: `templates/platform/users/list.html`
- Create: `templates/platform/users/form.html`
- Create: `templates/platform/users/password.html`

- [ ] **Step 1: Write failing school and user workflow tests**

```python
def test_superuser_creates_school(client, superuser):
    client.force_login(superuser)
    response = client.post(
        reverse("platform_admin:school-create"),
        {
            "name": "Lakeview Academy",
            "slug": "lakeview",
            "hostname": "lakeview.localhost",
            "is_active": "on",
        },
    )
    assert response.status_code == 302
    assert SchoolDomain.objects.get(hostname="lakeview.localhost").is_primary


def test_superuser_creates_user_with_hashed_temporary_password(client, superuser):
    client.force_login(superuser)
    response = client.post(
        reverse("platform_admin:user-create"),
        {
            "email": "teacher@lakeview.test",
            "first_name": "Terry",
            "last_name": "Teacher",
            "password1": "TemporaryPass123!",
            "password2": "TemporaryPass123!",
            "is_active": "on",
        },
    )
    user = get_user_model().objects.get(email="teacher@lakeview.test")
    assert response.status_code == 302
    assert user.check_password("TemporaryPass123!")


def test_superuser_cannot_deactivate_self_through_form(client, superuser):
    client.force_login(superuser)
    response = client.post(
        reverse("platform_admin:user-edit", args=[superuser.pk]),
        {
            "email": superuser.email,
            "first_name": "",
            "last_name": "",
        },
    )
    assert response.status_code == 400
    assert "own account" in response.content.decode()
```

Place the first test in `test_school_views.py` and the other two in
`test_user_views.py`. Include this fixture in each file that uses it:

```python
@pytest.fixture
def superuser():
    return get_user_model().objects.create_superuser("root@example.test")
```

- [ ] **Step 2: Run the view tests and verify routes fail**

Run: `pytest apps/platform_admin/tests/test_school_views.py apps/platform_admin/tests/test_user_views.py -v`

Expected: FAIL because the list/create/edit/password routes do not exist.

- [ ] **Step 3: Implement routes and views**

Add:

```python
path("schools/", views.school_list, name="schools"),
path("schools/new/", views.school_create, name="school-create"),
path("schools/<uuid:school_id>/edit/", views.school_edit, name="school-edit"),
path("users/", views.user_list, name="users"),
path("users/new/", views.user_create, name="user-create"),
path("users/<uuid:user_id>/edit/", views.user_edit, name="user-edit"),
path(
    "users/<uuid:user_id>/password/",
    views.user_password_reset,
    name="user-password-reset",
),
```

Every view uses `@platform_superuser_required`. List views use `Q` search and
`Count` annotations. POST views bind the forms, call the Task 2 services with
`request.request_id`, show `messages.success`, and redirect to the list.
Invalid POSTs render status 400. Edit views use `get_object_or_404`.

- [ ] **Step 4: Build responsive tables and shared form pages**

Use `components/page_header.html`, `elora-panel`, `elora-table`,
`elora-button-primary`, status badges, labeled inputs, field errors, and explicit
cancel links. School rows display name, slug, primary hostname, active state,
membership count, and Edit. User rows display name, email, active state,
superuser badge, membership count, Edit, and Reset password.

- [ ] **Step 5: Run school and user tests**

Run: `pytest apps/platform_admin/tests/test_school_views.py apps/platform_admin/tests/test_user_views.py -v`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add apps/platform_admin/urls.py apps/platform_admin/views.py apps/platform_admin/tests templates/platform/schools templates/platform/users
git commit -m "feat: manage schools and users in platform console"
```

### Task 6: Membership Management and Role Catalogue

**Files:**
- Modify: `apps/platform_admin/urls.py`
- Modify: `apps/platform_admin/views.py`
- Create: `apps/platform_admin/tests/test_membership_views.py`
- Create: `apps/platform_admin/tests/test_role_views.py`
- Create: `templates/platform/memberships/list.html`
- Create: `templates/platform/memberships/form.html`
- Create: `templates/platform/roles/list.html`

- [ ] **Step 1: Write failing membership-to-teacher workflow test**

```python
# apps/platform_admin/tests/test_membership_views.py
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import Membership, Role
from apps.staff.forms import TeacherProfileForm
from tests.factories import SchoolFactory

pytestmark = pytest.mark.django_db


def test_created_teacher_membership_appears_in_teacher_profile_form(client):
    root = get_user_model().objects.create_superuser("root@example.test")
    user = get_user_model().objects.create_user("teacher@example.test")
    school = SchoolFactory()
    teacher = Role.objects.create(
        code="teacher",
        name="Teacher",
        is_platform_role=False,
    )
    client.force_login(root)

    response = client.post(
        reverse("platform_admin:membership-create"),
        {
            "user": user.pk,
            "school": school.pk,
            "roles": [teacher.pk],
            "is_active": "on",
        },
    )

    membership = Membership.objects.get(user=user, school=school)
    form = TeacherProfileForm(school=school)
    assert response.status_code == 302
    assert membership in form.fields["membership"].queryset

```

```python
# apps/platform_admin/tests/test_role_views.py
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import Role

pytestmark = pytest.mark.django_db


def test_role_catalogue_is_read_only(client):
    root = get_user_model().objects.create_superuser("root@example.test")
    Role.objects.create(code="teacher", name="Teacher", is_platform_role=False)
    client.force_login(root)

    response = client.get(reverse("platform_admin:roles"))

    assert response.status_code == 200
    assert "Teacher" in response.content.decode()
    assert "Add role" not in response.content.decode()
```

- [ ] **Step 2: Run tests and verify missing routes fail**

Run: `pytest apps/platform_admin/tests/test_membership_views.py apps/platform_admin/tests/test_role_views.py -v`

Expected: FAIL because membership and role routes do not exist.

- [ ] **Step 3: Add routes and views**

```python
path("memberships/", views.membership_list, name="memberships"),
path("memberships/new/", views.membership_create, name="membership-create"),
path(
    "memberships/<uuid:membership_id>/edit/",
    views.membership_edit,
    name="membership-edit",
),
path("roles/", views.role_list, name="roles"),
```

`membership_list` accepts `q`, `school`, `role`, and `status`, applies them with
`Q` objects, and prefetches roles. Create/edit views use `MembershipForm` and
the services. `role_list` annotates membership counts and performs no writes.

- [ ] **Step 4: Build membership and role templates**

The membership table displays user, school, comma-separated roles, active state,
and Edit. The form renders user and school selects, role checkboxes, active
status, errors, Save, and Cancel. The role catalogue displays name, code,
`Platform`/`School` scope, and membership count without create/edit controls.

- [ ] **Step 5: Run membership, role, and staff form tests**

Run: `pytest apps/platform_admin/tests/test_membership_views.py apps/platform_admin/tests/test_role_views.py apps/staff/tests -v`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add apps/platform_admin/urls.py apps/platform_admin/views.py apps/platform_admin/tests templates/platform/memberships templates/platform/roles
git commit -m "feat: manage memberships and inspect roles"
```

### Task 7: End-to-End Security, Documentation, and Verification

**Files:**
- Create: `apps/platform_admin/tests/test_workflow.py`
- Create: `docs/operations/platform-console.md`

- [ ] **Step 1: Write the complete exit-workflow test**

```python
# apps/platform_admin/tests/test_workflow.py
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.accounts.models import AuditLog, Membership, Role
from apps.staff.forms import TeacherProfileForm
from tests.factories import SchoolFactory

pytestmark = pytest.mark.django_db


def test_platform_operator_creates_login_and_teacher_membership(client):
    root = get_user_model().objects.create_superuser(
        "root@example.test",
        password="RootPassword123!",
    )
    school = SchoolFactory(name="Green Hills Academy", slug="green-hills")
    role = Role.objects.create(code="teacher", name="Teacher")
    client.force_login(root)

    user_response = client.post(
        reverse("platform_admin:user-create"),
        {
            "email": "new.teacher@example.test",
            "first_name": "New",
            "last_name": "Teacher",
            "password1": "TemporaryPass123!",
            "password2": "TemporaryPass123!",
            "is_active": "on",
        },
    )
    user = get_user_model().objects.get(email="new.teacher@example.test")
    membership_response = client.post(
        reverse("platform_admin:membership-create"),
        {
            "user": user.pk,
            "school": school.pk,
            "roles": [role.pk],
            "is_active": "on",
        },
    )

    assert user_response.status_code == 302
    assert membership_response.status_code == 302
    assert user.check_password("TemporaryPass123!")
    membership = Membership.objects.get(user=user, school=school)
    assert membership in TeacherProfileForm(
        school=school
    ).fields["membership"].queryset
    metadata = " ".join(
        str(value)
        for value in AuditLog.objects.filter(action__startswith="platform.").values_list(
            "metadata", flat=True
        )
    )
    assert "TemporaryPass123!" not in metadata
```

- [ ] **Step 2: Run the workflow test**

Run: `pytest apps/platform_admin/tests/test_workflow.py -v`

Expected: PASS after Tasks 1–6; if it fails, fix the underlying service or view,
not the test.

- [ ] **Step 3: Write operator documentation**

Document:

- `/platform/login/` and `/platform/`
- superuser-only access
- create User, then Membership, then Teacher Profile
- temporary-password handling
- deactivation instead of deletion
- role catalogue is read-only
- audit action names
- Django Admin is reserved for emergency engineering recovery

- [ ] **Step 4: Run static checks and the complete test suite**

Run:

```bash
ruff check .
mypy apps
pytest -q
```

Expected: all commands exit 0 with no lint errors, type errors, or test failures.

- [ ] **Step 5: Run browser verification**

Start or reuse the local server, then verify:

1. `/platform/login/` uses Elora branding.
2. A school admin receives 403 at `/platform/`.
3. A superuser sees only Overview, Schools, Users, Memberships, and Roles.
4. Create a user with a temporary password.
5. Assign the user the Teacher role at Green Hills Academy.
6. Open `/staff/` as an authorized school administrator and confirm the new
   account appears in the Teacher profile membership selector.
7. Confirm responsive navigation and forms at desktop and mobile widths.

- [ ] **Step 6: Commit**

```bash
git add apps/platform_admin/tests/test_workflow.py docs/operations/platform-console.md
git commit -m "test: verify platform administration workflow"
```

- [ ] **Step 7: Review the final diff**

Run:

```bash
git status --short
git diff --check
git log --oneline -8
```

Expected: only intentionally untracked local server artifacts remain; no
whitespace errors; the platform-console commits appear in order.
