from django.contrib import admin

from apps.assessments.models import (
    Assessment,
    AssessmentResult,
    AssessmentWorkflowEvent,
    CriterionRating,
    Evidence,
    RatingLevel,
    Rubric,
    RubricCriterion,
)

admin.site.register(RatingLevel)
admin.site.register(Rubric)
admin.site.register(RubricCriterion)
admin.site.register(Assessment)
admin.site.register(AssessmentResult)
admin.site.register(CriterionRating)
admin.site.register(Evidence)
admin.site.register(AssessmentWorkflowEvent)
