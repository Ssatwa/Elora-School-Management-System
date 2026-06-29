from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import ProtectedError
from django.db.models import Q
from django.db.models import Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify

from apps.academics.forms import (
    AcademicYearForm,
    CompetencyForm,
    GradeForm,
    LearningAreaForm,
    StreamLabelForm,
)
from apps.academics.models import (
    AcademicYear,
    Competency,
    Grade,
    LearningArea,
    Stream,
    StreamLabel,
)
from apps.accounts.decorators import school_roles_required

ACADEMIC_ADMIN_ROLES = ("school_admin", "principal", "deputy_principal")
FORM_TYPES = {
    "academic-year": AcademicYearForm,
    "grade": GradeForm,
    "stream": StreamLabelForm,
    "learning-area": LearningAreaForm,
    "competency": CompetencyForm,
}


def _unique_stream_templates_for_school(school):
    return (
        StreamLabel.objects.for_school(school)
        .filter(is_active=True)
        .order_by("name")
    )


def _unique_stream_code(school, grade, base_code, name):
    root = slugify(base_code or name)[:24] or "stream"
    candidate = root
    suffix = 2
    while Stream.objects.for_school(school).filter(grade=grade, code=candidate).exists():
        candidate = f"{root[:24]}-{suffix}"
        suffix += 1
    return candidate[:32]


def _create_stream_for_grade(school, grade, label):
    if Stream.objects.for_school(school).filter(
        grade=grade,
        name__iexact=label.name,
    ).exists():
        return False
    Stream.objects.create(
        school=school,
        grade=grade,
        code=_unique_stream_code(school, grade, label.code, label.name),
        name=label.name,
        is_active=True,
    )
    return True


def _create_streams_from_school_templates(school, grade):
    if not grade.is_active:
        return 0
    created_count = 0
    for label in _unique_stream_templates_for_school(school):
        created_count += int(_create_stream_for_grade(school, grade, label))
    return created_count


def _create_streams_for_school_label(school, label):
    if not label.is_active:
        return 0
    created_count = 0
    grades = Grade.objects.for_school(school).filter(is_active=True)
    for grade in grades:
        created_count += int(_create_stream_for_grade(school, grade, label))
    return created_count


def _structure_context(school, *, query="", bound_form=None, model_name=""):
    school_streams = Stream.objects.for_school(school).filter(is_active=True)
    grades = Grade.objects.for_school(school).select_related("school").prefetch_related(
        Prefetch("streams", queryset=school_streams, to_attr="active_streams")
    )
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
        "stream_labels": StreamLabel.objects.for_school(school),
        "streams": school_streams.select_related("grade"),
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
        with transaction.atomic():
            instance = form.save()
            created_stream_count = (
                _create_streams_from_school_templates(request.school, instance)
                if model_name == "grade"
                else _create_streams_for_school_label(request.school, instance)
                if model_name == "stream"
                else 0
            )
        if model_name == "grade" and created_stream_count:
            messages.success(
                request,
                (
                    f"{instance.name} created and connected to "
                    f"{created_stream_count} existing stream label(s)."
                ),
            )
        elif model_name == "stream":
            messages.success(
                request,
                (
                    f"{instance.name} stream created and connected to "
                    f"{created_stream_count} existing grade(s)."
                ),
            )
        else:
            messages.success(request, "Academic structure updated.")
        return redirect("academics:structure")

    context = _structure_context(
        request.school,
        bound_form=form,
        model_name=model_name,
    )
    return render(request, "academics/structure.html", context, status=400)


@login_required
@school_roles_required(*ACADEMIC_ADMIN_ROLES)
def delete_stream_label(request, label_id):
    if request.method != "POST":
        return redirect("academics:structure")

    label = get_object_or_404(StreamLabel.objects.for_school(request.school), id=label_id)
    label_name = label.name
    deleted_count = 0
    archived_count = 0
    with transaction.atomic():
        label.delete()
        streams = list(Stream.objects.for_school(request.school).filter(name__iexact=label_name))
        for stream in streams:
            try:
                with transaction.atomic():
                    stream.delete()
                    deleted_count += 1
            except ProtectedError:
                stream.is_active = False
                stream.save(update_fields=["is_active", "updated_at"])
                archived_count += 1

    if archived_count:
        messages.success(
            request,
            (
                f"{label_name} stream archived. {deleted_count} unused class stream(s) "
                f"deleted and {archived_count} used class stream(s) hidden from setup."
            ),
        )
    else:
        messages.success(request, f"{label_name} stream deleted.")

    return redirect("academics:structure")
