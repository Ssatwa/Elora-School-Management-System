# Elora Platform Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the runnable, tenant-safe Elora foundation with authentication, school memberships, RBAC, role dashboards, UI shell, Docker services, seed data, and CI.

**Architecture:** A custom global user authenticates once, while school memberships carry tenant-specific roles. Subdomain middleware resolves the active school, tenant-aware query APIs require explicit school context, and PostgreSQL row-level security is introduced after the application-level isolation tests pass. Django templates provide the primary interface, with HTMX partials and Alpine.js used as progressive enhancement.

**Tech Stack:** Python 3.13, Django 5.2, PostgreSQL 17, Redis 7, Celery 5.6, Tailwind CSS 4, HTMX 2, Alpine.js 3, pytest, Ruff, mypy, Docker Compose

---

## File Responsibilities

- `config/settings/*`: environment-specific settings with secure production defaults.
- `apps/core`: UUID/timestamp bases, request identifiers, health checks, and shared template context.
- `apps/tenancy`: schools, domains, tenant context, middleware, managers, and RLS helpers.
- `apps/accounts`: global users, school memberships, roles, authentication, authorization, and audits.
- `apps/analytics`: dashboard registry and initial role-specific dashboard queries.
- `templates/layouts`: public and authenticated application shells.
- `templates/components`: reusable cards, tables, navigation, messages, and form fragments.
- `tests`: project-wide security and smoke tests that span applications.

### Task 0: Verify Workstation Prerequisites

**Files:** None

- [ ] **Step 1: Verify required tools**

Run:

```powershell
git --version
py -3.13 --version
docker --version
node --version
npm --version
```

Expected: every command prints a version and exits 0.

- [ ] **Step 2: Install `uv`**

Run:

```powershell
py -3.13 -m pip install --user uv
uv --version
```

Expected: `uv` prints its installed version.

- [ ] **Step 3: Initialize the repository if needed**

Run:

```powershell
git init
git branch -M main
git config user.name
git config user.email
```

Expected: the repository uses `main`, and the final two commands print the configured commit identity.

### Task 1: Bootstrap Tooling And Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `manage.py`
- Create: `config/__init__.py`
- Create: `config/asgi.py`
- Create: `config/wsgi.py`
- Create: `config/urls.py`
- Create: `config/settings/__init__.py`
- Create: `config/settings/base.py`
- Create: `config/settings/local.py`
- Create: `config/settings/test.py`
- Create: `config/settings/production.py`
- Test: `tests/test_project_bootstrap.py`

- [ ] **Step 1: Write the failing project bootstrap test**

```python
from django.conf import settings
from django.urls import reverse


def test_project_uses_nairobi_timezone():
    assert settings.TIME_ZONE == "Africa/Nairobi"


def test_health_url_is_registered(client):
    response = client.get(reverse("health"))
    assert response.status_code == 200
```

- [ ] **Step 2: Run the bootstrap test and verify it fails**

Run: `pytest tests/test_project_bootstrap.py -q`

Expected: FAIL because Django, settings, and the `health` route do not exist.

- [ ] **Step 3: Create the dependency and tool configuration**

```toml
[project]
name = "elora"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
  "Django>=5.2,<5.3",
  "celery>=5.6,<5.7",
  "django-environ>=0.12,<0.13",
  "django-htmx>=1.23,<2",
  "django-redis>=6,<7",
  "psycopg[binary]>=3.2,<4",
  "uvicorn[standard]>=0.34,<1",
  "whitenoise>=6.9,<7",
]

[dependency-groups]
dev = [
  "coverage[toml]>=7.8,<8",
  "django-stubs>=5.2,<6",
  "factory-boy>=3.3,<4",
  "mypy>=1.16,<2",
  "pytest>=8.4,<9",
  "pytest-django>=4.11,<5",
  "ruff>=0.12,<1",
]

[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
python_files = ["test_*.py"]
addopts = "--strict-markers --reuse-db"

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "DJ"]

[tool.mypy]
plugins = ["mypy_django_plugin.main"]
strict = true

[tool.django-stubs]
django_settings_module = "config.settings.test"
```

- [ ] **Step 4: Create split Django settings**

```python
# config/settings/base.py
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parents[2]
env = environ.Env(DEBUG=(bool, False))

SECRET_KEY = env("SECRET_KEY", default="unsafe-local-only")
DEBUG = env.bool("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", ".localhost"])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "analytics:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ],
    },
}]

DATABASES = {"default": env.db(default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")}
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "Africa/Nairobi"
LANGUAGE_CODE = "en"
```

- [ ] **Step 5: Create the project entry points and temporary health route**

```python
# config/urls.py
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def health(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
]
```

- [ ] **Step 6: Install dependencies, migrate, and run the test**

Run:

```powershell
uv sync
uv run python manage.py migrate
uv run pytest tests/test_project_bootstrap.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit the project skeleton**

```powershell
git add pyproject.toml .python-version .gitignore .env.example manage.py config tests
git commit -m "build: bootstrap Django project"
```

### Task 2: Add Core Primitives And Health Checks

**Files:**
- Create: `apps/__init__.py`
- Create: `apps/core/__init__.py`
- Create: `apps/core/apps.py`
- Create: `apps/core/models.py`
- Create: `apps/core/middleware.py`
- Create: `apps/core/views.py`
- Create: `apps/core/urls.py`
- Modify: `config/settings/base.py`
- Modify: `config/urls.py`
- Test: `apps/core/tests/test_health.py`

- [ ] **Step 1: Write failing health and request-ID tests**

```python
def test_health_response_has_request_id(client):
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.headers["X-Request-ID"]


