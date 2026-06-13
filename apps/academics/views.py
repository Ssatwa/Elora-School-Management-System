from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect, render

from apps.academics.forms import (
    AcademicYearForm,
    CompetencyForm,
    GradeForm,
    LearningAreaForm,
    StreamForm,
)
from apps.academics.models import (
    AcademicYear,
    Competency,
    Grade,
    LearningArea,
    Stream,
)
from apps.accounts.decorators import school_roles_required

ACADEMIC_ADMIN_ROLES = ("school_admin", "principal", "deputy_principal")
FORM_TYPES = {
    "academic-year": AcademicYearForm,
    "grade": GradeForm,
    "stream": StreamForm,
    "learning-area": LearningAreaForm,
    "competency": CompetencyForm,
}


def _structure_context(school, *, query="", bound_form=None, model_name=""):
    grades = Grade.objects.for_school(school).select_related("school")
    learning_areas = LearningArea.objects.for_school(school)
    if query:
        grades = grades.filter(Q(name__icontains=query) | Q(code__icontains=query))
        learning_areas = learning_areas.filter(
            Q(name__icontains=query) | Q(code__icontains=query)
        )
    forms = {
        name: form_type(school=school)
        for name, form_type in FORM_TYPES.items()
    }
    if bound_form is not None:
        forms[model_name] = bound_form
    return {
        "academic_years": AcademicYear.objects.for_school(school),
        "grades": grades,
        "streams": Stream.objects.for_school(school).select_related("grade"),
        "learning_areas": learning_areas,
        "competencies": Competency.objects.for_school(school),
        "academic_year_form": forms["academic-year"],
        "grade_form": forms["grade"],
        "stream_form": forms["stream"],
        "learning_area_form": forms["learning-area"],
        "competency_form": forms["competency"],
    }


@login_required
@school_roles_required(*ACADEMIC_ADMIN_ROLES)
def structure(request):
    context = _structure_context(request.school, query=request.GET.get("q", "").strip())
    template = (
        "academics/partials/structure_tables.html"
        if request.htmx
        else "academics/structure.html"
    )
    return render(request, template, context)


@login_required
@school_roles_required(*ACADEMIC_ADMIN_ROLES)
def create(request, model_name):
    form_type = FORM_TYPES.get(model_name)
    if form_type is None:
        raise Http404
    if request.method != "POST":
        return redirect("academics:structure")

    form = form_type(request.POST, school=request.school)
    if form.is_valid():
        form.save()
        messages.success(request, "Academic structure updated.")
        return redirect("academics:structure")

    context = _structure_context(
        request.school,
        bound_form=form,
        model_name=model_name,
    )
    return render(request, "academics/structure.html", context, status=400)
