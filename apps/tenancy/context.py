from contextvars import ContextVar
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.tenancy.models import School

current_school: ContextVar["School | None"] = ContextVar(
    "current_school",
    default=None,
)


def get_current_school():
    return current_school.get()
