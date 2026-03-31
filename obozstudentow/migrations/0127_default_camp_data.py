"""
Data migration: create a default "legacy" camp and assign all existing records to it.
All existing users get the MEMBER role; staff (is_staff=True) get the OWNER role.
"""
from django.db import migrations


def create_default_camp(apps, schema_editor):
    Camp = apps.get_model("obozstudentow", "Camp")
    UserCamp = apps.get_model("obozstudentow", "UserCamp")
    User = apps.get_model("obozstudentow", "User")

    camp, _ = Camp.objects.get_or_create(
        slug="default",
        defaults={"name": "Obóz (domyślny)", "is_active": True},
    )

    # Assign all users to the default camp
    for user in User.objects.all():
        role = UserCamp.Role.OWNER if user.is_staff else UserCamp.Role.MEMBER
        UserCamp.objects.get_or_create(user=user, camp=camp, defaults={"role": role})

    # Assign camp to all domain models
    models_to_update = [
        ("obozstudentow", "Group"),
        ("obozstudentow", "Announcement"),
        ("obozstudentow", "DailyQuest"),
        ("obozstudentow", "NightGameSignup"),
        ("obozstudentow", "Workshop"),
        ("obozstudentow", "House"),
        ("obozstudentow", "Meal"),
        ("obozstudentow", "ScheduleItem"),
        ("obozstudentow", "Bus"),
        ("obozstudentow", "FAQ"),
        ("obozstudentow", "Link"),
        ("obozstudentow", "HomeLink"),
        ("obozstudentow", "Image"),
        ("obozstudentow", "Partners"),
        ("obozstudentow", "Staff"),
        ("obozstudentow", "LifeGuard"),
        ("obozstudentow", "SoberDuty"),
        ("obozstudentow", "MealDuty"),
    ]

    for app_label, model_name in models_to_update:
        Model = apps.get_model(app_label, model_name)
        Model.objects.filter(camp__isnull=True).update(camp=camp)

    # BeReal models
    try:
        BerealPost = apps.get_model("bereal", "BerealPost")
        BerealPost.objects.filter(camp__isnull=True).update(camp=camp)
    except LookupError:
        pass

    try:
        BerealNotification = apps.get_model("bereal", "BerealNotification")
        BerealNotification.objects.filter(camp__isnull=True).update(camp=camp)
    except LookupError:
        pass

    # Bingo models
    try:
        BingoTaskTemplate = apps.get_model("bingo", "BingoTaskTemplate")
        BingoTaskTemplate.objects.filter(camp__isnull=True).update(camp=camp)
    except LookupError:
        pass

    try:
        BingoUserInstance = apps.get_model("bingo", "BingoUserInstance")
        BingoUserInstance.objects.filter(camp__isnull=True).update(camp=camp)
    except LookupError:
        pass

    # Tinder models
    try:
        TinderProfile = apps.get_model("tinder", "TinderProfile")
        TinderProfile.objects.filter(camp__isnull=True).update(camp=camp)
    except LookupError:
        pass


def reverse_default_camp(apps, schema_editor):
    Camp = apps.get_model("obozstudentow", "Camp")
    Camp.objects.filter(slug="default").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("obozstudentow", "0126_camp_announcement_camp_bus_camp_dailyquest_camp_and_more"),
        ("bereal", "0005_berealnotification_camp_berealpost_camp"),
        ("bingo", "0003_bingotasktemplate_camp_bingouserinstance_camp_and_more"),
        ("tinder", "0002_tinderprofile_camp"),
    ]

    operations = [
        migrations.RunPython(create_default_camp, reverse_default_camp),
    ]
