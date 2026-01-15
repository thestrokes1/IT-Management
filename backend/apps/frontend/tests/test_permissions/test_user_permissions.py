"""
Permission denial tests for user views.

Tests that unauthorized users cannot perform state-changing actions
even if they bypass the UI.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestUserPermissionDenials:
    """Test that unauthorized users are denied user management actions."""

    def test_non_superadmin_cannot_delete_user(self, client, manager_user, other_user):
        """Manager cannot delete users (only SUPERADMIN can delete)."""
        client.force_login(manager_user)
        response = client.post(
            reverse('frontend:delete_user', args=[other_user.id])
        )
        assert response.status_code == 403

    def test_non_superadmin_cannot_change_role(self, client, manager_user, other_user):
        """Manager cannot change user roles (only SUPERADMIN can)."""
        client.force_login(manager_user)
        response = client.post(
            reverse('frontend:change-user-role', args=[other_user.id]),
            {'role': 'TECHNICIAN'}
        )
        # This redirects with error message, not 403, but unauthorized access is still blocked
        assert response.status_code in (403, 302)
        if response.status_code == 302:
            # Should redirect with error message
            assert 'error' in response.url or 'Permission' in response.url