def test_readiness_reports_database(client):
    response = client.get("/ready/")
    assert response.json() == {"status": "ready", "database": "ok"}
```

- [ ] **Step 2: Run the tests and verify failure**

Run: `uv run pytest apps/core/tests/test_health.py -q`

Expected: FAIL because request middleware and readiness do not exist.

- [ ] **Step 3: Implement shared model bases**

```python
# apps/core/models.py
import uuid

from django.db import models


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
```

- [ ] **Step 4: Implement request IDs and health endpoints**

```python
# apps/core/middleware.py
import uuid


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = self.get_response(request)
        response.headers["X-Request-ID"] = request.request_id
        return response
```

```python
# apps/core/views.py
from django.db import connection
from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "ok"})


def readiness(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()
    return JsonResponse({"status": "ready", "database": "ok"})
```

- [ ] **Step 5: Wire middleware and URLs**

Add `"apps.core"` and `"django_htmx"` to `INSTALLED_APPS`; add
`"apps.core.middleware.RequestIDMiddleware"` after `SecurityMiddleware` and
`"django_htmx.middleware.HtmxMiddleware"` at the end of `MIDDLEWARE`; include
`apps.core.urls` at the root.

- [ ] **Step 6: Run core tests**

Run: `uv run pytest apps/core/tests/test_health.py -q`

Expected: PASS.

- [ ] **Step 7: Commit core primitives**

```powershell
git add apps/core config
git commit -m "feat: add core primitives and health checks"
```

### Task 3: Implement Schools, Users, Memberships, And Roles

**Files:**
- Create: `apps/tenancy/apps.py`
- Create: `apps/tenancy/models.py`
- Create: `apps/accounts/apps.py`
- Create: `apps/accounts/managers.py`
- Create: `apps/accounts/models.py`
- Create: `apps/accounts/roles.py`
- Modify: `config/settings/base.py`
- Create: `apps/tenancy/migrations/0001_initial.py`
- Create: `apps/accounts/migrations/0001_initial.py`
- Test: `apps/accounts/tests/test_models.py`

- [ ] **Step 1: Write failing identity model tests**

```python
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from apps.accounts.models import Membership, Role
from apps.tenancy.models import School


@pytest.mark.django_db
def test_email_is_the_user_identifier():
    user = get_user_model().objects.create_user("admin@elora.test", password="secret-pass")
    assert user.email == "admin@elora.test"
    assert user.username is None


@pytest.mark.django_db
def test_membership_role_is_unique_per_school():
    school = School.objects.create(name="Elora Academy", slug="elora-academy")
    user = get_user_model().objects.create_user("admin@elora.test")
    role = Role.objects.create(code="school_admin", name="School Admin")
    membership = Membership.objects.create(school=school, user=user)
    membership.roles.add(role)
    with pytest.raises(IntegrityError):
        Membership.objects.create(school=school, user=user)
```

- [ ] **Step 2: Run model tests and verify failure**

Run: `uv run pytest apps/accounts/tests/test_models.py -q`

Expected: FAIL because the identity models do not exist.

- [ ] **Step 3: Implement school and domain models**

```python
# apps/tenancy/models.py
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel


class School(UUIDModel, TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)
    primary_color = models.CharField(max_length=7, default="#1D4ED8")
    secondary_color = models.CharField(max_length=7, default="#0F766E")
    timezone = models.CharField(max_length=64, default="Africa/Nairobi")

    def __str__(self):
        return self.name


class SchoolDomain(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="domains")
    hostname = models.CharField(max_length=253, unique=True)
    is_primary = models.BooleanField(default=False)
```

- [ ] **Step 4: Implement global users and school memberships**

```python
# apps/accounts/models.py
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.managers import UserManager
from apps.core.models import TimeStampedModel, UUIDModel


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()


class Role(UUIDModel):
    code = models.SlugField(max_length=64, unique=True)
    name = models.CharField(max_length=100)
    is_platform_role = models.BooleanField(default=False)


class Membership(UUIDModel, TimeStampedModel):
    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    roles = models.ManyToManyField(Role, related_name="memberships")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "user"],
                name="unique_school_user_membership",
            )
        ]
```

- [ ] **Step 5: Add the email user manager**

```python
# apps/accounts/managers.py
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)
```

- [ ] **Step 6: Create and run migrations**

Add `"apps.tenancy"` and `"apps.accounts"` to `INSTALLED_APPS`, then set:

```python
AUTH_USER_MODEL = "accounts.User"
```

Run:

```powershell
uv run python manage.py makemigrations tenancy accounts
uv run python manage.py migrate
uv run pytest apps/accounts/tests/test_models.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit identity models**

```powershell
git add apps/tenancy apps/accounts
git commit -m "feat: add schools users memberships and roles"
```

### Task 4: Enforce Tenant Resolution And Query Scoping

