# Generated by Django 4.2.2 on 2023-08-19 12:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("obozstudentow", "0045_user_birthdate"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="freenow_code",
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
