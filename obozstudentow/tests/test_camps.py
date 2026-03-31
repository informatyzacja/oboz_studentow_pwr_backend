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
        self.assertIn(resp.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class CampAPIMyCampsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user("me@example.com")
        self.other = make_user("other@example.com")
        self.client.force_authenticate(user=self.user)
        self.camp1 = Camp.objects.create(name="Camp A", slug="camp-a")
        self.camp2 = Camp.objects.create(name="Camp B", slug="camp-b")
        self.camp3 = Camp.objects.create(name="Camp C", slug="camp-c")
        UserCamp.objects.create(user=self.user, camp=self.camp1, role=UserCamp.Role.OWNER)
        UserCamp.objects.create(user=self.user, camp=self.camp2, role=UserCamp.Role.MEMBER)
        UserCamp.objects.create(user=self.other, camp=self.camp3, role=UserCamp.Role.OWNER)

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
        UserCamp.objects.create(user=self.owner, camp=self.camp, role=UserCamp.Role.OWNER)
        UserCamp.objects.create(user=self.member, camp=self.camp, role=UserCamp.Role.MEMBER)

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
        self.assertTrue(
            UserCamp.objects.filter(user=new_user, camp=self.camp).exists()
        )

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

        UserCamp.objects.create(user=self.user_a, camp=self.camp_a, role=UserCamp.Role.MEMBER)
        UserCamp.objects.create(user=self.user_b, camp=self.camp_b, role=UserCamp.Role.MEMBER)

        self.gtype = GroupType.objects.create(name="Testowy")
        self.group_a = Group.objects.create(
            name="Grupa A", type=self.gtype, camp=self.camp_a
        )
        self.group_b = Group.objects.create(
            name="Grupa B", type=self.gtype, camp=self.camp_b
        )

    def test_group_scoped_by_camp(self):
        self.client.force_authenticate(user=self.user_a)
        resp = self.client.get(
            "/api/group/", HTTP_X_CAMP_ID=str(self.camp_a.id)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [g["name"] for g in resp.json()]
        self.assertIn("Grupa A", names)
        self.assertNotIn("Grupa B", names)

    def test_camp_b_user_only_sees_camp_b_groups(self):
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.get(
            "/api/group/", HTTP_X_CAMP_ID=str(self.camp_b.id)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        names = [g["name"] for g in resp.json()]
        self.assertNotIn("Grupa A", names)
        self.assertIn("Grupa B", names)

    def test_non_member_cannot_access_camp_a_data(self):
        # user_b is NOT a member of camp_a
        self.client.force_authenticate(user=self.user_b)
        resp = self.client.get(
            "/api/group/", HTTP_X_CAMP_ID=str(self.camp_a.id)
        )
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
