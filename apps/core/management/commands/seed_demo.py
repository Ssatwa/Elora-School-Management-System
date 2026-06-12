from django.core.management.base import BaseCommand

from apps.accounts.models import Membership, Role, User
from apps.accounts.roles import ROLE_DEFINITIONS
from apps.tenancy.models import School, SchoolDomain


class Command(BaseCommand):
    help = "Create deterministic local demo schools, roles, and users."

    def handle(self, *args, **options):
        school, _ = School.objects.update_or_create(
            slug="green-hills",
            defaults={"name": "Green Hills Academy", "is_active": True},
        )
        SchoolDomain.objects.update_or_create(
            hostname="green-hills.localhost",
            defaults={"school": school, "is_primary": True},
        )

        for code, (name, is_platform_role) in ROLE_DEFINITIONS.items():
            role, _ = Role.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "is_platform_role": is_platform_role,
                },
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

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
