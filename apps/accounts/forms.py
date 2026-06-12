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
