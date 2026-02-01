from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.tickets.models import Ticket, TicketCategory, TicketType

User = get_user_model()


class FrontendTicketReadPermissionsTest(TestCase):
    """Frontend TicketsView read permission tests."""

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

        category = TicketCategory.objects.create(name='General')
        ticket_type = TicketType.objects.create(
            name='Issue',
            category=category
        )

        cls.ticket_by_technician = Ticket.objects.create(
            title='Tech Ticket',
            category=category,
            ticket_type=ticket_type,
            created_by=cls.technician,
        )

        cls.ticket_by_manager = Ticket.objects.create(
            title='Manager Ticket',
            category=category,
            ticket_type=ticket_type,
            created_by=cls.manager,
        )

    def test_viewer_sees_zero_tickets(self):
        """VIEWER should not see any tickets."""
        self.client.force_login(self.viewer)

        response = self.client.get(reverse('frontend:tickets'))
        self.assertEqual(response.status_code, 200)

        tickets = list(response.context['tickets'])
        self.assertEqual(tickets, [])

    def test_technician_sees_only_own_tickets(self):
        """TECHNICIAN sees only tickets they created or are assigned to."""
        self.client.force_login(self.technician)

        response = self.client.get(reverse('frontend:tickets'))
        self.assertEqual(response.status_code, 200)

        tickets = list(response.context['tickets'])
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].id, self.ticket_by_technician.id)
