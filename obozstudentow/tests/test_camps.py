"""
Tests for multi-camp support.

Covers:
- Camp creation and UserCamp membership
- Data isolation between camps
- Camp API endpoints (create, list mine, add members)
- Authorization: non-members cannot access camp data
- X-Camp-Id header validation
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from obozstudentow.models.camp import Camp, UserCamp
from obozstudentow.models.user import User


def make_user(email, password="password123", is_staff=False, **kwargs):
    u = User(email=email, is_staff=is_staff, **kwargs)
    u.set_password(password)
    u.save()
    return u


class CampModelTest(TestCase):
    def setUp(self):
        self.user = make_user("owner@example.com")
        self.camp = Camp.objects.create(name="Obóz Testowy", slug="test-camp")

    def test_camp_str(self):
        self.assertEqual(str(self.camp), "Obóz Testowy")

    def test_user_camp_str(self):
        uc = UserCamp.objects.create(
            user=self.user, camp=self.camp, role=UserCamp.Role.OWNER
        )
        self.assertIn("Obóz Testowy", str(uc))
        self.assertIn(str(self.user), str(uc))

    def test_unique_together_user_camp(self):
        from django.db import IntegrityError

        UserCamp.objects.create(user=self.user, camp=self.camp)
        with self.assertRaises(IntegrityError):
            UserCamp.objects.create(user=self.user, camp=self.camp)

    def test_roles(self):
        uc = UserCamp.objects.create(
            user=self.user, camp=self.camp, role=UserCamp.Role.OWNER
        )
        self.assertEqual(uc.role, "owner")
        uc.role = UserCamp.Role.MEMBER
        uc.save()
        uc.refresh_from_db()
        self.assertEqual(uc.role, "member")


class CampAPICreateTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user("creator@example.com")
        self.client.force_authenticate(user=self.user)

    def test_create_camp(self):
        resp = self.client.post(
            "/api2/camps/", {"name": "Nowy Obóz", "slug": "nowy-oboz"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        data = resp.json()
        self.assertEqual(data["name"], "Nowy Obóz")
        self.assertEqual(data["slug"], "nowy-oboz")
        # Creator automatically becomes OWNER
        self.assertEqual(data["role"], UserCamp.Role.OWNER)
        self.assertTrue(
            UserCamp.objects.filter(
                user=self.user, camp__slug="nowy-oboz", role=UserCamp.Role.OWNER
            ).exists()
        )

    def test_create_camp_duplicate_slug(self):
        Camp.objects.create(name="Existing", slug="existing")
        resp = self.client.post(
            "/api2/camps/", {"name": "Nowy", "slug": "existing"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_camp_requires_auth(self):
        anon = APIClient()
        resp = anon.post(
            "/api2/camps/", {"name": "Anon", "slug": "anon"}, format="json"
        )
        self.assertIn(
            resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )


class CampAPIMyCampsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user("me@example.com")
        self.other = make_user("other@example.com")
        self.client.force_authenticate(user=self.user)
        self.camp1 = Camp.objects.create(name="Camp A", slug="camp-a")
        self.camp2 = Camp.objects.create(name="Camp B", slug="camp-b")
        self.camp3 = Camp.objects.create(name="Camp C", slug="camp-c")
        UserCamp.objects.create(
            user=self.user, camp=self.camp1, role=UserCamp.Role.OWNER
        )
        UserCamp.objects.create(
            user=self.user, camp=self.camp2, role=UserCamp.Role.MEMBER
        )
        UserCamp.objects.create(
            user=self.other, camp=self.camp3, role=UserCamp.Role.OWNER
        )

    def test_list_my_camps(self):
        resp = self.client.get("/api2/camps/my/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        slugs = {c["slug"] for c in resp.json()}
        self.assertIn("camp-a", slugs)
        self.assertIn("camp-b", slugs)
        # camp3 belongs to another user
        self.assertNotIn("camp-c", slugs)

    def test_user_in_multiple_camps(self):
        resp = self.client.get("/api2/camps/my/")
        self.assertEqual(len(resp.json()), 2)


class CampAPIMembersTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = make_user("owner@example.com")
        self.member = make_user("member@example.com")
        self.outsider = make_user("outsider@example.com")
        self.camp = Camp.objects.create(name="Camp X", slug="camp-x")
        UserCamp.objects.create(
            user=self.owner, camp=self.camp, role=UserCamp.Role.OWNER
        )
        UserCamp.objects.create(
            user=self.member, camp=self.camp, role=UserCamp.Role.MEMBER
        )

    def test_owner_can_list_members(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.get(f"/api2/camps/{self.camp.id}/members/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        emails = {m["user_email"] for m in resp.json()}
        self.assertIn("owner@example.com", emails)
        self.assertIn("member@example.com", emails)

    def test_member_can_list_members(self):
        self.client.force_authenticate(user=self.member)
        resp = self.client.get(f"/api2/camps/{self.camp.id}/members/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_outsider_cannot_list_members(self):
        self.client.force_authenticate(user=self.outsider)
        resp = self.client.get(f"/api2/camps/{self.camp.id}/members/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_add_member(self):
        self.client.force_authenticate(user=self.owner)
        new_user = make_user("new@example.com")
        resp = self.client.post(
            f"/api2/camps/{self.camp.id}/members/",
            {"email": "new@example.com", "role": "member"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserCamp.objects.filter(user=new_user, camp=self.camp).exists())

    def test_member_cannot_add_member(self):
        self.client.force_authenticate(user=self.member)
        new_user = make_user("new2@example.com")
        resp = self.client.post(
            f"/api2/camps/{self.camp.id}/members/",
            {"email": "new2@example.com", "role": "member"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_duplicate_member_returns_409(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.post(
            f"/api2/camps/{self.camp.id}/members/",
            {"email": "member@example.com", "role": "member"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)

    def test_owner_can_remove_member(self):
        self.client.force_authenticate(user=self.owner)
        uc = UserCamp.objects.get(user=self.member, camp=self.camp)
        resp = self.client.delete(
            f"/api2/camps/{self.camp.id}/members/{uc.id}/",
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            UserCamp.objects.filter(user=self.member, camp=self.camp).exists()
        )


class CampDataIsolationTest(TestCase):
    """Verify that data scoped by camp is isolated between camps."""

    def setUp(self):
        from obozstudentow.models import Group, GroupType

        self.client = APIClient()

        self.user_a = make_user("usera@example.com")
        self.user_b = make_user("userb@example.com")

        self.camp_a = Camp.objects.create(name="Camp A", slug="iso-camp-a")
        self.camp_b = Camp.objects.create(name="Camp B", slug="iso-camp-b")

        UserCamp.objects.create(
            user=self.user_a, camp=self.camp_a, role=UserCamp.Role.MEMBER
        )
        UserCamp.objects.create(
            user=self.user_b, camp=self.camp_b, role=UserCamp.Role.MEMBER
        )

        self.gtype = GroupType.objects.create(name="Testowy")
        self.group_a = Group.objects.create(
            name="Grupa A", type=self.gtype, camp=self.camp_a
        )
        self.group_b = Group.objects.create(
            name="Grupa B", type=self.gtype, camp=self.camp_b
        )

    def test_group_scoped_by_camp(self):
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get("/api/group/", HTTP_X_CAMP_ID=str(self.camp_a.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [g["name"] for g in resp.json()]
        self.assertIn("Grupa A", names)
        self.assertNotIn("Grupa B", names)

    def test_camp_b_user_only_sees_camp_b_groups(self):
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.get("/api/group/", HTTP_X_CAMP_ID=str(self.camp_b.id))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [g["name"] for g in resp.json()]
        self.assertNotIn("Grupa A", names)
        self.assertIn("Grupa B", names)

    def test_non_member_cannot_access_camp_a_data(self):
        # user_b is NOT a member of camp_a
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.get("/api/group/", HTTP_X_CAMP_ID=str(self.camp_a.id))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_camp_header_returns_all_backward_compat(self):
        # Without X-Camp-Id header, endpoint returns all data (backward compat)
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get("/api/group/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [g["name"] for g in resp.json()]
        # Both groups visible without scoping
        self.assertIn("Grupa A", names)
        self.assertIn("Grupa B", names)

    def test_invalid_camp_id_returns_400(self):
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get("/api/group/", HTTP_X_CAMP_ID="not-a-number")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_camp_id_returns_404(self):
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get("/api/group/", HTTP_X_CAMP_ID="999999")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# CampSettings model tests
# ---------------------------------------------------------------------------


class CampSettingsModelTest(TestCase):
    def setUp(self):
        self.camp = Camp.objects.create(name="Settings Camp", slug="settings-camp")

    def test_settings_auto_created(self):
        """CampSettings should be auto-created on Camp creation."""
        from obozstudentow.models.camp import CampSettings

        self.assertTrue(CampSettings.objects.filter(camp=self.camp).exists())

    def test_settings_str(self):
        from obozstudentow.models.camp import CampSettings

        settings = self.camp.settings
        self.assertIn("Settings Camp", str(settings))

    def test_feature_flags_default_true(self):
        s = self.camp.settings
        for field in [
            "feature_workshops",
            "feature_schedule",
            "feature_tinder",
            "feature_bereal",
            "feature_bingo",
            "feature_points",
        ]:
            self.assertTrue(getattr(s, field), f"{field} should default to True")

    def test_branding_defaults(self):
        s = self.camp.settings
        self.assertEqual(s.primary_color, "#3b5bdb")
        self.assertEqual(s.secondary_color, "#ffffff")


# ---------------------------------------------------------------------------
# Feature flag helper tests
# ---------------------------------------------------------------------------


class FeatureFlagHelperTest(TestCase):
    def setUp(self):
        self.camp = Camp.objects.create(name="Flag Camp", slug="flag-camp")

    def test_feature_enabled_by_default(self):
        from obozstudentow.api.camps import check_feature_enabled

        self.assertTrue(check_feature_enabled(self.camp, "workshops"))
        self.assertTrue(check_feature_enabled(self.camp, "bingo"))

    def test_feature_disabled(self):
        from obozstudentow.api.camps import check_feature_enabled

        self.camp.settings.feature_workshops = False
        self.camp.settings.save()
        self.assertFalse(check_feature_enabled(self.camp, "workshops"))

    def test_feature_enabled_when_camp_none(self):
        """When no camp (backward-compat mode), all features are enabled."""
        from obozstudentow.api.camps import check_feature_enabled

        self.assertTrue(check_feature_enabled(None, "bingo"))

    def test_require_feature_raises_when_disabled(self):
        from rest_framework.exceptions import PermissionDenied
        from obozstudentow.api.camps import require_feature

        self.camp.settings.feature_tinder = False
        self.camp.settings.save()
        with self.assertRaises(PermissionDenied):
            require_feature(self.camp, "tinder")

    def test_require_feature_ok_when_enabled(self):
        from obozstudentow.api.camps import require_feature

        # Should not raise
        require_feature(self.camp, "tinder")


# ---------------------------------------------------------------------------
# Camp settings API endpoint tests
# ---------------------------------------------------------------------------


class CampSettingsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner = make_user("owner@settings.com")
        self.member = make_user("member@settings.com")
        self.other = make_user("other@settings.com")
        self.camp = Camp.objects.create(name="API Settings Camp", slug="api-settings")
        UserCamp.objects.create(
            user=self.owner, camp=self.camp, role=UserCamp.Role.OWNER
        )
        UserCamp.objects.create(
            user=self.member, camp=self.camp, role=UserCamp.Role.MEMBER
        )

    def test_owner_can_read_settings(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.get(f"/api2/camps/{self.camp.pk}/settings/")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("feature_workshops", data)
        self.assertIn("primary_color", data)

    def test_member_can_read_settings(self):
        self.client.force_authenticate(user=self.member)
        resp = self.client.get(f"/api2/camps/{self.camp.pk}/settings/")
        self.assertEqual(resp.status_code, 200)

    def test_non_member_cannot_read_settings(self):
        self.client.force_authenticate(user=self.other)
        resp = self.client.get(f"/api2/camps/{self.camp.pk}/settings/")
        self.assertEqual(resp.status_code, 403)

    def test_owner_can_patch_settings(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.patch(
            f"/api2/camps/{self.camp.pk}/settings/",
            {"feature_bingo": False, "primary_color": "#ff0000"},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.camp.settings.refresh_from_db()
        self.assertFalse(self.camp.settings.feature_bingo)
        self.assertEqual(self.camp.settings.primary_color, "#ff0000")

    def test_member_cannot_patch_settings(self):
        self.client.force_authenticate(user=self.member)
        resp = self.client.patch(
            f"/api2/camps/{self.camp.pk}/settings/",
            {"feature_bingo": False},
            format="json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_settings_in_my_camps(self):
        self.client.force_authenticate(user=self.owner)
        resp = self.client.get("/api2/camps/my/")
        self.assertEqual(resp.status_code, 200)
        camps = resp.json()
        self.assertEqual(len(camps), 1)
        self.assertIn("settings", camps[0])
        self.assertIn("feature_workshops", camps[0]["settings"])


# ---------------------------------------------------------------------------
# Feature flag enforcement via API tests
# ---------------------------------------------------------------------------


class FeatureFlagAPIEnforcementTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user("ff_user@example.com")
        self.camp = Camp.objects.create(name="FF Camp", slug="ff-camp")
        UserCamp.objects.create(
            user=self.user, camp=self.camp, role=UserCamp.Role.MEMBER
        )
        self.camp.settings.feature_workshops = False
        self.camp.settings.feature_schedule = False
        self.camp.settings.save()
        self.client.force_authenticate(user=self.user)
        self.headers = {"HTTP_X_CAMP_ID": str(self.camp.pk)}

    def test_workshop_returns_403_when_disabled(self):
        resp = self.client.get("/api/workshop/", **self.headers)
        self.assertEqual(resp.status_code, 403)

    def test_schedule_returns_403_when_disabled(self):
        resp = self.client.get("/api/schedule/", **self.headers)
        self.assertEqual(resp.status_code, 403)

    def test_workshop_accessible_when_enabled(self):
        self.camp.settings.feature_workshops = True
        self.camp.settings.save()
        resp = self.client.get("/api/workshop/", **self.headers)
        # 200 or 404 (no data) – not 403
        self.assertNotEqual(resp.status_code, 403)


# ---------------------------------------------------------------------------
# Django Admin isolation unit tests
# ---------------------------------------------------------------------------


class AdminCampIsolationTest(TestCase):
    """
    Tests for CampScopedAdmin queryset isolation and permission methods.

    These tests exercise the mixin logic directly using a mock request,
    without loading the full admin HTTP stack.
    """

    def setUp(self):
        from obozstudentow.admin import WorkshopAdmin
        from django.contrib.admin import site as admin_site

        self.admin_site = admin_site

        # Superuser
        self.superuser = make_user("super@admin.com", is_staff=True, is_superuser=True)

        # Two owners with separate camps
        self.owner_a = make_user("owner_a@admin.com", is_staff=True)
        self.owner_b = make_user("owner_b@admin.com", is_staff=True)

        self.camp_a = Camp.objects.create(name="Camp A", slug="camp-a")
        self.camp_b = Camp.objects.create(name="Camp B", slug="camp-b")

        UserCamp.objects.create(
            user=self.owner_a, camp=self.camp_a, role=UserCamp.Role.OWNER
        )
        UserCamp.objects.create(
            user=self.owner_b, camp=self.camp_b, role=UserCamp.Role.OWNER
        )

        # Member with no admin access
        self.member = make_user("member@admin.com")
        UserCamp.objects.create(
            user=self.member, camp=self.camp_a, role=UserCamp.Role.MEMBER
        )

    def _mock_request(self, user, session=None):
        """Build a minimal request-like object for admin mixin testing."""
        from unittest.mock import MagicMock

        req = MagicMock()
        req.user = user
        req.session = session or {}
        return req

    def _get_workshop_admin(self):
        from obozstudentow.admin.workshop import WorkshopAdmin
        from django.contrib.admin import site

        return WorkshopAdmin(
            __import__("obozstudentow.models", fromlist=["Workshop"]).Workshop,
            site,
        )

    def test_superuser_sees_all_workshops(self):
        """Superuser queryset is not filtered."""
        from obozstudentow.models import Workshop

        Workshop.objects.create(
            name="WS-A",
            start="2026-07-01 10:00",
            userLimit=10,
            end="2026-07-01 12:00",
            camp=self.camp_a,
        )
        Workshop.objects.create(
            name="WS-B",
            start="2026-07-01 10:00",
            userLimit=10,
            end="2026-07-01 12:00",
            camp=self.camp_b,
        )
        admin_obj = self._get_workshop_admin()
        req = self._mock_request(self.superuser)
        qs = admin_obj.get_queryset(req)
        self.assertEqual(qs.count(), 2)

    def test_owner_a_sees_only_camp_a_workshops(self):
        """OWNER A queryset is limited to camp A."""
        from obozstudentow.models import Workshop

        Workshop.objects.create(
            name="WS-A",
            start="2026-07-01 10:00",
            userLimit=10,
            end="2026-07-01 12:00",
            camp=self.camp_a,
        )
        Workshop.objects.create(
            name="WS-B",
            start="2026-07-01 10:00",
            userLimit=10,
            end="2026-07-01 12:00",
            camp=self.camp_b,
        )
        admin_obj = self._get_workshop_admin()
        req = self._mock_request(self.owner_a)
        qs = admin_obj.get_queryset(req)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().name, "WS-A")

    def test_owner_a_no_access_to_camp_b_object(self):
        """OWNER A cannot view/change an object belonging to camp B."""
        from obozstudentow.models import Workshop

        ws_b = Workshop.objects.create(
            name="WS-B",
            start="2026-07-01 10:00",
            userLimit=10,
            end="2026-07-01 12:00",
            camp=self.camp_b,
        )
        admin_obj = self._get_workshop_admin()
        req = self._mock_request(self.owner_a)
        self.assertFalse(admin_obj.has_view_permission(req, ws_b))
        self.assertFalse(admin_obj.has_change_permission(req, ws_b))

    def test_owner_a_can_access_own_object(self):
        """OWNER A can view/change an object belonging to camp A."""
        from obozstudentow.models import Workshop

        ws_a = Workshop.objects.create(
            name="WS-A",
            start="2026-07-01 10:00",
            userLimit=10,
            end="2026-07-01 12:00",
            camp=self.camp_a,
        )
        admin_obj = self._get_workshop_admin()
        req = self._mock_request(self.owner_a)
        self.assertTrue(admin_obj.has_view_permission(req, ws_a))
        self.assertTrue(admin_obj.has_change_permission(req, ws_a))

    def test_member_has_no_admin_perms(self):
        """MEMBER should not have any admin permissions."""
        admin_obj = self._get_workshop_admin()
        req = self._mock_request(self.member)
        self.assertFalse(admin_obj.has_add_permission(req))
        self.assertFalse(admin_obj.has_view_permission(req))


# ---------------------------------------------------------------------------
# Admin active camp tests
# ---------------------------------------------------------------------------


class AdminActiveCampTest(TestCase):
    def setUp(self):
        self.owner = make_user("owner@active.com", is_staff=True)
        self.camp_a = Camp.objects.create(name="Camp Active A", slug="camp-active-a")
        self.camp_b = Camp.objects.create(name="Camp Active B", slug="camp-active-b")
        UserCamp.objects.create(
            user=self.owner, camp=self.camp_a, role=UserCamp.Role.OWNER
        )
        UserCamp.objects.create(
            user=self.owner, camp=self.camp_b, role=UserCamp.Role.OWNER
        )

    def _mock_request(self, user, session=None):
        from unittest.mock import MagicMock

        req = MagicMock()
        req.user = user
        req.session = session if session is not None else {}
        return req

    def _get_workshop_admin(self):
        from obozstudentow.admin.workshop import WorkshopAdmin
        from django.contrib.admin import site

        return WorkshopAdmin(
            __import__("obozstudentow.models", fromlist=["Workshop"]).Workshop,
            site,
        )

    def test_active_camp_filters_queryset(self):
        """When active camp is set to camp_a, only camp_a workshops are shown."""
        from obozstudentow.models import Workshop
        from obozstudentow.admin.mixins import SESSION_ACTIVE_CAMP_KEY

        Workshop.objects.create(
            name="Active-A",
            start="2026-07-01 10:00",
            userLimit=10,
            end="2026-07-01 12:00",
            camp=self.camp_a,
        )
        Workshop.objects.create(
            name="Active-B",
            start="2026-07-01 10:00",
            userLimit=10,
            end="2026-07-01 12:00",
            camp=self.camp_b,
        )
        session = {SESSION_ACTIVE_CAMP_KEY: self.camp_a.pk}
        req = self._mock_request(self.owner, session=session)

        admin_obj = self._get_workshop_admin()
        qs = admin_obj.get_queryset(req)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().name, "Active-A")

    def test_no_active_camp_shows_all_owned(self):
        """Without active camp set, all camps owned by user are shown."""
        from obozstudentow.models import Workshop

        Workshop.objects.create(
            name="Active-A",
            start="2026-07-01 10:00",
            userLimit=10,
            end="2026-07-01 12:00",
            camp=self.camp_a,
        )
        Workshop.objects.create(
            name="Active-B",
            start="2026-07-01 10:00",
            userLimit=10,
            end="2026-07-01 12:00",
            camp=self.camp_b,
        )
        req = self._mock_request(self.owner)
        admin_obj = self._get_workshop_admin()
        qs = admin_obj.get_queryset(req)
        self.assertEqual(qs.count(), 2)

    def test_save_model_auto_assigns_active_camp(self):
        """New record gets active camp auto-assigned on save."""
        from obozstudentow.models import Workshop
        from obozstudentow.admin.mixins import SESSION_ACTIVE_CAMP_KEY

        session = {SESSION_ACTIVE_CAMP_KEY: self.camp_a.pk}
        req = self._mock_request(self.owner, session=session)

        ws = Workshop(
            name="AutoAssign",
            start="2026-07-01 10:00",
            userLimit=10,
            end="2026-07-01 12:00",
        )
        admin_obj = self._get_workshop_admin()
        admin_obj.save_model(req, ws, form=None, change=False)
        self.assertEqual(ws.camp, self.camp_a)

    def test_save_model_falls_back_to_first_owned_camp(self):
        """If no active camp, new record is assigned to first owned camp."""
        from obozstudentow.models import Workshop

        req = self._mock_request(self.owner)
        ws = Workshop(
            name="FallbackAssign",
            start="2026-07-01 10:00",
            userLimit=10,
            end="2026-07-01 12:00",
        )
        admin_obj = self._get_workshop_admin()
        admin_obj.save_model(req, ws, form=None, change=False)
        # Should be one of the owned camps
        self.assertIn(ws.camp, [self.camp_a, self.camp_b])

    def test_active_camp_invalid_for_user_is_cleared(self):
        """Active camp belonging to another user gets cleared from session."""
        from obozstudentow.admin.mixins import SESSION_ACTIVE_CAMP_KEY, _get_active_camp

        other_camp = Camp.objects.create(name="Other Camp", slug="other-camp")
        session = {SESSION_ACTIVE_CAMP_KEY: other_camp.pk}
        req = self._mock_request(self.owner, session=session)

        result = _get_active_camp(req)
        self.assertIsNone(result)
        self.assertNotIn(SESSION_ACTIVE_CAMP_KEY, req.session)
