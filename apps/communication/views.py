from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.communication.models import Announcement, Message, Notification


@login_required
def index(request):
    return render(
        request,
        "communication/index.html",
        {
            "announcements": Announcement.objects.for_school(request.school)[:10],
            "notifications": Notification.objects.for_school(request.school).filter(
                user=request.user
            )[:10],
            "messages": Message.objects.for_school(request.school).filter(
                recipient=request.user
            )[:10],
        },
    )
