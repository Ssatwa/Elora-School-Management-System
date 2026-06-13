from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, render

from apps.accounts.decorators import school_roles_required
from apps.staff.forms import DepartmentForm, StaffAssignmentForm, TeacherProfileForm
from apps.staff.models import Department, StaffAssignment, TeacherProfile
from apps.staff.services import assign_staff

STAFF_ADMIN_ROLES = (
    "school_admin",
    "principal",
    "deputy_principal",
    "department_head",
)
FORM_TYPES = {
    "teacher": TeacherProfileForm,
    "department": DepartmentForm,
    "assignment": StaffAssignmentForm,
}


def _staff_context(school, *, query="", bound_form=None, model_name=""):
    teachers = TeacherProfile.objects.for_school(school).select_related(
        "membership__user"
    )
    if query:
        teachers = teachers.filter(
            Q(employee_number__icontains=query)
            | Q(membership__user__first_name__icontains=query)
            | Q(membership__user__last_name__icontains=query)
            | Q(membership__user__email__icontains=query)
        )
    forms = {
        name: form_type(school=school)
        for name, form_type in FORM_TYPES.items()
    }
    if bound_form is not None:
        forms[model_name] = bound_form
    return {
        "teachers": teachers,
        "departments": Department.objects.for_school(school).select_related("head"),
        "assignments": StaffAssignment.objects.for_school(school).select_related(
            "teacher__membership__user",
            "learning_area",
            "grade",
            "stream",
        ),
        "teacher_form": forms["teacher"],
        "department_form": forms["department"],
        "assignment_form": forms["assignment"],
    }


@login_required
@school_roles_required(*STAFF_ADMIN_ROLES)
def index(request):
    context = _staff_context(
        request.school,
        query=request.GET.get("q", "").strip(),
    )
    template = "staff/partials/staff_tables.html" if request.htmx else "staff/index.html"
    return render(request, template, context)


@login_required
@school_roles_required(*STAFF_ADMIN_ROLES)
def create(request, model_name):
    form_type = FORM_TYPES.get(model_name)
    if form_type is None:
        raise Http404
    if request.method != "POST":
        return redirect("staff:index")

    form = form_type(request.POST, school=request.school)
    if form.is_valid():
        if model_name == "assignment":
            assign_staff(
                school=request.school,
                actor=request.user,
                **form.cleaned_data,
            )
        else:
            form.save()
        messages.success(request, "Staff records updated.")
        return redirect("staff:index")

    context = _staff_context(
        request.school,
        bound_form=form,
        model_name=model_name,
    )
    return render(request, "staff/index.html", context, status=400)
