from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel
from apps.tenancy.managers import TenantManager


class RatingLevel(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="rating_levels",
    )
    code = models.SlugField(max_length=16)
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    rank = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-rank", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "code"],
                name="unique_rating_code_per_school",
            ),
            models.UniqueConstraint(
                fields=["school", "rank"],
                name="unique_rating_rank_per_school",
            ),
        ]
        indexes = [models.Index(fields=["school", "is_active", "rank"])]

    def __str__(self):
        return self.name


class Rubric(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="rubrics",
    )
    name = models.CharField(max_length=160)
    learning_area = models.ForeignKey(
        "academics.LearningArea",
        on_delete=models.PROTECT,
        related_name="rubrics",
    )
    grade = models.ForeignKey(
        "academics.Grade",
        on_delete=models.PROTECT,
        related_name="rubrics",
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        ordering = ["learning_area__name", "grade__order", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "learning_area", "grade", "name"],
                name="unique_named_rubric_per_area_grade",
            )
        ]
        indexes = [models.Index(fields=["school", "learning_area", "grade"])]

    def clean(self):
        super().clean()
        errors = {}
        for field_name in ("learning_area", "grade"):
            related_id = getattr(self, f"{field_name}_id")
            if related_id and getattr(self, field_name).school_id != self.school_id:
                errors[field_name] = (
                    f"{field_name.replace('_', ' ').title()} must belong to the same school."
                )
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name


class RubricCriterion(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="rubric_criteria",
    )
    rubric = models.ForeignKey(
        Rubric,
        on_delete=models.CASCADE,
        related_name="criteria",
    )
    outcome = models.ForeignKey(
        "academics.LearningOutcome",
        on_delete=models.PROTECT,
        related_name="rubric_criteria",
    )
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    sequence = models.PositiveSmallIntegerField()

    objects = TenantManager()

    class Meta:
        ordering = ["rubric", "sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "rubric", "sequence"],
                name="unique_criterion_sequence_per_rubric",
            ),
            models.UniqueConstraint(
                fields=["school", "rubric", "outcome"],
                name="unique_outcome_per_rubric",
            ),
        ]
        indexes = [models.Index(fields=["school", "rubric", "sequence"])]

    def clean(self):
        super().clean()
        errors = {}
        if self.rubric_id and self.rubric.school_id != self.school_id:
            errors["rubric"] = "Rubric must belong to the same school."
        if self.outcome_id and self.outcome.school_id != self.school_id:
            errors["outcome"] = "Learning outcome must belong to the same school."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.name


class Assessment(UUIDModel, TimeStampedModel):
    class AssessmentType(models.TextChoices):
        FORMATIVE = "formative", "Formative"
        SUMMATIVE = "summative", "Summative"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        SUBMITTED = "submitted", "Submitted for moderation"
        MODERATED = "moderated", "Moderated"
        APPROVED = "approved", "Approved"
        PUBLISHED = "published", "Published"

    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    term = models.ForeignKey(
        "academics.Term",
        on_delete=models.PROTECT,
        related_name="assessments",
    )
    stream = models.ForeignKey(
        "academics.Stream",
        on_delete=models.PROTECT,
        related_name="assessments",
    )
    learning_area = models.ForeignKey(
        "academics.LearningArea",
        on_delete=models.PROTECT,
        related_name="assessments",
    )
    teacher = models.ForeignKey(
        "staff.TeacherProfile",
        on_delete=models.PROTECT,
        related_name="assessments",
    )
    rubric = models.ForeignKey(
        Rubric,
        on_delete=models.PROTECT,
        related_name="assessments",
    )
    title = models.CharField(max_length=180)
    assessment_type = models.CharField(max_length=16, choices=AssessmentType.choices)
    assessment_date = models.DateField()
    instructions = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    moderated_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-assessment_date", "title"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "term", "stream", "learning_area", "title"],
                name="unique_named_assessment_per_class_term",
            )
        ]
        indexes = [
            models.Index(fields=["school", "status", "assessment_date"]),
            models.Index(fields=["school", "term", "stream", "learning_area"]),
        ]

    def clean(self):
        super().clean()
        errors = {}
        for field_name in (
            "term",
            "stream",
            "learning_area",
            "teacher",
            "rubric",
        ):
            related_id = getattr(self, f"{field_name}_id")
            if related_id and getattr(self, field_name).school_id != self.school_id:
                errors[field_name] = (
                    f"{field_name.replace('_', ' ').title()} must belong to the same school."
                )
        if self.rubric_id and self.learning_area_id:
            if self.rubric.learning_area_id != self.learning_area_id:
                errors["rubric"] = "Rubric must match the selected learning area."
        if self.rubric_id and self.stream_id:
            if self.rubric.grade_id != self.stream.grade_id:
                errors["rubric"] = "Rubric grade must match the selected stream."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title


