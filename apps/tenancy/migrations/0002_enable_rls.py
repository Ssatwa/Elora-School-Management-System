from django.db import migrations


ENABLE_RLS = """
ALTER TABLE accounts_membership ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounts_membership FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS school_isolation ON accounts_membership;
CREATE POLICY school_isolation ON accounts_membership
USING (
    school_id = NULLIF(current_setting('app.current_school', true), '')::uuid
)
WITH CHECK (
    school_id = NULLIF(current_setting('app.current_school', true), '')::uuid
);
"""

DISABLE_RLS = """
DROP POLICY IF EXISTS school_isolation ON accounts_membership;
ALTER TABLE accounts_membership NO FORCE ROW LEVEL SECURITY;
ALTER TABLE accounts_membership DISABLE ROW LEVEL SECURITY;
"""


def enable_rls(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(ENABLE_RLS)


def disable_rls(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(DISABLE_RLS)


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_auditlog"),
        ("tenancy", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(enable_rls, disable_rls),
    ]
