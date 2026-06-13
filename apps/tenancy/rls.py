from django.db import connection


def set_database_school(school_id):
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT set_config('app.current_school', %s, false)",
            [str(school_id)],
        )


def clear_database_school():
    if connection.vendor != "postgresql":
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('app.current_school', '', false)")
