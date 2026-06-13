from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import school_roles_required
from apps.staff.models import TeacherProfile
from apps.timetabling.forms import (
    RoomForm,
    TimetableEntryForm,
    TimetableForm,
    TimetablePeriodForm,
)
from apps.timetabling.models import Room, Timetable, TimetableEntry, TimetablePeriod
from apps.timetabling.services import (
    add_timetable_entry,
    publish_timetable,
    validate_timetable,
)

TIMETABLE_VIEW_ROLES = (
    "school_admin",
    "principal",
    "deputy_principal",
    "teacher",
    "class_teacher",
    "department_head",
)
TIMETABLE_ADMIN_ROLES = ("school_admin", "principal", "deputy_principal")


def _index_context(school, *, timetable_form=None, room_form=None, period_form=None):
    return {
        "timetables": Timetable.objects.for_school(school)
        .select_related("academic_year", "term", "published_by")
        .prefetch_related("entries"),
        "rooms": Room.objects.for_school(school),
        "periods": TimetablePeriod.objects.for_school(school),
        "timetable_form": timetable_form or TimetableForm(school=school),
        "room_form": room_form or RoomForm(school=school),
        "period_form": period_form or TimetablePeriodForm(school=school),
    }


@login_required
@school_roles_required(*TIMETABLE_VIEW_ROLES)
def index(request):
    return render(request, "timetabling/index.html", _index_context(request.school))


@login_required
@school_roles_required(*TIMETABLE_ADMIN_ROLES)
def create_timetable(request):
    if request.method != "POST":
        return redirect("timetabling:index")
    form = TimetableForm(request.POST, school=request.school)
    if form.is_valid():
        timetable = form.save()
        messages.success(request, "Timetable draft created.")
        return redirect("timetabling:detail", timetable_id=timetable.id)
    return render(
        request,
        "timetabling/index.html",
        _index_context(request.school, timetable_form=form),
        status=400,
    )


@login_required
@school_roles_required(*TIMETABLE_ADMIN_ROLES)
def create_setup(request, setup_type):
    form_types = {"room": RoomForm, "period": TimetablePeriodForm}
    form_type = form_types.get(setup_type)
    if form_type is None:
        raise Http404
    if request.method != "POST":
        return redirect("timetabling:index")
    form = form_type(request.POST, school=request.school)
    if form.is_valid():
        form.save()
        messages.success(request, f"{setup_type.title()} added.")
        return redirect("timetabling:index")
    kwargs = {f"{setup_type}_form": form}
    return render(
        request,
        "timetabling/index.html",
        _index_context(request.school, **kwargs),
        status=400,
    )


@login_required
@school_roles_required(*TIMETABLE_VIEW_ROLES)
def detail(request, timetable_id):
    timetable = get_object_or_404(
        Timetable.objects.for_school(request.school).select_related(
            "academic_year", "term"
        ),
        pk=timetable_id,
    )
    entries = (
        TimetableEntry.objects.for_school(request.school)
        .filter(timetable=timetable)
        .select_related(
            "period",
            "stream__grade",
            "learning_area",
            "teacher__membership__user",
            "room",
        )
    )
    return render(
        request,
        "timetabling/detail.html",
        {
            "timetable": timetable,
            "entries": entries,
            "entry_form": TimetableEntryForm(
                school=request.school,
                timetable=timetable,
            ),
            "conflicts": validate_timetable(school=request.school, timetable=timetable),
        },
    )


@login_required
@school_roles_required(*TIMETABLE_ADMIN_ROLES)
def add_entry(request, timetable_id):
    timetable = get_object_or_404(
        Timetable.objects.for_school(request.school),
        pk=timetable_id,
    )
    if request.method != "POST":
        return redirect("timetabling:detail", timetable_id=timetable.id)
    form = TimetableEntryForm(
        request.POST,
        school=request.school,
        timetable=timetable,
    )
    if form.is_valid():
        try:
            add_timetable_entry(
                school=request.school,
                actor=request.user,
                timetable=timetable,
                **form.cleaned_data,
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "Lesson added to timetable.")
            return redirect("timetabling:detail", timetable_id=timetable.id)
    entries = (
        TimetableEntry.objects.for_school(request.school)
        .filter(timetable=timetable)
        .select_related("period", "stream", "learning_area", "teacher", "room")
    )
    return render(
        request,
        "timetabling/detail.html",
        {
            "timetable": timetable,
            "entries": entries,
            "entry_form": form,
            "conflicts": validate_timetable(school=request.school, timetable=timetable),
        },
        status=400,
    )


@login_required
@school_roles_required(*TIMETABLE_ADMIN_ROLES)
def publish(request, timetable_id):
    timetable = get_object_or_404(
        Timetable.objects.for_school(request.school),
        pk=timetable_id,
    )
    if request.method == "POST":
        try:
            publish_timetable(
                school=request.school,
                actor=request.user,
                timetable=timetable,
            )
        except ValidationError as exc:
            messages.error(request, " ".join(exc.messages))
        else:
            messages.success(request, "Timetable published.")
    return redirect("timetabling:detail", timetable_id=timetable.id)


@login_required
@school_roles_required(*TIMETABLE_VIEW_ROLES)
def my_schedule(request):
    teacher = (
        TeacherProfile.objects.for_school(request.school)
        .filter(membership__user=request.user)
        .first()
    )
    entries = TimetableEntry.objects.none()
    if teacher is not None:
        entries = (
            TimetableEntry.objects.for_school(request.school)
            .filter(teacher=teacher, timetable__status=Timetable.Status.PUBLISHED)
            .select_related("period", "stream__grade", "learning_area", "room")
        )
    return render(
        request,
        "timetabling/schedule.html",
        {"heading": "My teaching schedule", "entries": entries},
    )


@login_required
@school_roles_required(*TIMETABLE_VIEW_ROLES)
def class_schedule(request, stream_id):
    entries = (
        TimetableEntry.objects.for_school(request.school)
        .filter(stream_id=stream_id, timetable__status=Timetable.Status.PUBLISHED)
        .select_related(
            "period",
            "stream__grade",
            "learning_area",
            "teacher__membership__user",
            "room",
        )
    )
    if not entries.exists():
        raise Http404
    return render(
        request,
        "timetabling/schedule.html",
        {"heading": f"{entries.first().stream} schedule", "entries": entries},
    )
