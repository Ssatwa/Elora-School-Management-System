import factory
from django.contrib.auth import get_user_model

from apps.accounts.models import Membership, Role
from apps.tenancy.models import School, SchoolDomain


class SchoolFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = School
        skip_postgeneration_save = True

    name = factory.Sequence(lambda number: f"School {number}")
    slug = factory.Sequence(lambda number: f"school-{number}")

    @factory.post_generation
    def primary_domain(self, create, extracted, **kwargs):
        if create:
            SchoolDomainFactory(
                school=self,
                hostname=f"{self.slug}.localhost",
                is_primary=True,
            )


class SchoolDomainFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SchoolDomain

    school = factory.SubFactory(SchoolFactory, primary_domain=None)
    hostname = factory.Sequence(lambda number: f"school-{number}.localhost")
    is_primary = True


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Sequence(lambda number: f"user-{number}@example.test")

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return model_class.objects.create_user(*args, **kwargs)


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role

    code = factory.Sequence(lambda number: f"role-{number}")
    name = factory.LazyAttribute(lambda role: role.code.replace("-", " ").title())


class MembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Membership

    school = factory.SubFactory(SchoolFactory)
    user = factory.SubFactory(UserFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        role_code = kwargs.pop("role_code", "teacher")
        membership = super()._create(model_class, *args, **kwargs)
        role, _ = Role.objects.get_or_create(
            code=role_code,
            defaults={"name": role_code.replace("_", " ").title()},
        )
        membership.roles.add(role)
        return membership
