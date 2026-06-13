from django.db import migrations


TENANT_TABLES = (
    "academics_academicyear",
    "academics_term",
    "academics_grade",
    "academics_stream",
    "academics_learningarea",
    "academics_strand",
    "academics_substrand",
    "academics_learningoutcome",
    "academics_competency",
    "academics_outcomecompetency",
    "staff_teacherprofile",
    "staff_department",
    "staff_staffassignment",
    "learners_learner",
    "learners_guardian",
    "learners_learnerguardian",
    "learners_medicalrecord",
    "learners_admissionapplication",
    "learners_admissionsequence",
    "learners_enrollment",
    "learners_transferrecord",
)


ENABLE_TEMPLATE = """
ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {table} FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS school_isolation ON {table};
CREATE POLICY school_isolation ON {table}
USING (
    school_id = NULLIF(current_setting('app.current_school', true), '')::uuid
)
WITH CHECK (
    school_id = NULLIF(current_setting('app.current_school', true), '')::uuid
);
"""

DISABLE_TEMPLATE = """
DROP POLICY IF EXISTS school_isolation ON {table};
ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;
ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;
"""


def enable_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    for table_name in TENANT_TABLES:
        table = schema_editor.quote_name(table_name)
        schema_editor.execute(ENABLE_TEMPLATE.format(table=table))


def disable_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    for table_name in reversed(TENANT_TABLES):
        table = schema_editor.quote_name(table_name)
        schema_editor.execute(DISABLE_TEMPLATE.format(table=table))


class Migration(migrations.Migration):
    dependencies = [
        ("academics", "0002_competency_learningarea_learningoutcome_and_more"),
        ("learners", "0004_learner_membership"),
        ("staff", "0001_initial"),
        ("tenancy", "0002_enable_rls"),
    ]

    operations = [
        migrations.RunPython(enable_rls, disable_rls),
    ]
