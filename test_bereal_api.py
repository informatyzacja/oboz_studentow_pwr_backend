from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from obozstudentow.models import Setting
from bereal.models import BerealNotification, BerealPost
import json

User = get_user_model()


class BeerealAPITestCase(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create(
            email="test@example.com", first_name="Test", last_name="User"
        )
        self.user.set_password("testpass123")
        self.user.save()

        # Use APIClient for proper DRF authentication
        self.client = APIClient()

        # Get JWT tokens for authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # Create or update BeReal setting
        setting, created = Setting.objects.get_or_create(
            name="bereal_active",
            defaults={"value": "true", "description": "Czy BeReal jest aktywny"},
        )
        if not created:
            setting.value = "true"
            setting.save()

    def test_bereal_status_disabled(self):
        """Test BeReal status when disabled"""
        setting = Setting.objects.get(name="bereal_active")
        setting.value = "false"
        setting.save()

    response = self.client.get("/api2/bereal/status/")
    self.assertEqual(response.status_code, 200)
    data = response.json()
    # In new app response keys: is_active, was_today, can_post, deadline
    self.assertIn("is_active", data)
    self.assertFalse(data["is_active"])

    def test_bereal_status_enabled(self):
        """Test BeReal status when enabled"""

    response = self.client.get("/api2/bereal/status/")
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertIn("is_active", data)
    self.assertFalse(data["is_active"])  # No notification yet

    def test_bereal_status_with_notification(self):
        """Test BeReal status with active notification"""
        # Create active notification
        BerealNotification.objects.create(
            date=timezone.now().date(),
            deadline=timezone.now() + timezone.timedelta(hours=2),
        )

    response = self.client.get("/api2/bereal/status/")
    self.assertEqual(response.status_code, 200)
    data = response.json()
    self.assertTrue(data["is_active"])
    self.assertTrue(data["can_post"])

    def test_bereal_home_empty(self):
        """Test BeReal home with no posts"""
        response = self.client.get("/api2/bereal/home/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("posts", data)
        self.assertIn("pagination", data)
        self.assertIn("bereal_status", data)
        self.assertEqual(len(data["posts"]), 0)

    def test_bereal_profile(self):
        """Test BeReal profile endpoint"""
        response = self.client.get("/api2/bereal/profile/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("user", data)
        self.assertIn("posts", data)
        self.assertEqual(data["user"]["first_name"], "Test")
        self.assertEqual(data["user"]["last_name"], "User")

    def test_upload_bereal_disabled(self):
        """Test uploading BeReal when disabled"""
        setting = Setting.objects.get(name="bereal_active")
        setting.value = "false"
        setting.save()

        response = self.client.post(
            "/api2/bereal/upload/",
            {
                "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_upload_bereal_no_notification(self):
        """Test uploading BeReal when no notification exists"""
        response = self.client.post(
            "/api2/bereal/upload/",
            {
                "photo": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
