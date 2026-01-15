"""
Permission denial tests for project views.

Tests that unauthorized users cannot perform state-changing actions
even if they bypass the UI.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestProjectPermissionDenials:
    """Test that unauthorized users are denied project actions."""

    def test_technician_cannot_create_project(self, client, technician_user):
        """Technician cannot create projects (requires PROJECT_MANAGER or higher)."""
        client.force_login(technician_user)
        response = client.post(reverse('frontend:create-project'), {
            'name': 'Unauthorized Project',
            'description': 'Should not be created',
            'status': 'PLANNING',
            'priority': 'MEDIUM'
        })
        assert response.status_code in (403, 302)

    def test_viewer_cannot_edit_project(self, client, viewer_user, project):
        """Viewer cannot edit any project."""
        client.force_login(viewer_user)
        response = client.post(
            reverse('frontend:edit-project', args=[project.id]),
            {
                'name': 'Hacked Project Name',
                'description': 'Modified without permission'
            }
        )
        assert response.status_code in (403, 302)

    def test_viewer_cannot_delete_project(self, client, viewer_user, project):
        """Viewer cannot delete any project."""
        client.force_login(viewer_user)
        response = client.delete(
            reverse('frontend:project_crud', args=[project.id]),
            content_type='application/json'
        )
        assert response.status_code == 403

