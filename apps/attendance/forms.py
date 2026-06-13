from typing import cast

from django import forms

from apps.academics.models import Stream
from apps.attendance.models import AttendanceRegister, LearnerAttendanceEntry


class LearnerRegisterForm(forms.Form):
    attendance_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    session = forms.ChoiceField(choices=AttendanceRegister.Session.choices)
    stream = forms.ModelChoiceField(queryset=Stream.objects.none())

    def __init__(self, *args, school, **kwargs):
        super().__init__(*args, **kwargs)
        stream_field = cast(forms.ModelChoiceField, self.fields["stream"])
        stream_field.queryset = (
            Stream.objects.for_school(school)
            .filter(is_active=True)
            .select_related("grade")
        )


class StaffRegisterForm(forms.Form):
    attendance_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    session = forms.ChoiceField(choices=AttendanceRegister.Session.choices)


class AttendanceCorrectionForm(forms.Form):
    status = forms.ChoiceField(choices=LearnerAttendanceEntry.Status.choices)
    arrival_time = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={"type": "time"}),
    )
    note = forms.CharField(max_length=250, required=False, widget=forms.Textarea)
    reason = forms.CharField(widget=forms.Textarea)


class AttendanceReportForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    subject_type = forms.ChoiceField(
        choices=AttendanceRegister.SubjectType.choices,
        required=False,
    )

    def clean(self):
        cleaned = super().clean() or {}
        if (
            cleaned.get("start_date")
            and cleaned.get("end_date")
            and cleaned["end_date"] < cleaned["start_date"]
        ):
            self.add_error("end_date", "End date must follow start date.")
        return cleaned
