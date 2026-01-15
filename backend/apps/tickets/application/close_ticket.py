"""
Ticket close use case.

Application layer for closing tickets.
Handles authorization and transaction boundaries.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from apps.tickets.domain.services.ticket_authority import assert_can_close_ticket


@dataclass
class CloseTicketResult:
    """Result of ticket close use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Dict) -> 'CloseTicketResult':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'CloseTicketResult':
        return cls(success=False, error=error)


class CloseTicket:
    """
    Use case for closing a ticket.

    Business Rules:
    - Authorization check via domain service
    - Same rules as UPDATE permission

    Input (via execute):
        user: User - User performing the close
        ticket_id: UUID - ID of ticket to close
        idempotency_key: Optional[str] - Key to prevent duplicate closes

    Output:
        CloseTicketResult with close confirmation or error

    Usage:
        result = CloseTicket().execute(
            user=request.user,
            ticket_id=ticket_uuid,
            idempotency_key="close-ticket-123"
        )

        if result.success:
            print(f"Closed ticket")
        else:
            print(f"Error: {result.error}")
    """

    def execute(
        self,
        user: Any,
        ticket_id: str,
        idempotency_key: Optional[str] = None,
    ) -> CloseTicketResult:
        """
        Execute ticket close use case.

        Args:
            user: User performing the close
            ticket_id: UUID string of ticket to close
            idempotency_key: Optional key to prevent duplicate closes

        Returns:
            CloseTicketResult with close confirmation or error
        """
        from django.utils import timezone
        from apps.tickets.models import Ticket

        # Get ticket
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_id)
        except Ticket.DoesNotExist:
            return CloseTicketResult.fail("Ticket not found")

        # Authorization check - raises AuthorizationError if not authorized
        assert_can_close_ticket(user, ticket)

        # Close the ticket
        ticket.status = 'CLOSED'
        ticket.closed_at = timezone.now()
        ticket.updated_by = user
        ticket.save()

        return CloseTicketResult.ok(
            data={
                'ticket_id': str(ticket.ticket_id),
                'status': ticket.status,
                'closed_at': ticket.closed_at.isoformat(),
                'message': 'Ticket closed successfully',
            }
        )

