from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth.decorators import permission_required

from ...models import UserFCMToken, Announcement, GroupMember, GroupWarden

from ..notifications import send_notification

from django.db.models import Q

from django.utils import timezone


@api_view(["POST"])
@permission_required("obozstudentow.can_add_announcement")
def add_announcement(request):
    title = request.data.get("title")
    content = request.data.get("content")
    hide_date = request.data.get("hide_date")

    if title is None or content is None or hide_date is None:
        return Response(
            {
                "success": False,
                "error": "Nie podano tytułu, treści lub daty zakończenia ogłoszenia",
            }
        )

    hide_date = timezone.datetime.strptime(hide_date, "%Y-%m-%dT%H:%M")

    groupId = request.data.get("groupId")

    Announcement.objects.create(
        title=title,
        content=content,
        group_id=groupId,
        addedBy=request.user,
        hide_date=hide_date,
    )

    info = "Dodano ogłoszenie"

    if request.data.get("sendNotif"):
        if groupId is None:
            tokens = list(
                UserFCMToken.objects.filter(user__notifications=True).values_list(
                    "token", flat=True
                )
            )
        else:
            tokens = list(
                UserFCMToken.objects.filter(
                    user__notifications=True,
                    user__in=GroupMember.objects.filter(group__id=groupId).values_list(
                        "user", flat=True
                    ),
                ).values_list("token", flat=True)
                | UserFCMToken.objects.filter(
                    user__notifications=True,
                    user__in=GroupWarden.objects.filter(group__id=groupId).values_list(
                        "user", flat=True
                    ),
                ).values_list("token", flat=True)
            )

        if tokens:
            response = send_notification(title, content, tokens)
            info = f"Wysłano powiadomienie do {response.success_count} użytkowników"
            # , {response.failure_count} niepowodzeń'

    return Response({"success": True, "info": info})


from .. import AnnouncementSerializer


@api_view(["GET"])
@permission_required("obozstudentow.can_add_announcement")
def get_visible_announcements(request):
    announcements = (
        Announcement.objects.filter(visible=True)
        .filter(Q(hide_date=None) | Q(hide_date__gt=timezone.now()))
        .order_by("-date")
    )

    return Response(
        AnnouncementSerializer(
            announcements, many=True, context={"request": request}
        ).data
    )


@api_view(["PUT"])
@permission_required("obozstudentow.can_add_announcement")
def hide_announcement(request, id):
    try:
        announcement = Announcement.objects.get(id=id)
        announcement.visible = False
        announcement.save()
    except Announcement.DoesNotExist:
        return Response(
            {"success": False, "error": "Nie znaleziono ogłoszenia o podanym id"}
        )
    return Response({"success": True})
