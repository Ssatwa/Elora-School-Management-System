from django.contrib import admin

from apps.communication.models import Announcement, Message, Notification

admin.site.register(Announcement)
admin.site.register(Notification)
admin.site.register(Message)
