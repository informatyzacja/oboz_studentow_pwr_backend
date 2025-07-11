from django.db import migrations, models
from ..models import CustomPermissions

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from django.contrib.auth.models import Group as DjangoGroup

from ..models import User


def create_groups(apps, schema_editor):
    bajer_group, created = DjangoGroup.objects.get_or_create(name="Bajer")
    kadra_group, created = DjangoGroup.objects.get_or_create(name="Kadra")
    sztab_group, created = DjangoGroup.objects.get_or_create(name="Sztab")
    ratownicy_group, created = DjangoGroup.objects.get_or_create(name="Ratownicy")

    content_type = ContentType.objects.get_for_model(CustomPermissions)

    # bajer
    for permission in []:
        permission, created = Permission.objects.get_or_create(
            codename=permission[0], name=permission[1], content_type=content_type
        )
        for group in [bajer_group, kadra_group, sztab_group]:
            group.permissions.add(permission)

    # kadra
    for permission in []:
        permission, created = Permission.objects.get_or_create(
            codename=permission[0], name=permission[1], content_type=content_type
        )
        for group in [kadra_group, sztab_group]:
            group.permissions.add(permission)

    # sztab
    for permission in []:
        permission, created = Permission.objects.get_or_create(
            codename=permission[0], name=permission[1], content_type=content_type
        )
        sztab_group.permissions.add(permission)

    # ratownicy
    for permission in []:
        permission, created = Permission.objects.get_or_create(
            codename=permission[0], name=permission[1], content_type=content_type
        )
        ratownicy_group.permissions.add(permission)

    # superuser
    for permission in [
        ("can_change_bands", "Can change bands"),
    ]:
        permission, created = Permission.objects.get_or_create(
            codename=permission[0], name=permission[1], content_type=content_type
        )
        for superuser in User.objects.filter(is_superuser=True):
            superuser.user_permissions.add(permission)

    for permission in [
        ("can_change_bands", "Can change bands"),
    ]:
        permission, created = Permission.objects.get_or_create(
            codename=permission[0], name=permission[1], content_type=content_type
        )
        group, created = DjangoGroup.objects.get_or_create(name="Sztab: Uczestnicy")
        group.permissions.add(permission)


class Migration(migrations.Migration):
    dependencies = [
        ("obozstudentow", "0119_alter_partners_options_mealduty"),
    ]

    operations = [
        migrations.RunPython(create_groups),
    ]