**Files:**
- Create: `apps/tenancy/context.py`
- Create: `apps/tenancy/managers.py`
- Create: `apps/tenancy/middleware.py`
- Create: `apps/tenancy/exceptions.py`
- Modify: `config/settings/base.py`
- Test: `apps/tenancy/tests/test_middleware.py`
- Test: `apps/tenancy/tests/test_managers.py`

- [ ] **Step 1: Write failing tenant middleware tests**

```python
import pytest

from apps.tenancy.models import School, SchoolDomain


@pytest.mark.django_db
def test_known_subdomain_sets_request_school(client):
    school = School.objects.create(name="Green Hills", slug="green-hills")
    SchoolDomain.objects.create(
        school=school,
        hostname="green-hills.localhost",
        is_primary=True,
    )
    response = client.get("/health/", HTTP_HOST="green-hills.localhost")
    assert response.headers["X-Elora-School"] == str(school.id)


@pytest.mark.django_db
def test_unknown_subdomain_returns_404(client):
    response = client.get("/health/", HTTP_HOST="unknown.localhost")
    assert response.status_code == 404
```

- [ ] **Step 2: Write a failing cross-school manager test**

```python
@pytest.mark.django_db
def test_tenant_queryset_requires_explicit_school(school_factory, note_factory):
    first = school_factory()
    second = school_factory()
    note_factory(school=first, title="First")
    note_factory(school=second, title="Second")
    assert list(Note.objects.for_school(first).values_list("title", flat=True)) == ["First"]
```

- [ ] **Step 3: Run tenant tests and verify failure**

Run: `uv run pytest apps/tenancy/tests -q`

Expected: FAIL because tenant middleware and managers do not exist.

- [ ] **Step 4: Implement tenant context and queryset**

```python
# apps/tenancy/managers.py
from django.db import models


class TenantQuerySet(models.QuerySet):
    def for_school(self, school):
        if school is None:
            raise ValueError("school is required")
        return self.filter(school=school)


class TenantManager(models.Manager.from_queryset(TenantQuerySet)):
    pass
```

- [ ] **Step 5: Implement domain resolution middleware**

```python
# apps/tenancy/middleware.py
from django.http import Http404

from apps.tenancy.models import SchoolDomain


class TenantMiddleware:
    platform_hosts = {"localhost", "127.0.0.1", "testserver"}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":", 1)[0].lower()
        request.school = None
        if host not in self.platform_hosts:
            domain = (
                SchoolDomain.objects.select_related("school")
                .filter(hostname=host, school__is_active=True)
                .first()
            )
            if domain is None:
                raise Http404("School not found")
            request.school = domain.school
        response = self.get_response(request)
        if request.school:
            response.headers["X-Elora-School"] = str(request.school.id)
        return response
```

- [ ] **Step 6: Register middleware before authentication**

Insert `"apps.tenancy.middleware.TenantMiddleware"` before `AuthenticationMiddleware`.

- [ ] **Step 7: Run tenant tests**

Run: `uv run pytest apps/tenancy/tests -q`

Expected: PASS.

- [ ] **Step 8: Commit tenant isolation**

```powershell
git add apps/tenancy config/settings/base.py
git commit -m "feat: resolve and scope school tenants"
```

### Task 5: Add Role Permissions And Authorization Guards

**Files:**
- Create: `apps/accounts/permissions.py`
- Create: `apps/accounts/decorators.py`
- Create: `apps/accounts/management/commands/seed_roles.py`
- Test: `apps/accounts/tests/test_permissions.py`

- [ ] **Step 1: Write failing authorization tests**

```python
import pytest

from apps.accounts.permissions import has_school_role


@pytest.mark.django_db
def test_role_check_uses_active_school_membership(user_factory, membership_factory, school_factory):
    user = user_factory()
    first = school_factory()
    second = school_factory()
    membership_factory(user=user, school=first, role_code="school_admin")
    assert has_school_role(user, first, "school_admin")
    assert not has_school_role(user, second, "school_admin")
```

- [ ] **Step 2: Run permission tests and verify failure**

Run: `uv run pytest apps/accounts/tests/test_permissions.py -q`

Expected: FAIL because role helpers do not exist.

- [ ] **Step 3: Define stable role codes**

```python
# apps/accounts/roles.py
ROLE_DEFINITIONS = {
    "super_admin": ("Super Admin", True),
    "school_admin": ("School Admin", False),
    "principal": ("Principal", False),
    "deputy_principal": ("Deputy Principal", False),
    "teacher": ("Teacher", False),
    "class_teacher": ("Class Teacher", False),
    "department_head": ("Department Head", False),
    "parent": ("Parent", False),
    "learner": ("Learner", False),
    "accountant": ("Accountant", False),
    "librarian": ("Librarian", False),
    "guidance_counsellor": ("Guidance & Counselling Officer", False),
}
```

- [ ] **Step 4: Implement role checks**

```python
# apps/accounts/permissions.py
from apps.accounts.models import Membership


def has_school_role(user, school, *role_codes):
    if not user.is_authenticated or school is None:
        return False
    return Membership.objects.filter(
        user=user,
        school=school,
        roles__code__in=role_codes,
        is_active=True,
    ).exists()
```

- [ ] **Step 5: Add deterministic role seeding**

