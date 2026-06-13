from django.contrib import admin

from apps.timetabling.models import Room, Timetable, TimetableEntry, TimetablePeriod

admin.site.register(Room)
admin.site.register(TimetablePeriod)
admin.site.register(Timetable)
admin.site.register(TimetableEntry)
