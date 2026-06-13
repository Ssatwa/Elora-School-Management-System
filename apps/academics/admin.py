from django.contrib import admin

from apps.academics.models import (
    AcademicYear,
    Competency,
    Grade,
    LearningArea,
    LearningOutcome,
    OutcomeCompetency,
    Strand,
    Stream,
    SubStrand,
    Term,
)


@admin.register(AcademicYear, Term, Grade, Stream, LearningArea, Competency)
class AcademicLookupAdmin(admin.ModelAdmin):
    list_filter = ("school",)
    search_fields = ("name",)


@admin.register(Strand, SubStrand, LearningOutcome, OutcomeCompetency)
class CurriculumAdmin(admin.ModelAdmin):
    list_filter = ("school",)
    search_fields = ("code",)
