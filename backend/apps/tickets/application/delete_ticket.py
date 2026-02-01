"""
Ticket deletion use case.

Application layer for deleting tickets.
Handles authorization and transaction boundaries.
Authorization is enforced via domain service with strict RBAC.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from apps.tickets.domain.services.ticket_authority import (
    assert_can_delete,
    can_delete,
)


@dataclass
class DeleteTicketResult:
    """Result of ticket deletion use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Dict) -> 'DeleteTicketResult':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'DeleteTicketResult':
        return cls(success=False, error=error)


class DeleteTicket:
    """
    Use case for deleting a ticket.

    Business Rules:
    - Authorization check via domain service
    - Cascades deletion of related records
    - Technician can only delete tickets assigned to them

    Input (via execute):
        user: User - User performing the deletion
        ticket_id: UUID - ID of ticket to delete
        idempotency_key: Optional[str] - Key to prevent duplicate deletions

    Output:
        DeleteTicketResult with deletion confirmation or error

    Usage:
        result = DeleteTicket().execute(
            user=request.user,
            ticket_id=ticket_uuid,
            idempotency_key="delete-ticket-123"
        )

        if result.success:
            print(f"Deleted ticket")
        else:
            print(f"Error: {result.error}")
    """

    def execute(
        self,
        user: Any,
        ticket_id: str,
        idempotency_key: Optional[str] = None,
    ) -> DeleteTicketResult:
        """
        Execute ticket deletion use case.

        Args:
            user: User performing the deletion
            ticket_id: UUID string of ticket to delete
            idempotency_key: Optional key to prevent duplicate deletions

        Returns:
            DeleteTicketResult with deletion confirmation or error
        """
        from django.db import transaction
        from apps.tickets.models import (
            Ticket, TicketAttachment, TicketComment,
            TicketHistory, TicketEscalation, TicketSatisfaction,
        )

        # Get ticket
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_id)
        except Ticket.DoesNotExist:
            return DeleteTicketResult.fail("Ticket not found")

        # Authorization check - raises AuthorizationError if not authorized
        try:
            assert_can_delete(user, ticket)
        except Exception as e:
            return DeleteTicketResult.fail(str(e))

        # Delete with cascade
        with transaction.atomic():
            # Delete related records
            TicketAttachment.objects.filter(ticket=ticket).delete()
            TicketComment.objects.filter(ticket=ticket).delete()
            TicketHistory.objects.filter(ticket=ticket).delete()
            TicketEscalation.objects.filter(ticket=ticket).delete()
            TicketSatisfaction.objects.filter(ticket=ticket).delete()

            # Clear related tickets
            ticket.related_tickets.clear()

            # Update child tickets
            Ticket.objects.filter(parent_ticket=ticket).update(parent_ticket=None)

            # Delete the ticket
            ticket_id_str = str(ticket.ticket_id)
            ticket.delete()

        return DeleteTicketResult.ok(
            data={
                'ticket_id': ticket_id_str,
                'message': 'Ticket deleted successfully',
            }
        )


class CanDeleteTicket:
    """
    Simple check if user can delete a ticket.
    
    Returns:
        bool: True if user can delete the ticket
    """
    
    def check(self, user: Any, ticket_id: str) -> bool:
        """
        Check if user can delete the ticket.
        
        Args:
            user: User attempting to delete
            ticket_id: UUID of ticket to delete
            
        Returns:
            bool: True if authorized, False otherwise
        """
        from apps.tickets.models import Ticket
        
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_id)
        except Ticket.DoesNotExist:
            return False
        
        return can_delete(user, ticket)

