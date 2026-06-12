import pytest

from apps.tenancy.models import School
from apps.tenancy.tasks import school_task


@pytest.mark.django_db
def test_school_task_requires_existing_active_school():
    school = School.objects.create(name="Green Hills", slug="green-hills")

    assert school_task.run(str(school.id)) == {"school_id": str(school.id)}


@pytest.mark.django_db
def test_school_task_rejects_inactive_school():
    school = School.objects.create(
        name="Closed School",
        slug="closed-school",
        is_active=False,
    )

    with pytest.raises(School.DoesNotExist):
        school_task.run(str(school.id))
