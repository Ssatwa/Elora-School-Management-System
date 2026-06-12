from functools import wraps

from django.core.exceptions import PermissionDenied

from apps.accounts.permissions import has_school_role


def school_roles_required(*role_codes):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not has_school_role(
                request.user,
                getattr(request, "school", None),
                *role_codes,
            ):
                raise PermissionDenied
            return view(request, *args, **kwargs)

        return wrapped

    return decorator
