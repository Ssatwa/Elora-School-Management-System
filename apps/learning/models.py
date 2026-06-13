from django.db import models

from apps.core.models import TimeStampedModel, UUIDModel
from apps.tenancy.managers import TenantManager


class Assignment(UUIDModel, TimeStampedModel):
    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    teacher = models.ForeignKey("staff.TeacherProfile", on_delete=models.PROTECT)
    term = models.ForeignKey("academics.Term", on_delete=models.PROTECT)
    stream = models.ForeignKey("academics.Stream", on_delete=models.PROTECT)
    learning_area = models.ForeignKey("academics.LearningArea", on_delete=models.PROTECT)
    title = models.CharField(max_length=180)
    instructions = models.TextField()
    due_at = models.DateTimeField()
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-published_at", "due_at"]
        indexes = [models.Index(fields=["school", "stream", "is_published"])]

    def __str__(self):
        return self.title


class Submission(UUIDModel, TimeStampedModel):
    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.PROTECT, related_name="submissions")
    learner = models.ForeignKey("learners.Learner", on_delete=models.PROTECT)
    response = models.TextField(blank=True)
    file = models.FileField(upload_to="submissions/%Y/%m/", blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    feedback = models.TextField(blank=True)

    objects = TenantManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["school", "assignment", "learner"],
                name="unique_assignment_submission",
            )
        ]


class Resource(UUIDModel, TimeStampedModel):
    class Kind(models.TextChoices):
        NOTE = "note", "Note"
        FILE = "file", "File"
        VIDEO = "video", "Video"

    school = models.ForeignKey("tenancy.School", on_delete=models.CASCADE)
    teacher = models.ForeignKey("staff.TeacherProfile", on_delete=models.PROTECT)
    learning_area = models.ForeignKey("academics.LearningArea", on_delete=models.PROTECT)
    title = models.CharField(max_length=180)
    kind = models.CharField(max_length=12, choices=Kind.choices)
    content = models.TextField(blank=True)
    url = models.URLField(blank=True)
    file = models.FileField(upload_to="resources/%Y/%m/", blank=True)
    is_published = models.BooleanField(default=True)

    objects = TenantManager()

    def __str__(self):
        return self.title
