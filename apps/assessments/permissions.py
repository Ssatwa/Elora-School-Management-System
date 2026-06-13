from apps.accounts.permissions import has_school_role


def can_enter_assessment(user, school, assessment):
    return (
        assessment.school_id == school.id
        and assessment.teacher.membership.user_id == user.id
        and has_school_role(user, school, "teacher", "class_teacher", "department_head")
    )


def can_moderate_assessment(user, school):
    return has_school_role(
        user,
        school,
        "department_head",
        "school_admin",
        "principal",
        "deputy_principal",
    )


def can_approve_assessment(user, school):
    return has_school_role(user, school, "principal", "school_admin")
