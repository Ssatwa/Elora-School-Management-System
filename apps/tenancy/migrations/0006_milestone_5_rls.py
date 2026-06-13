from django.db import migrations


TENANT_TABLES = (
    "finance_feestructure",
    "finance_invoice",
    "finance_payment",
    "finance_paymentallocation",
    "finance_receipt",
)

ENABLE_TEMPLATE = """
ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {table} FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS school_isolation ON {table};
CREATE POLICY school_isolation ON {table}
USING (school_id = NULLIF(current_setting('app.current_school', true), '')::uuid)
WITH CHECK (school_id = NULLIF(current_setting('app.current_school', true), '')::uuid);
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
        schema_editor.execute(
            ENABLE_TEMPLATE.format(table=schema_editor.quote_name(table_name))
        )


def disable_rls(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    for table_name in reversed(TENANT_TABLES):
        schema_editor.execute(
            DISABLE_TEMPLATE.format(table=schema_editor.quote_name(table_name))
        )


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0001_initial"),
        ("tenancy", "0005_milestone_4_rls"),
    ]

    operations = [migrations.RunPython(enable_rls, disable_rls)]
