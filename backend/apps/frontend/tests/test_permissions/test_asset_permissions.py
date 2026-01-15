"""
Permission denial tests for asset views.

Tests that unauthorized users cannot perform state-changing actions
even if they bypass the UI.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAssetPermissionDenials:
    """Test that unauthorized users are denied asset actions."""

    def test_technician_cannot_delete_asset(self, client, technician_user, asset):
        """Technician cannot delete assets (requires IT_ADMIN, SUPERADMIN, or ADMIN)."""
        client.force_login(technician_user)
        response = client.delete(
            reverse('frontend:asset_crud', args=[asset.id]),
            content_type='application/json'
        )
        assert response.status_code == 403

    def test_viewer_cannot_update_asset(self, client, viewer_user, asset):
        """Viewer cannot update any asset."""
        client.force_login(viewer_user)
        response = client.patch(
            reverse('frontend:asset_crud', args=[asset.id]),
            data={'name': 'Hacked Asset Name'},
            content_type='application/json'
        )
        assert response.status_code == 403

