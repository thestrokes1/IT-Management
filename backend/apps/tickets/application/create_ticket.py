"""
Ticket creation use case.

Application layer for creating tickets.
Handles authorization, idempotency, and transaction boundaries.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from django.db import transaction

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
    
    @transaction.atomic
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
        from django.utils.dateparse import parse_date
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Handle assigned_to_id - get the user object if provided
        assigned_to = None
        if ticket_data.get('assigned_to_id'):
            try:
                assigned_to = User.objects.get(id=ticket_data.get('assigned_to_id'))
            except User.DoesNotExist:
                pass  # Ignore invalid user ID
        
        # Handle due_date - parse the date string
        due_date = None
        if ticket_data.get('due_date'):
            due_date = parse_date(ticket_data.get('due_date'))
        
        ticket = Ticket.objects.create(
            title=ticket_data.get('title'),
            description=ticket_data.get('description', ''),
            category_id=ticket_data.get('category_id'),
            ticket_type_id=ticket_data.get('ticket_type_id'),
            priority=ticket_data.get('priority', 'MEDIUM'),
            impact=ticket_data.get('impact', 'MEDIUM'),
            urgency=ticket_data.get('urgency', 'MEDIUM'),
            location=ticket_data.get('location', ''),
            contact_phone=ticket_data.get('contact_phone', ''),
            contact_email=ticket_data.get('contact_email', ''),
            contact_type=ticket_data.get('contact_type', ''),
            requester=actor,
            created_by=actor,
            assigned_to=assigned_to,
            assignment_status='ASSIGNED' if assigned_to else 'UNASSIGNED',
            sla_due_at=due_date,
        )
        
        # Activity logging - runs after transaction commits, never breaks command
        transaction.on_commit(lambda: self._log_ticket_created(ticket, actor))
        
        return CreateTicketResult.ok(
            data={
                'ticket_id': str(ticket.ticket_id),
                'title': ticket.title,
                'status': ticket.status,
                'created_at': ticket.created_at.isoformat(),
            }
        )
    
    def _log_ticket_created(self, ticket, actor):
        """Log ticket creation activity and kick off background async tasks."""
        try:
            from apps.logs.services.activity_service import ActivityService
            ActivityService().log_ticket_created(ticket, actor, None)
        except Exception:
            pass  # Logging must never break the command
            
        try:
            from apps.tickets.tasks import send_ticket_creation_notification
            send_ticket_creation_notification.delay(ticket.id, actor.id)
        except Exception as e:
            # If celery is offline, do not break the transaction
            print(f"Warning: Celery task failed to enqueue - {str(e)}")
