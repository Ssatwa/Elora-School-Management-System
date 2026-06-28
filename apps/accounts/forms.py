from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from apps.accounts.models import Membership


class SchoolAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not Membership.objects.filter(
            user=user,
            is_active=True,
            school__is_active=True,
        ).exists():
            raise ValidationError(
                "Your account is not linked to an active school.",
                code="missing_school_membership",
            )
