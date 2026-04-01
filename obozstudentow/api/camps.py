from django.shortcuts import get_object_or_404
from rest_framework import serializers, viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, PermissionDenied, ParseError

from ..models.camp import Camp, CampSettings, UserCamp


# ---------------------------------------------------------------------------
# Public helper used by other viewsets for camp-scoped queryset filtering
# ---------------------------------------------------------------------------


def get_camp_from_request(request):
    """
    Read X-Camp-Id header and return the corresponding Camp if the requesting
    user is a member, or None if the header is absent (backward-compat mode).

    Raises rest_framework.exceptions.PermissionDenied / ParseError / NotFound
    when the header is present but invalid.
    """
    camp_id = request.META.get("HTTP_X_CAMP_ID")
    if not camp_id:
        return None
    try:
        camp_id_int = int(camp_id)
    except (ValueError, TypeError):
        raise ParseError("Nagłówek X-Camp-Id musi być liczbą całkowitą.")
    try:
        camp = Camp.objects.get(pk=camp_id_int)
    except Camp.DoesNotExist:
        raise NotFound("Obóz o podanym ID nie istnieje.")
    if not UserCamp.objects.filter(user=request.user, camp=camp).exists():
        raise PermissionDenied("Nie jesteś członkiem tego obozu.")
    return camp


# ---------------------------------------------------------------------------
# Feature-flag helper
# ---------------------------------------------------------------------------

FEATURE_FIELDS = {
    "workshops": "feature_workshops",
    "schedule": "feature_schedule",
    "tinder": "feature_tinder",
    "bereal": "feature_bereal",
    "bingo": "feature_bingo",
    "points": "feature_points",
}


def check_feature_enabled(camp, feature: str) -> bool:
    """
    Return True if *feature* is enabled for *camp*.

    When *camp* is None (no X-Camp-Id header) the feature is considered enabled
    (backward-compat mode: single-camp behaviour).

    Raises ValueError for unknown feature names.
    """
    if camp is None:
        return True
    field = FEATURE_FIELDS.get(feature)
    if field is None:
        raise ValueError(f"Unknown feature: {feature}")
    try:
        settings = camp.settings
    except CampSettings.DoesNotExist:
        # Settings missing – treat as all enabled
        return True
    return getattr(settings, field, True)


def require_feature(camp, feature: str):
    """
    Like check_feature_enabled but raises PermissionDenied when the feature is
    disabled, suitable for use in DRF views.
    """
    if not check_feature_enabled(camp, feature):
        raise PermissionDenied(
            f"Funkcja '{feature}' jest wyłączona dla tego obozu."
        )


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------


class CampSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampSettings
        fields = (
            "logo",
            "primary_color",
            "secondary_color",
            "feature_workshops",
            "feature_schedule",
            "feature_tinder",
            "feature_bereal",
            "feature_bingo",
            "feature_points",
            "extra_config",
        )


class CampSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    settings = CampSettingsSerializer(read_only=True)

    def get_role(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            uc = UserCamp.objects.filter(user=request.user, camp=obj).first()
            return uc.role if uc else None
        return None

    class Meta:
        model = Camp
        fields = ("id", "name", "slug", "created_at", "is_active", "role", "settings")
        read_only_fields = ("id", "created_at", "role", "settings")


class CampCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camp
        fields = ("name", "slug")


class UserCampSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    camp_name = serializers.CharField(source="camp.name", read_only=True)

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()

    class Meta:
        model = UserCamp
        fields = (
            "id",
            "user",
            "user_email",
            "user_name",
            "camp",
            "camp_name",
            "role",
            "joined_at",
        )
        read_only_fields = ("id", "joined_at")


class AddMemberSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    user_id = serializers.IntegerField(required=False)
    role = serializers.ChoiceField(
        choices=UserCamp.Role.choices, default=UserCamp.Role.MEMBER
    )

    def validate(self, data):
        from ..models.user import User

        if not data.get("email") and not data.get("user_id"):
            raise serializers.ValidationError("Podaj email lub user_id użytkownika.")
        if data.get("email"):
            try:
                data["user"] = User.objects.get(email=data["email"])
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"email": "Nie znaleziono użytkownika o podanym emailu."}
                )
        else:
            try:
                data["user"] = User.objects.get(pk=data["user_id"])
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    {"user_id": "Nie znaleziono użytkownika o podanym ID."}
                )
        return data


# ---------------------------------------------------------------------------
# Helper: get camp from X-Camp-Id header and verify membership
# ---------------------------------------------------------------------------


def get_camp_for_user(request, require_owner=False):
    """
    Read the X-Camp-Id request header, fetch the Camp and verify
    that the authenticated user is a member (or owner when require_owner=True).
    Returns (camp, user_camp) or raises an appropriate DRF exception.
    """
    camp_id = request.META.get("HTTP_X_CAMP_ID")
    if not camp_id:
        raise ParseError("Brak nagłówka X-Camp-Id.")
    try:
        camp_id_int = int(camp_id)
    except (ValueError, TypeError):
        raise ParseError("Nagłówek X-Camp-Id musi być liczbą całkowitą.")

    try:
        camp = Camp.objects.get(pk=camp_id_int)
    except Camp.DoesNotExist:
        raise NotFound("Obóz o podanym ID nie istnieje.")

    try:
        user_camp = UserCamp.objects.get(user=request.user, camp=camp)
    except UserCamp.DoesNotExist:
        raise PermissionDenied("Nie jesteś członkiem tego obozu.")

    if require_owner and user_camp.role != UserCamp.Role.OWNER:
        raise PermissionDenied("Tylko właściciel obozu może wykonać tę operację.")

    return camp, user_camp


