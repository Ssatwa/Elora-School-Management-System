from typing import cast

from django import forms

from apps.academics.models import AcademicYear, Grade, Stream
from apps.learners.models import Learner, LearnerGuardian


class AdmissionForm(forms.Form):
    first_name = forms.CharField(max_length=80)
    middle_name = forms.CharField(max_length=80, required=False)
    last_name = forms.CharField(max_length=80)
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    gender = forms.ChoiceField(choices=Learner.Gender.choices)
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.none())
    grade = forms.ModelChoiceField(queryset=Grade.objects.none())
    stream = forms.ModelChoiceField(queryset=Stream.objects.none())
    admission_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    guardian_first_name = forms.CharField(max_length=80)
    guardian_last_name = forms.CharField(max_length=80)
    guardian_email = forms.EmailField(required=False)
    guardian_phone_number = forms.CharField(max_length=32)
    guardian_relationship = forms.ChoiceField(choices=LearnerGuardian.Relationship.choices)
    blood_group = forms.CharField(max_length=8, required=False)
    allergies = forms.CharField(widget=forms.Textarea, required=False)
    conditions = forms.CharField(widget=forms.Textarea, required=False)
    medication = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, school, **kwargs):
        super().__init__(*args, **kwargs)
        academic_year_field = cast(
            forms.ModelChoiceField,
            self.fields["academic_year"],
        )
        grade_field = cast(forms.ModelChoiceField, self.fields["grade"])
        stream_field = cast(forms.ModelChoiceField, self.fields["stream"])
        academic_year_field.queryset = AcademicYear.objects.for_school(school)
        grade_field.queryset = Grade.objects.for_school(school).filter(is_active=True)
        stream_field.queryset = Stream.objects.for_school(school).filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean() or {}
        grade = cleaned_data.get("grade")
        stream = cleaned_data.get("stream")
        if grade and stream and stream.grade_id != grade.id:
            self.add_error("stream", "Stream must belong to the selected grade.")
        return cleaned_data


class TransferForm(forms.Form):
    destination_school_name = forms.CharField(max_length=200)
    transfer_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    reason = forms.CharField(widget=forms.Textarea)
    export_reference = forms.CharField(max_length=80, required=False)
