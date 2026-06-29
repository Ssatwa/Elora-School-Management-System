from django import forms

from apps.academics.models import (
    AcademicYear,
    Competency,
    Grade,
    LearningArea,
    StreamLabel,
)


class SchoolScopedModelForm(forms.ModelForm):
    def __init__(self, *args, school, **kwargs):
        self.school = school
        super().__init__(*args, **kwargs)
        has_school_field = any(field.name == "school" for field in self.instance._meta.fields)
        if has_school_field and not self.instance.school_id:
            self.instance.school = school

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.school = self.school
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class AcademicYearForm(SchoolScopedModelForm):
    class Meta:
        model = AcademicYear
        fields = ("name", "start_date", "end_date", "status")
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class GradeForm(SchoolScopedModelForm):
    class Meta:
        model = Grade
        fields = ("code", "name", "education_level", "order", "is_active")


class StreamLabelForm(SchoolScopedModelForm):
    class Meta:
        model = StreamLabel
        fields = ("code", "name", "is_active")


class LearningAreaForm(SchoolScopedModelForm):
    class Meta:
        model = LearningArea
        fields = ("code", "name", "is_active")


class CompetencyForm(SchoolScopedModelForm):
    class Meta:
        model = Competency
        fields = ("code", "name", "description", "is_active")
