"""
Permission denial tests for ticket views.

Tests that unauthorized users cannot perform state-changing actions
even if they bypass the UI.
"""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestTicketPermissionDenials:
    """Test that unauthorized users are denied ticket actions."""

    def test_viewer_cannot_create_ticket(self, client, viewer_user):
        """Viewer cannot create tickets (only non-VIEWER roles can create)."""
        client.force_login(viewer_user)
        response = client.post(reverse('frontend:create-ticket'), {
            'title': 'Unauthorized Ticket',
            'description': 'Should not be created',
            'priority': 'MEDIUM',
            'status': 'NEW'
        })
        # Service raises PermissionDeniedError, view re-renders form with error
        # Check that ticket was NOT created
        from apps.tickets.models import Ticket
        assert not Ticket.objects.filter(title='Unauthorized Ticket').exists()
        # Verify user was redirected back to form with error
        assert response.status_code == 200

    def test_viewer_cannot_delete_ticket(self, client, viewer_user, ticket):
        """Viewer cannot delete any ticket."""
        client.force_login(viewer_user)
        response = client.delete(
            reverse('frontend:ticket_crud', args=[ticket.id]),
            content_type='application/json'
        )
        assert response.status_code == 403

    def test_viewer_cannot_update_ticket(self, client, viewer_user, ticket):
        """Viewer cannot update any ticket via PATCH."""
        client.force_login(viewer_user)
        response = client.patch(
            reverse('frontend:ticket_crud', args=[ticket.id]),
            data={'title': 'Hacked Title'},
            content_type='application/json'
        )
        assert response.status_code == 403

