# Generated by Django 5.0.6 on 2024-08-20 20:10

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("obozstudentow", "0106_group_chat"),
    ]

    operations = [
        migrations.CreateModel(
            name="ZdjeciaKadra",
            fields=[],
            options={
                "verbose_name": "Zdjęcia Kadra",
                "verbose_name_plural": "Zdjęcia Kadra",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("obozstudentow.user",),
        ),
    ]
