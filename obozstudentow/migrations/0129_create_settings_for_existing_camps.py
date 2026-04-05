"""
Data migration: create CampSettings for any existing camps that don't have one yet.
"""
from django.db import migrations


def create_settings_for_existing_camps(apps, schema_editor):
    Camp = apps.get_model("obozstudentow", "Camp")
    CampSettings = apps.get_model("obozstudentow", "CampSettings")
    for camp in Camp.objects.all():
        CampSettings.objects.get_or_create(camp=camp)


class Migration(migrations.Migration):
    dependencies = [
        ("obozstudentow", "0128_campsettings"),
    ]

    operations = [
        migrations.RunPython(
            create_settings_for_existing_camps,
            migrations.RunPython.noop,
        ),
    ]
