# Generated by Django 5.0.4 on 2024-05-04 12:42

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("obozstudentow", "0095_tinderaction_tinderprofile"),
        ("obozstudentow_async", "0002_remove_message_group_name_chat_message_chat"),
    ]

    operations = [
        migrations.AddField(
            model_name="house",
            name="chat",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="obozstudentow_async.chat",
                verbose_name="Czat",
            ),
        ),
        migrations.AlterField(
            model_name="tinderaction",
            name="target",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tinderaction_target",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
