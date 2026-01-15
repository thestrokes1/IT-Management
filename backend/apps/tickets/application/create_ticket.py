"""
Ticket creation use case.

Application layer for creating tickets.
Handles authorization, idempotency, and transaction boundaries.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from apps.core.domain.authorization import AuthorizationError
from apps.tickets.domain.services.ticket_authority import can_create_ticket


@dataclass
class CreateTicketResult:
    """Result of ticket creation use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    
    @classmethod
    def ok(cls, data: Dict) -> 'CreateTicketResult':
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: str) -> 'CreateTicketResult':
        return cls(success=False, error=error)


class CreateTicket:
    """
    Use case for creating a new ticket.
    
    Business Rules:
    - Only users with permission can create tickets (VIEWER denied)
    - Supports idempotency via idempotency_key
    
    Input (via execute):
        actor: User - User creating the ticket
        ticket_data: Dict - Ticket creation data
        idempotency_key: Optional[str] - Key to prevent duplicate creation
    
    Output:
        CreateTicketResult with ticket details or error
    
    Usage:
        result = CreateTicket().execute(
            actor=request.user,
            ticket_data={'title': 'Issue', 'description': '...'},
            idempotency_key="create-ticket-123"
        )
        
        if result.success:
            print(f"Created ticket {result.data['ticket_id']}")
        else:
            print(f"Error: {result.error}")
    """
    
    def execute(
        self,
        actor: Any,
        ticket_data: Dict,
        idempotency_key: Optional[str] = None,
    ) -> CreateTicketResult:
        """
        Execute ticket creation use case.
        
        Args:
            actor: User creating the ticket
            ticket_data: Dictionary with ticket creation data
            idempotency_key: Optional key to prevent duplicate creation
            
        Returns:
            CreateTicketResult with ticket details or error
        """
        # Authorization check
        if not can_create_ticket(actor):
            raise AuthorizationError(
                f"User '{actor.username}' is not authorized to create tickets"
            )
        
        # Create the ticket
        from apps.tickets.models import Ticket
        
        ticket = Ticket.objects.create(
            title=ticket_data.get('title'),
            description=ticket_data.get('description', ''),
            category_id=ticket_data.get('category_id'),
            ticket_type_id=ticket_data.get('ticket_type_id'),
            priority=ticket_data.get('priority', 'MEDIUM'),
            impact=ticket_data.get('impact', 'MEDIUM'),
            urgency=ticket_data.get('urgency', 'MEDIUM'),
            requester=actor,
            created_by=actor,
        )
        
        return CreateTicketResult.ok(
            data={
                'ticket_id': str(ticket.ticket_id),
                'title': ticket.title,
                'status': ticket.status,
                'created_at': ticket.created_at.isoformat(),
            }
        )

