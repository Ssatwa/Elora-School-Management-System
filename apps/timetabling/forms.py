from typing import cast

from django import forms

from apps.academics.models import AcademicYear, LearningArea, Stream, Term
from apps.staff.models import TeacherProfile
from apps.timetabling.models import Room, Timetable, TimetableEntry, TimetablePeriod


class SchoolScopedModelForm(forms.ModelForm):
    def __init__(self, *args, school, **kwargs):
        self.school = school
        super().__init__(*args, **kwargs)
        self.instance.school = school

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.school = self.school
        if commit:
            instance.full_clean()
            instance.save()
            self.save_m2m()
        return instance


class TimetableForm(SchoolScopedModelForm):
    class Meta:
        model = Timetable
        fields = ("academic_year", "term", "name")

    def __init__(self, *args, school, **kwargs):
        super().__init__(*args, school=school, **kwargs)
        year_field = cast(forms.ModelChoiceField, self.fields["academic_year"])
        term_field = cast(forms.ModelChoiceField, self.fields["term"])
        year_field.queryset = AcademicYear.objects.for_school(school)
        term_field.queryset = Term.objects.for_school(school).select_related("academic_year")

    def clean(self):
        cleaned = super().clean() or {}
        year = cleaned.get("academic_year")
        term = cleaned.get("term")
        if year and term and term.academic_year_id != year.id:
            self.add_error("term", "Term must belong to the selected academic year.")
        return cleaned


class TimetableEntryForm(forms.ModelForm):
    class Meta:
        model = TimetableEntry
        fields = ("period", "stream", "learning_area", "teacher", "room")

    def __init__(self, *args, school, timetable=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.school = school
        if timetable is not None:
            self.instance.timetable = timetable
        period_field = cast(forms.ModelChoiceField, self.fields["period"])
        stream_field = cast(forms.ModelChoiceField, self.fields["stream"])
        area_field = cast(forms.ModelChoiceField, self.fields["learning_area"])
        teacher_field = cast(forms.ModelChoiceField, self.fields["teacher"])
        room_field = cast(forms.ModelChoiceField, self.fields["room"])
        period_field.queryset = TimetablePeriod.objects.for_school(school).filter(
            is_break=False
        )
        stream_field.queryset = Stream.objects.for_school(school).filter(is_active=True)
        area_field.queryset = LearningArea.objects.for_school(school).filter(is_active=True)
        teacher_field.queryset = TeacherProfile.objects.for_school(school).filter(
            status=TeacherProfile.Status.ACTIVE
        )
        room_field.queryset = Room.objects.for_school(school).filter(is_active=True)


class RoomForm(SchoolScopedModelForm):
    class Meta:
        model = Room
        fields = ("code", "name", "capacity", "is_active")


class TimetablePeriodForm(SchoolScopedModelForm):
    class Meta:
        model = TimetablePeriod
        fields = (
            "weekday",
            "sequence",
            "name",
            "start_time",
            "end_time",
            "is_break",
        )
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }
