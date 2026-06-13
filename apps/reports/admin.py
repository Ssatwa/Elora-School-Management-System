from django.contrib import admin

from apps.reports.models import ReportCard, ReportGenerationJob

admin.site.register(ReportCard)
admin.site.register(ReportGenerationJob)
