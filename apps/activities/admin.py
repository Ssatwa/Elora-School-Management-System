from django.contrib import admin

from apps.activities.models import ActivityParticipation, Club

admin.site.register(Club)
admin.site.register(ActivityParticipation)
