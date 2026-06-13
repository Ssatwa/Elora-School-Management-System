from apps.accounts.permissions import has_school_role


def school_module_access(request):
    school = getattr(request, "school", None)
    user = request.user
    return {
        "can_manage_academics": has_school_role(
            user,
            school,
            "school_admin",
            "principal",
            "deputy_principal",
        ),
        "can_manage_staff": has_school_role(
            user,
            school,
            "school_admin",
            "principal",
            "deputy_principal",
            "department_head",
        ),
        "can_view_learners": has_school_role(
            user,
            school,
            "school_admin",
            "principal",
            "deputy_principal",
            "teacher",
            "class_teacher",
            "department_head",
            "guidance_counsellor",
        ),
        "can_administer_learners": has_school_role(
            user,
            school,
            "school_admin",
            "principal",
            "deputy_principal",
        ),
    }