```python
# apps/accounts/management/commands/seed_roles.py
from django.core.management.base import BaseCommand

from apps.accounts.models import Role
from apps.accounts.roles import ROLE_DEFINITIONS


class Command(BaseCommand):
    def handle(self, *args, **options):
        for code, (name, is_platform_role) in ROLE_DEFINITIONS.items():
            Role.objects.update_or_create(
                code=code,
                defaults={"name": name, "is_platform_role": is_platform_role},
            )
```

- [ ] **Step 6: Run permission tests and seed roles**

Run:

```powershell
uv run python manage.py seed_roles
uv run pytest apps/accounts/tests/test_permissions.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit authorization**

```powershell
git add apps/accounts
git commit -m "feat: add school role authorization"
```

### Task 6: Build Tenant-Aware Login And Session Flow

**Files:**
- Create: `apps/accounts/forms.py`
- Create: `apps/accounts/views.py`
- Create: `apps/accounts/urls.py`
- Create: `templates/accounts/login.html`
- Create: `templates/accounts/logged_out.html`
- Modify: `config/urls.py`
- Test: `apps/accounts/tests/test_auth_views.py`

- [ ] **Step 1: Write failing login tests**

```python
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_member_can_log_into_school(client, membership_factory):
    membership = membership_factory(password="correct-horse")
    response = client.post(
        reverse("accounts:login"),
        {"username": membership.user.email, "password": "correct-horse"},
        HTTP_HOST=membership.school.domains.get(is_primary=True).hostname,
    )
    assert response.status_code == 302
    assert response.url == reverse("analytics:dashboard")


@pytest.mark.django_db
def test_non_member_cannot_log_into_school(client, user_factory, school_domain_factory):
    user = user_factory(password="correct-horse")
    domain = school_domain_factory()
    response = client.post(
        reverse("accounts:login"),
        {"username": user.email, "password": "correct-horse"},
        HTTP_HOST=domain.hostname,
    )
    assert response.status_code == 200
    assert "You do not have access to this school." in response.content.decode()
```

- [ ] **Step 2: Run login tests and verify failure**

Run: `uv run pytest apps/accounts/tests/test_auth_views.py -q`

Expected: FAIL because tenant-aware authentication views do not exist.

- [ ] **Step 3: Implement tenant-aware authentication form**

```python
# apps/accounts/forms.py
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from apps.accounts.models import Membership


class SchoolAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        school = getattr(self.request, "school", None)
        if school and not Membership.objects.filter(
            user=user,
            school=school,
            is_active=True,
        ).exists():
            raise ValidationError(
                "You do not have access to this school.",
                code="invalid_school_membership",
            )
```

- [ ] **Step 4: Wire login and logout views**

```python
# apps/accounts/urls.py
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from apps.accounts.forms import SchoolAuthenticationForm

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=SchoolAuthenticationForm,
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
]
```

- [ ] **Step 5: Create the branded login template**

```html
{% extends "layouts/public.html" %}
{% block title %}Sign in | Elora{% endblock %}
{% block content %}
<main class="mx-auto flex min-h-screen max-w-md items-center px-6">
  <section class="w-full rounded-3xl bg-white p-8 shadow-xl">
    <p class="text-sm font-semibold text-blue-700">Elora</p>
    <h1 class="mt-2 text-3xl font-bold text-slate-950">Welcome back</h1>
    <p class="mt-2 text-slate-600">Powering Modern Education</p>
    <form method="post" class="mt-8 space-y-5">
      {% csrf_token %}
      {{ form.as_p }}
      <button class="w-full rounded-xl bg-blue-700 px-4 py-3 font-semibold text-white">
        Sign in
      </button>
    </form>
  </section>
</main>
{% endblock %}
```

- [ ] **Step 6: Run authentication tests**

Run: `uv run pytest apps/accounts/tests/test_auth_views.py -q`

Expected: PASS.

- [ ] **Step 7: Commit authentication flow**

```powershell
git add apps/accounts templates/accounts config/urls.py
git commit -m "feat: add tenant-aware authentication"
```

### Task 7: Build The Responsive Application Shell

**Files:**
- Create: `package.json`
- Create: `assets/css/input.css`
- Create: `static/js/app.js`
- Create: `templates/layouts/public.html`
- Create: `templates/layouts/app.html`
- Create: `templates/components/sidebar.html`
- Create: `templates/components/topbar.html`
- Create: `templates/components/messages.html`
- Test: `tests/test_app_shell.py`

- [ ] **Step 1: Write failing application shell tests**

```python
import pytest
from django.urls import reverse


from pathlib import Path


def test_authenticated_shell_has_responsive_navigation():
    content = Path("templates/layouts/app.html").read_text()
    assert 'name="viewport"' in content
    assert 'x-data="{ sidebarOpen: false }"' in content
    assert "lg:grid-cols" in content
