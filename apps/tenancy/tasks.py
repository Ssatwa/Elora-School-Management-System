from celery import shared_task

from apps.tenancy.models import School


@shared_task
def school_task(school_id):
    school = School.objects.get(pk=school_id, is_active=True)
    return {"school_id": str(school.id)}
