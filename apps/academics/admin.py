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
    StreamLabel,
    SubStrand,
    Term,
)


@admin.register(AcademicYear, Term, Grade, Stream, StreamLabel, LearningArea, Competency)
class AcademicLookupAdmin(admin.ModelAdmin):
    list_filter = ("school",)
    search_fields = ("name",)


@admin.register(Strand, SubStrand, LearningOutcome)
class CurriculumAdmin(admin.ModelAdmin):
    list_filter = ("school",)
    search_fields = ("code",)


@admin.register(OutcomeCompetency)
class OutcomeCompetencyAdmin(admin.ModelAdmin):
    list_filter = ("school",)
    search_fields = ("outcome__code", "competency__code", "competency__name")