```

- [ ] **Step 2: Run the shell test and verify failure**

Run: `uv run pytest tests/test_app_shell.py -q`

Expected: FAIL because the dashboard and shell do not exist.

- [ ] **Step 3: Configure frontend dependencies**

```json
{
  "private": true,
  "scripts": {
    "css:build": "tailwindcss -i ./assets/css/input.css -o ./static/css/app.css --minify",
    "css:watch": "tailwindcss -i ./assets/css/input.css -o ./static/css/app.css --watch"
  },
  "devDependencies": {
    "@tailwindcss/cli": "^4.1.0",
    "tailwindcss": "^4.1.0"
  },
  "dependencies": {
    "alpinejs": "^3.14.0",
    "chart.js": "^4.4.0",
    "htmx.org": "^2.0.0"
  }
}
```

- [ ] **Step 4: Create the Tailwind input**

```css
@import "tailwindcss";
@source "../../templates";
@source "../../apps";

@theme {
  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
  --color-elora-blue: #1d4ed8;
  --color-elora-teal: #0f766e;
}

@layer base {
  body {
    @apply bg-slate-50 text-slate-900 antialiased;
  }
  input, select, textarea {
    @apply w-full rounded-xl border border-slate-300 bg-white px-3 py-2;
  }
}
```

- [ ] **Step 5: Create the authenticated shell**

```html
<!doctype html>
<html lang="en" x-data="{ sidebarOpen: false }">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Elora{% endblock %}</title>
  <link rel="stylesheet" href="/static/css/app.css">
  <script defer src="/static/js/app.js"></script>
</head>
<body>
  <div class="min-h-screen lg:grid lg:grid-cols-[17rem_1fr]">
    {% include "components/sidebar.html" %}
    <div class="min-w-0">
      {% include "components/topbar.html" %}
      <main id="main-content" class="p-4 sm:p-6 lg:p-8">
        {% include "components/messages.html" %}
        {% block content %}{% endblock %}
      </main>
    </div>
  </div>
</body>
</html>
```

- [ ] **Step 6: Build assets and run shell tests**

Run:

```powershell
npm install
npm run css:build
uv run pytest tests/test_app_shell.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit the interface shell**

```powershell
git add package.json package-lock.json assets static templates
git commit -m "feat: add responsive Elora application shell"
```

### Task 8: Add Role-Specific Dashboards

**Files:**
- Create: `apps/analytics/apps.py`
- Create: `apps/analytics/dashboard_registry.py`
- Create: `apps/analytics/views.py`
- Create: `apps/analytics/urls.py`
- Create: `templates/analytics/dashboard.html`
- Create: `templates/analytics/partials/metric_card.html`
- Modify: `config/urls.py`
- Modify: `config/settings/base.py`
- Test: `apps/analytics/tests/test_dashboards.py`

- [ ] **Step 1: Write failing dashboard routing tests**

```python
import pytest
from django.urls import reverse


@pytest.mark.parametrize(
    ("role_code", "expected_heading"),
    [
        ("school_admin", "School operations"),
        ("principal", "School performance"),
        ("teacher", "Teaching today"),
        ("parent", "My learners"),
        ("learner", "My learning"),
        ("accountant", "Finance overview"),
        ("librarian", "Library overview"),
        ("guidance_counsellor", "Learner wellbeing"),
    ],
)
@pytest.mark.django_db
def test_dashboard_matches_role(
    client, membership_factory, role_code, expected_heading
):
    membership = membership_factory(role_code=role_code)
    client.force_login(membership.user)
    response = client.get(
        reverse("analytics:dashboard"),
        HTTP_HOST=membership.school.domains.get(is_primary=True).hostname,
    )
    assert expected_heading in response.content.decode()
```

- [ ] **Step 2: Run dashboard tests and verify failure**

Run: `uv run pytest apps/analytics/tests/test_dashboards.py -q`

Expected: FAIL because dashboard routing does not exist.

- [ ] **Step 3: Implement the role dashboard registry**

```python
# apps/analytics/dashboard_registry.py
DASHBOARDS = {
    "school_admin": {"heading": "School operations", "metrics": []},
    "principal": {"heading": "School performance", "metrics": []},
    "deputy_principal": {"heading": "Daily oversight", "metrics": []},
    "teacher": {"heading": "Teaching today", "metrics": []},
    "class_teacher": {"heading": "My class", "metrics": []},
    "department_head": {"heading": "Department performance", "metrics": []},
    "parent": {"heading": "My learners", "metrics": []},
    "learner": {"heading": "My learning", "metrics": []},
    "accountant": {"heading": "Finance overview", "metrics": []},
    "librarian": {"heading": "Library overview", "metrics": []},
    "guidance_counsellor": {"heading": "Learner wellbeing", "metrics": []},
}
```

- [ ] **Step 4: Implement dashboard selection**

```python
# apps/analytics/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.accounts.models import Membership
from apps.analytics.dashboard_registry import DASHBOARDS


@login_required
def dashboard(request):
    membership = (
        Membership.objects.select_related("school")
        .prefetch_related("roles")
        .filter(user=request.user, school=request.school, is_active=True)
        .first()
    )
    if membership is None:
        return render(request, "403.html", status=403)
    role = membership.roles.order_by("name").first()
    dashboard_config = DASHBOARDS.get(
        role.code if role else "",
        {"heading": "Dashboard", "metrics": []},
    )
    return render(
        request,
        "analytics/dashboard.html",
        {"membership": membership, "active_role": role, "dashboard": dashboard_config},
    )
```

- [ ] **Step 5: Create the dashboard template**

