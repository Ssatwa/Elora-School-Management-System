from typing import cast

from django import forms

from apps.academics.models import (
    AcademicYear,
    Competency,
    Grade,
    LearningArea,
    Stream,
)


class SchoolScopedModelForm(forms.ModelForm):
    def __init__(self, *args, school, **kwargs):
        self.school = school
        super().__init__(*args, **kwargs)

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


class StreamForm(SchoolScopedModelForm):
    class Meta:
        model = Stream
        fields = ("grade", "code", "name", "is_active")

    def __init__(self, *args, school, **kwargs):
        super().__init__(*args, school=school, **kwargs)
        grade_field = cast(forms.ModelChoiceField, self.fields["grade"])
        grade_field.queryset = Grade.objects.for_school(school).filter(is_active=True)


class LearningAreaForm(SchoolScopedModelForm):
    class Meta:
        model = LearningArea
        fields = ("code", "name", "is_active")


class CompetencyForm(SchoolScopedModelForm):
    class Meta:
        model = Competency
        fields = ("code", "name", "description", "is_active")