class AssessmentResult(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="assessment_results",
    )
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.PROTECT,
        related_name="results",
    )
    learner = models.ForeignKey(
        "learners.Learner",
        on_delete=models.PROTECT,
        related_name="assessment_results",
    )
    overall_rating = models.ForeignKey(
        RatingLevel,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="overall_results",
    )
    teacher_comment = models.TextField(blank=True)
    moderated_comment = models.TextField(blank=True)
    is_complete = models.BooleanField(default=False)

    objects = TenantManager()

    class Meta:
        ordering = ["learner__last_name", "learner__first_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "assessment", "learner"],
                name="unique_assessment_result_per_learner",
            )
        ]
        indexes = [
            models.Index(fields=["school", "assessment", "is_complete"]),
            models.Index(fields=["school", "learner"]),
        ]

    def clean(self):
        super().clean()
        errors = {}
        for field_name in ("assessment", "learner", "overall_rating"):
            related_id = getattr(self, f"{field_name}_id")
            if related_id and getattr(self, field_name).school_id != self.school_id:
                errors[field_name] = (
                    f"{field_name.replace('_', ' ').title()} must belong to the same school."
                )
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.assessment} - {self.learner}"


class CriterionRating(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="criterion_ratings",
    )
    result = models.ForeignKey(
        AssessmentResult,
        on_delete=models.CASCADE,
        related_name="criterion_ratings",
    )
    criterion = models.ForeignKey(
        RubricCriterion,
        on_delete=models.PROTECT,
        related_name="ratings",
    )
    rating = models.ForeignKey(
        RatingLevel,
        on_delete=models.PROTECT,
        related_name="criterion_ratings",
    )
    comment = models.CharField(max_length=250, blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ["criterion__sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "result", "criterion"],
                name="unique_criterion_rating_per_result",
            )
        ]
        indexes = [models.Index(fields=["school", "result", "criterion"])]

    def clean(self):
        super().clean()
        errors = {}
        for field_name in ("result", "criterion", "rating"):
            related_id = getattr(self, f"{field_name}_id")
            if related_id and getattr(self, field_name).school_id != self.school_id:
                errors[field_name] = (
                    f"{field_name.replace('_', ' ').title()} must belong to the same school."
                )
        if self.result_id and self.criterion_id:
            if self.result.assessment.rubric_id != self.criterion.rubric_id:
                errors["criterion"] = "Criterion must belong to the assessment rubric."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.result} - {self.criterion}"


class Evidence(UUIDModel, TimeStampedModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="assessment_evidence",
    )
    result = models.ForeignKey(
        AssessmentResult,
        on_delete=models.PROTECT,
        related_name="evidence",
    )
    learner = models.ForeignKey(
        "learners.Learner",
        on_delete=models.PROTECT,
        related_name="portfolio_evidence",
    )
    outcome = models.ForeignKey(
        "academics.LearningOutcome",
        on_delete=models.PROTECT,
        related_name="assessment_evidence",
    )
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="assessment-evidence/%Y/%m/", blank=True)
    file_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120)
    size_bytes = models.PositiveIntegerField()
    captured_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-captured_at"]
        indexes = [
            models.Index(fields=["school", "learner", "captured_at"]),
            models.Index(fields=["school", "result"]),
        ]

    def clean(self):
        super().clean()
        errors = {}
        for field_name in ("result", "learner", "outcome"):
            related_id = getattr(self, f"{field_name}_id")
            if related_id and getattr(self, field_name).school_id != self.school_id:
                errors[field_name] = (
                    f"{field_name.replace('_', ' ').title()} must belong to the same school."
                )
        if self.result_id and self.learner_id and self.result.learner_id != self.learner_id:
            errors["learner"] = "Evidence learner must match the result learner."
        if self.size_bytes > 10 * 1024 * 1024:
            errors["size_bytes"] = "Evidence files may not exceed 10 MB."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title


class AssessmentWorkflowEvent(UUIDModel):
    school = models.ForeignKey(
        "tenancy.School",
        on_delete=models.CASCADE,
        related_name="assessment_workflow_events",
    )
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.PROTECT,
        related_name="workflow_events",
    )
    actor = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="assessment_workflow_events",
    )
    action = models.CharField(max_length=40)
    from_status = models.CharField(max_length=16)
    to_status = models.CharField(max_length=16)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["school", "assessment", "created_at"])]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Assessment workflow history is immutable.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.assessment}: {self.action}"
