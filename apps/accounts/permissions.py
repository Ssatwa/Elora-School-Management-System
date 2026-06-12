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