```html
{% extends "layouts/app.html" %}
{% block title %}{{ dashboard.heading }} | Elora{% endblock %}
{% block content %}
<header>
  <p class="text-sm font-semibold text-blue-700">{{ active_role.name }}</p>
  <h1 class="mt-1 text-3xl font-bold tracking-tight">{{ dashboard.heading }}</h1>
  <p class="mt-2 text-slate-600">{{ membership.school.name }}</p>
</header>
<section class="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
  {% for metric in dashboard.metrics %}
    {% include "analytics/partials/metric_card.html" with metric=metric %}
  {% empty %}
    <div class="rounded-2xl border border-dashed border-slate-300 bg-white p-6">
      Module metrics will appear as school records are added.
    </div>
  {% endfor %}
</section>
{% endblock %}
```

Add `"apps.analytics"` to `INSTALLED_APPS` and include `apps.analytics.urls`.

- [ ] **Step 6: Run dashboard and shell tests**

Run:

```powershell
uv run pytest apps/analytics/tests/test_dashboards.py tests/test_app_shell.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit dashboards**

```powershell
git add apps/analytics templates/analytics config/urls.py
git commit -m "feat: add role-specific dashboards"
```

### Task 9: Configure Admin And Audit Logging

**Files:**
- Create: `apps/accounts/audit.py`
- Modify: `apps/accounts/models.py`
- Create: `apps/accounts/admin.py`
- Create: `apps/tenancy/admin.py`
- Create: `apps/accounts/migrations/0002_auditlog.py`
- Test: `apps/accounts/tests/test_audit.py`
- Test: `apps/accounts/tests/test_admin.py`

- [ ] **Step 1: Write failing audit tests**

```python
import pytest

from apps.accounts.audit import record_audit_event
from apps.accounts.models import AuditLog


@pytest.mark.django_db
def test_audit_event_keeps_school_actor_and_request_id(
    school_factory, user_factory
):
    school = school_factory()
    actor = user_factory()
    event = record_audit_event(
        school=school,
        actor=actor,
        action="membership.created",
        target_type="Membership",
        target_id="abc",
        request_id="request-123",
        metadata={"role": "teacher"},
    )
    assert AuditLog.objects.get(pk=event.pk).metadata == {"role": "teacher"}
```

- [ ] **Step 2: Run audit tests and verify failure**

Run: `uv run pytest apps/accounts/tests/test_audit.py -q`

Expected: FAIL because audit storage does not exist.

- [ ] **Step 3: Implement append-only audit records**

```python
class AuditLog(UUIDModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=120)
    target_type = models.CharField(max_length=120)
    target_id = models.CharField(max_length=64)
    request_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
```

- [ ] **Step 4: Implement the audit service**

```python
# apps/accounts/audit.py
from apps.accounts.models import AuditLog


def record_audit_event(
    *,
    school,
    actor,
    action,
    target_type,
    target_id,
    request_id="",
    metadata=None,
):
    return AuditLog.objects.create(
        school=school,
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        request_id=request_id,
        metadata=metadata or {},
    )
```

- [ ] **Step 5: Register tenant-safe admin classes**

Register `School`, `SchoolDomain`, `User`, `Role`, `Membership`, and read-only `AuditLog`. Prevent audit changes and deletes in `AuditLogAdmin`.

- [ ] **Step 6: Migrate and run audit/admin tests**

Run:

```powershell
uv run python manage.py makemigrations accounts
uv run python manage.py migrate
uv run pytest apps/accounts/tests/test_audit.py apps/accounts/tests/test_admin.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit admin and audit**

```powershell
git add apps/accounts apps/tenancy
git commit -m "feat: add administration and audit logging"
```

### Task 10: Add Celery And Tenant-Safe Background Tasks

**Files:**
- Create: `config/celery.py`
- Modify: `config/__init__.py`
- Modify: `config/settings/base.py`
- Create: `apps/tenancy/tasks.py`
- Test: `apps/tenancy/tests/test_tasks.py`

- [ ] **Step 1: Write a failing tenant-task test**

```python
import pytest

from apps.tenancy.tasks import school_task


@pytest.mark.django_db
def test_school_task_requires_existing_school(school_factory):
    school = school_factory()
    assert school_task.run(str(school.id)) == {"school_id": str(school.id)}
```

- [ ] **Step 2: Run the task test and verify failure**

Run: `uv run pytest apps/tenancy/tests/test_tasks.py -q`

Expected: FAIL because Celery configuration and the task do not exist.

- [ ] **Step 3: Configure Celery**

```python
# config/celery.py
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("elora")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

- [ ] **Step 4: Add a tenant-safe task base**

```python
# apps/tenancy/tasks.py
from celery import shared_task

from apps.tenancy.models import School


@shared_task
def school_task(school_id):
    school = School.objects.get(pk=school_id, is_active=True)
    return {"school_id": str(school.id)}
```

- [ ] **Step 5: Configure Redis and eager test tasks**

Add `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, and JSON-only serializer settings in `base.py`; set `CELERY_TASK_ALWAYS_EAGER = True` in `test.py`.

- [ ] **Step 6: Run task tests**

Run: `uv run pytest apps/tenancy/tests/test_tasks.py -q`

Expected: PASS.

- [ ] **Step 7: Commit task infrastructure**

```powershell
git add config apps/tenancy
git commit -m "feat: add tenant-safe background tasks"
```

