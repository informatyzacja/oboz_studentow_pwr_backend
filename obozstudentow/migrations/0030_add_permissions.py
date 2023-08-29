

from django.db import migrations, models
from ..models import CustomPermissions

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import Group as DjangoGroup

from ..models import User

def create_groups(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ("obozstudentow", "0029_point_validated_point_validatedby_and_more"),
    ]

    operations = [
        migrations.RunPython(create_groups),
    ]
