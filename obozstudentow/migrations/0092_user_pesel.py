# Generated by Django 5.0.3 on 2024-04-30 17:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("obozstudentow", "0091_user_additional_health_info_user_ice_number_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="pesel",
            field=models.CharField(blank=True, max_length=11, null=True),
        ),
    ]
