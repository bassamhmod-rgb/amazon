from django.db import migrations


def ensure_expense_tables(apps, schema_editor):
    # Use historical models so each backend gets its own valid SQL and indexes.
    existing = set(schema_editor.connection.introspection.table_names())
    for name in ("ExpenseReason", "ExpenseType", "Expense"):
        model = apps.get_model("dashboard", name)
        if model._meta.db_table not in existing:
            schema_editor.create_model(model)
            existing.add(model._meta.db_table)


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(ensure_expense_tables, migrations.RunPython.noop),
    ]
