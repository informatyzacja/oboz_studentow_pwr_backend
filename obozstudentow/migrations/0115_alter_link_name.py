# Generated by Django 5.0.6 on 2024-08-23 19:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("obozstudentow", "0114_alter_bus_location"),
    ]

    operations = [
        migrations.AlterField(
            model_name="link",
            name="name",
            field=models.CharField(
                help_text="Nazwa linku (nie widoczna dla użytkownika)", max_length=100
            ),
        ),
    ]
