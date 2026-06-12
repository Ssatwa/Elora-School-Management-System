from contextvars import ContextVar

current_school = ContextVar("current_school", default=None)


def get_current_school():
    return current_school.get()
