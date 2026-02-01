from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class FrontendAssetReadPermissionsTest(TestCase):
    """Frontend AssetsView read permission tests."""

    @classmethod
    def setUpTestData(cls):
        cls.viewer = User.objects.create_user(
            username='viewer',
            password='pass',
            role='VIEWER',
        )

        cls.technician = User.objects.create_user(
            username='technician',
            password='pass',
            role='TECHNICIAN',
        )

        cls.manager = User.objects.create_user(
            username='manager',
            password='pass',
            role='MANAGER',
        )

    def test_viewer_denied_asset_list(self):
        """VIEWER should receive HTTP 403."""
        self.client.force_login(self.viewer)

        response = self.client.get(reverse('frontend:assets'))
        self.assertEqual(response.status_code, 403)

    def test_technician_denied_asset_list(self):
        """TECHNICIAN should receive HTTP 403."""
        self.client.force_login(self.technician)

        response = self.client.get(reverse('frontend:assets'))
        self.assertEqual(response.status_code, 403)

    def test_manager_can_access_asset_list(self):
        """MANAGER is allowed to access assets."""
        self.client.force_login(self.manager)

        response = self.client.get(reverse('frontend:assets'))
        self.assertEqual(response.status_code, 200)
