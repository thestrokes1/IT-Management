"""
Ticket update use case.

Application layer for updating tickets.
Handles authorization and transaction boundaries.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from apps.core.domain.authorization import AuthorizationError
from apps.tickets.domain.services.ticket_authority import assert_can_update_ticket


@dataclass
class UpdateTicketResult:
    """Result of ticket update use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    
    @classmethod
    def ok(cls, data: Dict) -> 'UpdateTicketResult':
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: str) -> 'UpdateTicketResult':
        return cls(success=False, error=error)


class UpdateTicket:
    """
    Use case for updating an existing ticket.
    
    Business Rules:
    - Authorization check via domain service
    - Supports partial updates
    
    Input (via execute):
        user: User - User performing the update
        ticket_id: UUID - ID of ticket to update
        ticket_data: Dict - Fields to update
        idempotency_key: Optional[str] - Key to prevent duplicate updates
    
    Output:
        UpdateTicketResult with updated ticket details or error
    
    Usage:
        result = UpdateTicket().execute(
            user=request.user,
            ticket_id=ticket_uuid,
            ticket_data={'status': 'IN_PROGRESS'},
            idempotency_key="update-ticket-123"
        )
        
        if result.success:
            print(f"Updated ticket {result.data['ticket_id']}")
        else:
            print(f"Error: {result.error}")
    """
    
    def execute(
        self,
        user: Any,
        ticket_id: str,
        ticket_data: Dict,
        idempotency_key: Optional[str] = None,
    ) -> UpdateTicketResult:
        """
        Execute ticket update use case.
        
        Args:
            user: User performing the update
            ticket_id: UUID string of ticket to update
            ticket_data: Dictionary with fields to update
            idempotency_key: Optional key to prevent duplicate updates
            
        Returns:
            UpdateTicketResult with updated ticket details or error
        """
        from apps.tickets.models import Ticket
        from django.utils import timezone
        
        # Get ticket
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_id)
        except Ticket.DoesNotExist:
            return UpdateTicketResult.fail("Ticket not found")
        
        # Authorization check - raises AuthorizationError if not authorized
        assert_can_update_ticket(user, ticket)
        
        # Update fields
        allowed_fields = {
            'title', 'description', 'priority', 'status',
            'impact', 'urgency', 'category_id', 'ticket_type_id',
            'resolution_summary', 'assigned_team',
        }
        
        for field, value in ticket_data.items():
            if field in allowed_fields:
                if field.endswith('_id'):
                    # Handle foreign key fields
                    setattr(ticket, field, value)
                else:
                    setattr(ticket, field, value)
        
        # Handle status-specific logic
        if 'status' in ticket_data:
            new_status = ticket_data['status']
            if new_status == 'RESOLVED':
                ticket.resolved_at = timezone.now()
                if not ticket.resolution_time and ticket.created_at:
                    ticket.resolution_time = ticket.resolved_at - ticket.created_at
            elif new_status == 'CLOSED':
                ticket.closed_at = timezone.now()
        
        ticket.updated_by = user
        ticket.save()
        
        return UpdateTicketResult.ok(
            data={
                'ticket_id': str(ticket.ticket_id),
                'title': ticket.title,
                'status': ticket.status,
                'updated_at': ticket.updated_at.isoformat(),
            }
        )

