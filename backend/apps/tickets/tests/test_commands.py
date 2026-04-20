"""
Integration tests for ticket CQRS commands.

These tests hit the real DB (SQLite) and verify that commands enforce
authorization correctly and produce the expected side-effects.

transaction.on_commit() callbacks do NOT fire in non-transactional test mode,
so activity logging is intentionally not tested here.
"""

import pytest

from apps.tickets.application.create_ticket import CreateTicket
from apps.tickets.application.update_ticket import UpdateTicket
from apps.core.domain.authorization import AuthorizationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_ticket_data(category_id, ticket_type_id, title='Test ticket'):
    return {
        'title': title,
        'description': 'Test description',
        'category_id': category_id,
        'ticket_type_id': ticket_type_id,
        'priority': 'MEDIUM',
    }


# ---------------------------------------------------------------------------
# CreateTicket
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCreateTicket:
    def test_viewer_cannot_create(self, viewer, ticket_category, ticket_type):
        data = make_ticket_data(ticket_category.id, ticket_type.id)
        with pytest.raises(AuthorizationError):
            CreateTicket().execute(actor=viewer, ticket_data=data)

    def test_technician_can_create(self, technician, ticket_category, ticket_type):
        data = make_ticket_data(ticket_category.id, ticket_type.id)
        result = CreateTicket().execute(actor=technician, ticket_data=data)
        assert result.success is True
        assert result.data['title'] == 'Test ticket'
        assert result.data['status'] == 'NEW'

    def test_manager_can_create(self, manager, ticket_category, ticket_type):
        data = make_ticket_data(ticket_category.id, ticket_type.id)
        result = CreateTicket().execute(actor=manager, ticket_data=data)
        assert result.success is True

    def test_it_admin_can_create(self, it_admin, ticket_category, ticket_type):
        data = make_ticket_data(ticket_category.id, ticket_type.id)
        result = CreateTicket().execute(actor=it_admin, ticket_data=data)
        assert result.success is True

    def test_superadmin_can_create(self, superadmin, ticket_category, ticket_type):
        data = make_ticket_data(ticket_category.id, ticket_type.id)
        result = CreateTicket().execute(actor=superadmin, ticket_data=data)
        assert result.success is True

    def test_returns_ticket_id(self, technician, ticket_category, ticket_type):
        data = make_ticket_data(ticket_category.id, ticket_type.id)
        result = CreateTicket().execute(actor=technician, ticket_data=data)
        assert 'ticket_id' in result.data
        assert len(result.data['ticket_id']) == 36  # UUID string


# ---------------------------------------------------------------------------
# UpdateTicket
# ---------------------------------------------------------------------------

@pytest.fixture
def open_ticket(db, manager, ticket_category, ticket_type):
    """A ticket assigned to nobody, created by manager."""
    from apps.tickets.models import Ticket
    return Ticket.objects.create(
        title='Open ticket',
        description='Test',
        category=ticket_category,
        ticket_type=ticket_type,
        requester=manager,
        created_by=manager,
        status='OPEN',
    )


@pytest.fixture
def assigned_ticket(db, manager, technician, ticket_category, ticket_type):
    """A ticket assigned to the technician fixture."""
    from apps.tickets.models import Ticket
    return Ticket.objects.create(
        title='Assigned ticket',
        description='Test',
        category=ticket_category,
        ticket_type=ticket_type,
        requester=manager,
        created_by=manager,
        assigned_to=technician,
        assignment_status='ASSIGNED',
        status='IN_PROGRESS',
    )


@pytest.mark.django_db
class TestUpdateTicket:
    def test_manager_can_update_any_ticket(self, manager, open_ticket):
        result = UpdateTicket().execute(
            user=manager,
            ticket_id=str(open_ticket.ticket_id),
            ticket_data={'priority': 'HIGH'},
        )
        assert result.success is True

    def test_it_admin_can_update_any_ticket(self, it_admin, open_ticket):
        result = UpdateTicket().execute(
            user=it_admin,
            ticket_id=str(open_ticket.ticket_id),
            ticket_data={'priority': 'CRITICAL'},
        )
        assert result.success is True

    def test_superadmin_can_update_any_ticket(self, superadmin, open_ticket):
        result = UpdateTicket().execute(
            user=superadmin,
            ticket_id=str(open_ticket.ticket_id),
            ticket_data={'status': 'RESOLVED'},
        )
        assert result.success is True

    def test_technician_can_update_own_assigned_ticket(self, technician, assigned_ticket):
        result = UpdateTicket().execute(
            user=technician,
            ticket_id=str(assigned_ticket.ticket_id),
            ticket_data={'status': 'RESOLVED'},
        )
        assert result.success is True

    def test_technician_denied_on_unassigned_ticket(self, technician, open_ticket):
        result = UpdateTicket().execute(
            user=technician,
            ticket_id=str(open_ticket.ticket_id),
            ticket_data={'priority': 'HIGH'},
        )
        assert result.success is False

    def test_viewer_denied(self, viewer, open_ticket):
        result = UpdateTicket().execute(
            user=viewer,
            ticket_id=str(open_ticket.ticket_id),
            ticket_data={'priority': 'HIGH'},
        )
        assert result.success is False

    def test_nonexistent_ticket_returns_failure(self, manager):
        result = UpdateTicket().execute(
            user=manager,
            ticket_id='00000000-0000-0000-0000-000000000000',
            ticket_data={'priority': 'HIGH'},
        )
        assert result.success is False
        assert 'not found' in result.error.lower()

    def test_status_resolved_sets_resolved_at(self, manager, open_ticket):
        from apps.tickets.models import Ticket
        result = UpdateTicket().execute(
            user=manager,
            ticket_id=str(open_ticket.ticket_id),
            ticket_data={'status': 'RESOLVED', 'resolution_summary': 'Fixed'},
        )
        assert result.success is True
        open_ticket.refresh_from_db()
        assert open_ticket.resolved_at is not None
