# Generated by Django 4.2.2 on 2023-08-25 21:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("obozstudentow", "0059_alter_user_bandid"),
    ]

    operations = [
        migrations.CreateModel(
            name="HouseCollocationForImport",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=10)),
                (
                    "bandId",
                    models.CharField(blank=True, max_length=6, null=True, unique=True),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="user",
            name="bandId",
            field=models.CharField(blank=True, max_length=6, null=True, unique=True),
        ),
    ]
