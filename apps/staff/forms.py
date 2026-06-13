from typing import cast

from django import forms

from apps.academics.models import Grade, LearningArea, Stream
from apps.accounts.models import Membership
from apps.staff.models import Department, StaffAssignment, TeacherProfile


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


class TeacherProfileForm(SchoolScopedModelForm):
    class Meta:
        model = TeacherProfile
        fields = (
            "membership",
            "employee_number",
            "tsc_number",
            "phone_number",
            "employment_date",
            "status",
        )
        widgets = {"employment_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, school, **kwargs):
        super().__init__(*args, school=school, **kwargs)
        membership_field = cast(forms.ModelChoiceField, self.fields["membership"])
        membership_field.queryset = (
            Membership.objects.for_school(school)
            .filter(
                is_active=True,
                roles__code__in=("teacher", "class_teacher", "department_head"),
            )
            .select_related("user")
            .distinct()
        )


class DepartmentForm(SchoolScopedModelForm):
    class Meta:
        model = Department
        fields = ("code", "name", "head", "is_active")

    def __init__(self, *args, school, **kwargs):
        super().__init__(*args, school=school, **kwargs)
        head_field = cast(forms.ModelChoiceField, self.fields["head"])
        head_field.queryset = TeacherProfile.objects.for_school(school).filter(
            status=TeacherProfile.Status.ACTIVE
        )


class StaffAssignmentForm(SchoolScopedModelForm):
    class Meta:
        model = StaffAssignment
        fields = (
            "teacher",
            "department",
            "learning_area",
            "grade",
            "stream",
            "role",
            "start_date",
            "end_date",
            "weekly_lessons",
        )
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, school, **kwargs):
        super().__init__(*args, school=school, **kwargs)
        teacher_field = cast(forms.ModelChoiceField, self.fields["teacher"])
        department_field = cast(forms.ModelChoiceField, self.fields["department"])
        learning_area_field = cast(forms.ModelChoiceField, self.fields["learning_area"])
        grade_field = cast(forms.ModelChoiceField, self.fields["grade"])
        stream_field = cast(forms.ModelChoiceField, self.fields["stream"])
        teacher_field.queryset = TeacherProfile.objects.for_school(school)
        department_field.queryset = Department.objects.for_school(school)
        learning_area_field.queryset = LearningArea.objects.for_school(school)
        grade_field.queryset = Grade.objects.for_school(school)
        stream_field.queryset = Stream.objects.for_school(school)