### Task 11: Add Docker Development And Production Images

**Files:**
- Create: `Dockerfile`
- Create: `compose.yaml`
- Create: `docker/entrypoint.sh`
- Create: `.dockerignore`
- Test: `tests/test_container_config.py`

- [ ] **Step 1: Write failing container configuration tests**

```python
from pathlib import Path


def test_compose_defines_required_services():
    compose = Path("compose.yaml").read_text()
    for service in ("web:", "db:", "redis:", "worker:", "scheduler:"):
        assert service in compose


def test_production_image_runs_as_non_root():
    dockerfile = Path("Dockerfile").read_text()
    assert "USER elora" in dockerfile
```

- [ ] **Step 2: Run the container tests and verify failure**

Run: `uv run pytest tests/test_container_config.py -q`

Expected: FAIL because container files do not exist.

- [ ] **Step 3: Create the multi-stage Dockerfile**

```dockerfile
FROM python:3.13-slim AS builder
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.13-slim AS runtime
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN addgroup --system elora && adduser --system --ingroup elora elora
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .
RUN python manage.py collectstatic --noinput
USER elora
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: Create Docker Compose services**

```yaml
services:
  web:
    build: .
    command: uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload
    env_file: .env
    ports: ["8000:8000"]
    depends_on: [db, redis]
  worker:
    build: .
    command: celery -A config worker -l INFO
    env_file: .env
    depends_on: [db, redis]
  scheduler:
    build: .
    command: celery -A config beat -l INFO
    env_file: .env
    depends_on: [db, redis]
  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: elora
      POSTGRES_USER: elora
      POSTGRES_PASSWORD: elora
    volumes: [postgres_data:/var/lib/postgresql/data]
  redis:
    image: redis:7-alpine

volumes:
  postgres_data:
```

- [ ] **Step 5: Run configuration tests and build**

Run:

```powershell
uv run pytest tests/test_container_config.py -q
docker compose config
docker compose build
```

Expected: tests pass, Compose validates, and images build.

- [ ] **Step 6: Commit container setup**

```powershell
git add Dockerfile compose.yaml docker .dockerignore
git commit -m "build: add Docker development stack"
```

### Task 12: Add Factories And Deterministic Seed Data

**Files:**
- Create: `tests/factories.py`
- Create: `tests/conftest.py`
- Create: `apps/core/management/commands/seed_demo.py`
- Test: `apps/core/tests/test_seed_demo.py`

- [ ] **Step 1: Write a failing seed-data test**

```python
import pytest
from django.core.management import call_command

from apps.accounts.models import Membership
from apps.tenancy.models import School


@pytest.mark.django_db
def test_seed_demo_is_idempotent():
    call_command("seed_demo")
    call_command("seed_demo")
    assert School.objects.filter(slug="green-hills").count() == 1
    assert Membership.objects.filter(school__slug="green-hills").count() == 11
    assert User.objects.filter(email="super_admin@elora.local", is_superuser=True).count() == 1
```

- [ ] **Step 2: Run the seed test and verify failure**

Run: `uv run pytest apps/core/tests/test_seed_demo.py -q`

Expected: FAIL because the command does not exist.

- [ ] **Step 3: Implement reusable test factories**

Create factories for `School`, `SchoolDomain`, `User`, `Role`, and `Membership`. A membership factory must create a primary `*.localhost` domain and accept `role_code` and `password`.

- [ ] **Step 4: Implement deterministic demo seeding**

```python
# apps/core/management/commands/seed_demo.py
from django.core.management.base import BaseCommand

from apps.accounts.models import Membership, Role, User
from apps.accounts.roles import ROLE_DEFINITIONS
from apps.tenancy.models import School, SchoolDomain


class Command(BaseCommand):
    def handle(self, *args, **options):
        school, _ = School.objects.update_or_create(
            slug="green-hills",
            defaults={"name": "Green Hills Academy"},
        )
        SchoolDomain.objects.update_or_create(
            hostname="green-hills.localhost",
            defaults={"school": school, "is_primary": True},
        )
        for code, (name, is_platform_role) in ROLE_DEFINITIONS.items():
            role, _ = Role.objects.update_or_create(
                code=code,
                defaults={"name": name, "is_platform_role": is_platform_role},
            )
            if is_platform_role:
                user, created = User.objects.get_or_create(
                    email="super_admin@elora.local",
                    defaults={"is_staff": True, "is_superuser": True},
                )
                if created:
                    user.set_password("EloraDemo123!")
                    user.save(update_fields=["password"])
                continue
            email = f"{code}@green-hills.localhost"
            user, created = User.objects.get_or_create(email=email)
            if created:
                user.set_password("EloraDemo123!")
                user.save(update_fields=["password"])
            membership, _ = Membership.objects.get_or_create(
                school=school,
                user=user,
            )
            membership.roles.add(role)
```

- [ ] **Step 5: Run seed tests**

Run:

```powershell
uv run python manage.py seed_demo
uv run pytest apps/core/tests/test_seed_demo.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit factories and seed data**

```powershell
git add tests apps/core
git commit -m "test: add factories and deterministic demo data"
```

### Task 13: Add PostgreSQL Row-Level Security

