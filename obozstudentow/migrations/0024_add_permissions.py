

from django.db import migrations, models
from ..models import CustomPermissions

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import Group as DjangoGroup

def create_groups(apps, schema_editor):

    bajer_group, created = DjangoGroup.objects.get_or_create(name="Bajer")
    kadra_group, created = DjangoGroup.objects.get_or_create(name="Kadra")
    sztab_group, created = DjangoGroup.objects.get_or_create(name="Sztab")

    content_type = ContentType.objects.get_for_model(CustomPermissions)

    # bajer
    for permission in [
            ('can_view_fractions', 'Can view fractions'),
            ('can_view_groups', 'Can view groups'),
        ]:
        permission, created = Permission.objects.get_or_create( codename=permission[0], name=permission[1], content_type=content_type )
        for group in [bajer_group, kadra_group, sztab_group]:
            group.permissions.add(permission)

    #kadra
    for permission in []:
        permission, created = Permission.objects.get_or_create( codename=permission[0], name=permission[1], content_type=content_type )
        for group in [kadra_group, sztab_group]:
            group.permissions.add(permission)

    #sztab
    for permission in []:
        permission, created = Permission.objects.get_or_create( codename=permission[0], name=permission[1], content_type=content_type )
        sztab_group.permissions.add(permission)

class Migration(migrations.Migration):

    dependencies = [
        ("obozstudentow", "0023_image"),
    ]

    operations = [
        migrations.RunPython(create_groups),
    ]
