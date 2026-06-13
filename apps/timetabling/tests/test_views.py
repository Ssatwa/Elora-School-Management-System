import pytest
from django.urls import reverse

from apps.academics.models import LearningArea
from apps.attendance.tests.test_models import make_stream, make_teacher
from apps.timetabling.models import Room, Timetable
from apps.timetabling.tests.test_models import make_calendar, make_period
from tests.factories import MembershipFactory, SchoolFactory

pytestmark = pytest.mark.django_db


def login(client, school, role_code):
    membership = MembershipFactory(school=school, role_code=role_code)
    client.force_login(membership.user)
    return membership


def test_school_admin_can_create_timetable_add_entry_and_publish(client):
    school = SchoolFactory()
    login(client, school, "school_admin")
    year, term = make_calendar(school)

    created = client.post(
        reverse("timetabling:create-timetable"),
        {
            "academic_year": str(year.id),
            "term": str(term.id),
            "name": "Term 2 master",
        },
        HTTP_HOST=f"{school.slug}.localhost",
    )
    timetable = Timetable.objects.for_school(school).get()
    assert created.status_code == 302

    period = make_period(school)
    stream = make_stream(school)
    area = LearningArea.objects.create(school=school, code="math", name="Mathematics")
    teacher = make_teacher(school)
    room = Room.objects.create(school=school, code="R1", name="Room 1", capacity=40)
    added = client.post(
        reverse("timetabling:add-entry", kwargs={"timetable_id": timetable.id}),
        {
            "period": str(period.id),
            "stream": str(stream.id),
            "learning_area": str(area.id),
            "teacher": str(teacher.id),
            "room": str(room.id),
        },
        HTTP_HOST=f"{school.slug}.localhost",
    )
    assert added.status_code == 302
    assert timetable.entries.count() == 1

    published = client.post(
        reverse("timetabling:publish", kwargs={"timetable_id": timetable.id}),
        HTTP_HOST=f"{school.slug}.localhost",
    )
    timetable.refresh_from_db()
    assert published.status_code == 302
    assert timetable.status == Timetable.Status.PUBLISHED


def test_timetable_entry_conflict_is_rendered_without_creating_second_entry(client):
    school = SchoolFactory()
    login(client, school, "principal")
    year, term = make_calendar(school)
    timetable = Timetable.objects.create(
        school=school,
        academic_year=year,
        term=term,
        name="Term 2 master",
    )
    period = make_period(school)
    first_stream = make_stream(school)
    second_stream = make_stream(school, "-b")
    area = LearningArea.objects.create(school=school, code="math", name="Mathematics")
    teacher = make_teacher(school)
    room = Room.objects.create(school=school, code="R1", name="Room 1", capacity=40)
    url = reverse("timetabling:add-entry", kwargs={"timetable_id": timetable.id})
    values = {
        "period": str(period.id),
        "stream": str(first_stream.id),
        "learning_area": str(area.id),
        "teacher": str(teacher.id),
        "room": str(room.id),
    }
    client.post(url, values, HTTP_HOST=f"{school.slug}.localhost")
    values["stream"] = str(second_stream.id)
    response = client.post(url, values, HTTP_HOST=f"{school.slug}.localhost")

    assert response.status_code == 400
    assert "Teacher conflict" in response.content.decode()
    assert timetable.entries.count() == 1


def test_teacher_schedule_only_lists_own_published_lessons(client):
    school = SchoolFactory()
    teacher_membership = login(client, school, "teacher")
    year, term = make_calendar(school)
    timetable = Timetable.objects.create(
        school=school,
        academic_year=year,
        term=term,
        name="Term 2 master",
        status=Timetable.Status.PUBLISHED,
    )
    own_teacher = make_teacher(school)
    own_teacher.membership = teacher_membership
    own_teacher.employee_number = "T-OWN"
    own_teacher.save(update_fields=["membership", "employee_number"])
    other_teacher = make_teacher(school, "T-OTHER")
    period = make_period(school)
    first_stream = make_stream(school)
    second_stream = make_stream(school, "-b")
    own_area = LearningArea.objects.create(school=school, code="math", name="Mathematics")
    other_area = LearningArea.objects.create(school=school, code="eng", name="English")
    first_room = Room.objects.create(school=school, code="R1", name="Room 1", capacity=40)
    second_room = Room.objects.create(school=school, code="R2", name="Room 2", capacity=40)
    timetable.entries.create(
        school=school,
        period=period,
        stream=first_stream,
        learning_area=own_area,
        teacher=own_teacher,
        room=first_room,
    )
    timetable.entries.create(
        school=school,
        period=make_period(school, 2),
        stream=second_stream,
        learning_area=other_area,
        teacher=other_teacher,
        room=second_room,
    )

    response = client.get(
        reverse("timetabling:my-schedule"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    content = response.content.decode()
    assert response.status_code == 200
    assert "Mathematics" in content
    assert "English" not in content


def test_parent_cannot_open_timetable_administration(client):
    school = SchoolFactory()
    login(client, school, "parent")

    response = client.get(
        reverse("timetabling:index"),
        HTTP_HOST=f"{school.slug}.localhost",
    )

    assert response.status_code == 403