**Files:**
- Create: `apps/tenancy/rls.py`
- Create: `apps/tenancy/migrations/0002_enable_rls.py`
- Modify: `apps/tenancy/middleware.py`
- Test: `apps/tenancy/tests/test_rls.py`

- [ ] **Step 1: Write a PostgreSQL-only failing RLS test**

```python
import pytest
from django.db import connection


@pytest.mark.django_db(transaction=True)
def test_rls_blocks_cross_school_memberships(
    first_school,
    second_school,
    user_factory,
    role_factory,
):
    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL RLS test")
    role = role_factory(code="teacher")
    first_user = user_factory(email="first@example.test")
    second_user = user_factory(email="second@example.test")
    first = Membership.objects.create(school=first_school, user=first_user)
    second = Membership.objects.create(school=second_school, user=second_user)
    first.roles.add(role)
    second.roles.add(role)
    with connection.cursor() as cursor:
        cursor.execute("SET LOCAL app.current_school = %s", [str(first_school.id)])
        cursor.execute("SELECT user_id FROM accounts_membership")
        assert cursor.fetchall() == [(first_user.id,)]
```

- [ ] **Step 2: Run the RLS test against PostgreSQL and verify failure**

Run: `docker compose run --rm web pytest apps/tenancy/tests/test_rls.py -q`

Expected: FAIL because no RLS policy exists.

- [ ] **Step 3: Add transaction-scoped tenant context**

```python
# apps/tenancy/rls.py
from django.db import connection


def set_database_school(school_id):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.current_school', %s, true)",
            [str(school_id)],
        )
```

- [ ] **Step 4: Add explicit RLS policies through migrations**

Use `RunSQL` to enable and force RLS on each tenant table introduced in the milestone. Each policy compares `school_id` with `current_setting('app.current_school', true)::uuid`. Include reverse SQL that drops the policy and disables RLS.

- [ ] **Step 5: Set database tenant context in middleware**

After resolving `request.school`, call `set_database_school(request.school.id)` inside Django's request transaction. Production settings enable `ATOMIC_REQUESTS` for the default database.

- [ ] **Step 6: Run all tenant tests against PostgreSQL**

Run:

```powershell
docker compose run --rm web pytest apps/tenancy/tests apps/accounts/tests/test_permissions.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit RLS**

```powershell
git add apps/tenancy config/settings
git commit -m "security: enforce PostgreSQL tenant row policies"
```

### Task 14: Add CI, Security Settings, And Documentation

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `README.md`
- Create: `docs/operations/school-provisioning.md`
- Create: `docs/operations/backup-restore.md`
- Modify: `config/settings/production.py`
- Test: `tests/test_production_settings.py`

- [ ] **Step 1: Write failing production setting tests**

```python
def test_production_settings_enable_secure_cookies(settings):
    assert settings.SESSION_COOKIE_SECURE is True
    assert settings.CSRF_COOKIE_SECURE is True
    assert settings.SECURE_SSL_REDIRECT is True


def test_production_settings_disable_debug(settings):
    assert settings.DEBUG is False
```

- [ ] **Step 2: Run tests against production settings and verify failure**

Run:

```powershell
$env:DJANGO_SETTINGS_MODULE="config.settings.production"
uv run pytest tests/test_production_settings.py -q
```

Expected: FAIL until production settings are hardened.

- [ ] **Step 3: Harden production settings**

```python
# config/settings/production.py
from .base import *  # noqa: F403

DEBUG = False
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
```

- [ ] **Step 4: Add CI**

```yaml
name: CI
on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_DB: elora_test
          POSTGRES_USER: elora
          POSTGRES_PASSWORD: elora
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          python-version: "3.13"
      - run: uv sync --frozen
      - run: npm ci && npm run css:build
      - run: uv run ruff check .
      - run: uv run mypy apps config
      - run: uv run python manage.py makemigrations --check
      - run: uv run pytest --cov=apps --cov-fail-under=85
      - run: uv run python manage.py check --deploy
```

- [ ] **Step 5: Document setup and operations**

README commands must include:

```powershell
Copy-Item .env.example .env
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_demo
```

Document wildcard local domains, demo credentials, school provisioning, PostgreSQL backup, media backup, and restore verification.

- [ ] **Step 6: Run the full foundation verification**

Run:

```powershell
uv run ruff check .
uv run mypy apps config
uv run python manage.py makemigrations --check
uv run pytest --cov=apps --cov-fail-under=85
$env:DJANGO_SETTINGS_MODULE="config.settings.production"
uv run python manage.py check --deploy
docker compose config
```

Expected: all commands exit 0.

- [ ] **Step 7: Commit CI and documentation**

```powershell
git add .github README.md docs/operations config/settings/production.py tests
git commit -m "ci: verify and document Elora foundation"
```

## Foundation Completion Criteria

- [ ] Two school domains resolve to separate active tenant contexts.
- [ ] Cross-school model, view, form, task, and RLS tests pass.
- [ ] The platform Super Admin and all eleven school-scoped roles reach authorized dashboards.
- [ ] Non-members cannot authenticate into a school tenant.
- [ ] The authenticated shell works at mobile and desktop widths.
- [ ] Demo data can be seeded repeatedly without duplication.
- [ ] Docker services build and start.
- [ ] The full test, lint, type, migration, and deployment checks pass.