# ---------------------------------------------------------------------------
# IsCampMember DRF permission
# ---------------------------------------------------------------------------


class IsCampMember(IsAuthenticated):
    """
    Verifies that:
    1. The user is authenticated.
    2. The X-Camp-Id header is present and refers to an existing camp.
    3. The user is a member of that camp.

    The camp object is attached to ``request.camp`` and the
    UserCamp object to ``request.user_camp`` for downstream use.
    """

    message = "Nie jesteś członkiem tego obozu lub brak nagłówka X-Camp-Id."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        camp_id = request.META.get("HTTP_X_CAMP_ID")
        if not camp_id:
            return False
        try:
            camp = Camp.objects.get(pk=int(camp_id))
        except (Camp.DoesNotExist, ValueError, TypeError):
            return False
        uc = UserCamp.objects.filter(user=request.user, camp=camp).first()
        if not uc:
            return False
        request.camp = camp
        request.user_camp = uc
        return True


# ---------------------------------------------------------------------------
# CampScopedMixin – adds get_camp() to any ViewSet
# ---------------------------------------------------------------------------


class CampScopedMixin:
    """
    Mix into ViewSets that operate in the context of a single camp.
    Provides ``self.get_camp()`` which reads X-Camp-Id, validates membership,
    and caches the result on the request.
    """

    def get_camp(self, require_owner=False):
        if hasattr(self.request, "camp") and not require_owner:
            return self.request.camp
        camp, user_camp = get_camp_for_user(self.request, require_owner=require_owner)
        self.request.camp = camp
        self.request.user_camp = user_camp
        return camp


# ---------------------------------------------------------------------------
# ViewSets
# ---------------------------------------------------------------------------


class CampViewSet(viewsets.GenericViewSet):
    """
    POST   /api2/camps/                         – create a new camp
    GET    /api2/camps/my/                      – list camps the current user belongs to
    GET    /api2/camps/<id>/members/            – list members (camp member only)
    POST   /api2/camps/<id>/members/            – add member (OWNER only)
    DELETE /api2/camps/<id>/members/<member_id>/ – remove member (OWNER only)
    GET    /api2/camps/<id>/settings/           – get camp settings
    PATCH  /api2/camps/<id>/settings/           – update camp settings (OWNER only)
    """

    queryset = Camp.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request):
        serializer = CampCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        camp = serializer.save()
        # Creator becomes OWNER automatically
        UserCamp.objects.create(user=request.user, camp=camp, role=UserCamp.Role.OWNER)
        return Response(
            CampSerializer(camp, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="my")
    def my_camps(self, request):
        camps = Camp.objects.filter(user_camps__user=request.user).select_related(
            "settings"
        )
        serializer = CampSerializer(camps, many=True, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["get", "post"], url_path="members")
    def members(self, request, pk=None):
        camp = get_object_or_404(Camp, pk=pk)

        # Verify the requester is a member
        if not UserCamp.objects.filter(user=request.user, camp=camp).exists():
            return Response(
                {"detail": "Nie jesteś członkiem tego obozu."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if request.method == "GET":
            qs = UserCamp.objects.filter(camp=camp).select_related("user")
            serializer = UserCampSerializer(
                qs, many=True, context={"request": request}
            )
            return Response(serializer.data)

        # POST – add member (OWNER only)
        requester_uc = UserCamp.objects.get(user=request.user, camp=camp)
        if requester_uc.role != UserCamp.Role.OWNER:
            return Response(
                {"detail": "Tylko właściciel obozu może dodawać członków."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        role = serializer.validated_data["role"]

        uc, created = UserCamp.objects.get_or_create(
            user=user, camp=camp, defaults={"role": role}
        )
        if not created:
            return Response(
                {"detail": "Użytkownik jest już członkiem tego obozu."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            UserCampSerializer(uc, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"members/(?P<member_id>\d+)",
    )
    def remove_member(self, request, pk=None, member_id=None):
        camp = get_object_or_404(Camp, pk=pk)

        # Verify the requester is an OWNER
        requester_uc = UserCamp.objects.filter(user=request.user, camp=camp).first()
        if not requester_uc or requester_uc.role != UserCamp.Role.OWNER:
            return Response(
                {"detail": "Tylko właściciel obozu może usuwać członków."},
                status=status.HTTP_403_FORBIDDEN,
            )

        uc = get_object_or_404(UserCamp, pk=member_id, camp=camp)
        uc.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get", "patch"], url_path="settings")
    def settings(self, request, pk=None):
        camp = get_object_or_404(Camp, pk=pk)

        # Must be a member to read settings
        uc = UserCamp.objects.filter(user=request.user, camp=camp).first()
        if not uc:
            return Response(
                {"detail": "Nie jesteś członkiem tego obozu."},
                status=status.HTTP_403_FORBIDDEN,
            )

        camp_settings, _ = CampSettings.objects.get_or_create(camp=camp)

        if request.method == "GET":
            return Response(
                CampSettingsSerializer(camp_settings, context={"request": request}).data
            )

        # PATCH – update settings (OWNER only)
        if uc.role != UserCamp.Role.OWNER:
            return Response(
                {"detail": "Tylko właściciel obozu może edytować ustawienia."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = CampSettingsSerializer(
            camp_settings,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
