from django.contrib import admin

from apps.learning.models import Assignment, Resource, Submission

admin.site.register(Assignment)
admin.site.register(Submission)
admin.site.register(Resource)
