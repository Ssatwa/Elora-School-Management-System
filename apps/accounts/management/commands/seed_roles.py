from django.core.management.base import BaseCommand

from apps.accounts.models import Role
from apps.accounts.roles import ROLE_DEFINITIONS


class Command(BaseCommand):
    help = "Create or update Elora's stable role catalogue."

    def handle(self, *args, **options):
        for code, (name, is_platform_role) in ROLE_DEFINITIONS.items():
            Role.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "is_platform_role": is_platform_role,
                },
            )
