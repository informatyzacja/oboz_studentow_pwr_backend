from django.db import migrations


def create_bingo_setting(apps, schema_editor):
    Setting = apps.get_model("obozstudentow", "Setting")
    Setting.objects.get_or_create(
        name="bingo_active",
        defaults={
            "value": "false",
            "description": "Czy moduł Bingo jest aktywny (true/false). Steruje widocznością przycisku w aplikacji.",
        },
    )


def remove_bingo_setting(apps, schema_editor):
    Setting = apps.get_model("obozstudentow", "Setting")
    Setting.objects.filter(name="bingo_active").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("obozstudentow", "0124_workshop_notifications_sent"),
    ]

    operations = [
        migrations.RunPython(create_bingo_setting, remove_bingo_setting),
    ]
