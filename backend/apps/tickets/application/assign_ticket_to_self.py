"""
Use case for self-assigning a ticket.

Technician can self-assign to an OPEN, unassigned ticket.
Authorization is enforced via domain service with strict RBAC.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from apps.tickets.domain.services.ticket_authority import (
    can_self_assign,
    can_reassign,
    assert_can_self_assign,
)
from apps.core.domain.authorization import AuthorizationError


@dataclass
class AssignTicketToSelfResult:
    """Result of ticket self-assignment use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Dict) -> 'AssignTicketToSelfResult':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'AssignTicketToSelfResult':
        return cls(success=False, error=error)


class AssignTicketToSelf:
    """
    Use case for a technician to self-assign to a ticket.
    
    Business Rules:
    - Ticket must be OPEN
    - Ticket must not be already assigned
    - Technician can only self-assign to tickets they created
    - Admin roles can always self-assign
    
    Input (via execute):
        user: User - User performing the self-assignment
        ticket_id: UUID - ID of ticket to self-assign
        
    Output:
        AssignTicketToSelfResult with assignment confirmation or error
        
    Usage:
        result = AssignTicketToSelf().execute(
            user=request.user,
            ticket_id=ticket_uuid
        )
        
        if result.success:
            print(f"Self-assigned to ticket: {result.data['title']}")
        else:
            print(f"Error: {result.error}")
    """

    def execute(
        self,
        user: Any,
        ticket_id: str,
    ) -> AssignTicketToSelfResult:
        """
        Execute ticket self-assignment use case.

        Args:
            user: User performing the self-assignment
            ticket_id: UUID string of ticket to self-assign

        Returns:
            AssignTicketToSelfResult with assignment confirmation or error
        """
        from apps.tickets.models import Ticket
        from django.utils import timezone
        
        # Get ticket
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_id)
        except Ticket.DoesNotExist:
            return AssignTicketToSelfResult.fail("Ticket not found")

        # Authorization check - raises AuthorizationError if not authorized
        try:
            assert_can_self_assign(user, ticket)
        except AuthorizationError as e:
            return AssignTicketToSelfResult.fail(str(e))

        # Perform assignment
        old_assignment_status = ticket.assignment_status
        
        ticket.assigned_to = user
        ticket.assignment_status = 'ASSIGNED'
        ticket.updated_by = user
        
        # Update status if ticket is still NEW
        if ticket.status == 'NEW':
            ticket.status = 'OPEN'
        
        ticket.save()

        # Emit domain event
        from apps.tickets.domain.events import emit_ticket_assigned
        emit_ticket_assigned(
            ticket_id=ticket.id,
            ticket_title=ticket.title,
            actor=user,
            assignee_id=user.id,
            assignee_username=user.username,
            assigner_id=user.id,
            assigner_username=user.username,
        )

        return AssignTicketToSelfResult.ok(
            data={
                'ticket_id': str(ticket.ticket_id),
                'title': ticket.title,
                'assigned_to': user.username,
                'assigned_to_id': user.id,
                'previous_assignment_status': old_assignment_status,
                'new_assignment_status': ticket.assignment_status,
                'status': ticket.status,
                'message': f"Ticket self-assigned to {user.username}",
            }
        )


class ReassignTicket:
    """
    Use case for reassigning a ticket to a different user.
    
    Business Rules:
    - Only MANAGER, IT_ADMIN, SUPERADMIN can reassign
    - TECHNICIAN cannot reassign tickets
    
    Input (via execute):
        user: User - User performing the reassignment
        ticket_id: UUID - ID of ticket to reassign
        new_assignee_id: int - User ID to assign the ticket to
        
    Output:
        AssignTicketToSelfResult with reassignment confirmation or error
    """

    def execute(
        self,
        user: Any,
        ticket_id: str,
        new_assignee_id: int,
    ) -> AssignTicketToSelfResult:
        """
        Execute ticket reassignment use case.

        Args:
            user: User performing the reassignment
            ticket_id: UUID string of ticket to reassign
            new_assignee_id: User ID of new assignee

        Returns:
            AssignTicketToSelfResult with reassignment confirmation or error
        """
        from apps.tickets.models import Ticket
        from apps.users.models import User
        
        # Get ticket
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_id)
        except Ticket.DoesNotExist:
            return AssignTicketToSelfResult.fail("Ticket not found")

        # Get new assignee
        try:
            new_assignee = User.objects.get(id=new_assignee_id)
        except User.DoesNotExist:
            return AssignTicketToSelfResult.fail("New assignee not found")

        # Authorization check - TECHNICIAN cannot reassign
        if not can_reassign(user, ticket):
            return AssignTicketToSelfResult.fail(
                "You are not authorized to reassign tickets. "
                "Only MANAGER, IT_ADMIN, or SUPERADMIN can reassign tickets."
            )

        old_assignee = ticket.assigned_to
        
        # Perform reassignment
        ticket.assigned_to = new_assignee
        ticket.assignment_status = 'ASSIGNED'
        ticket.updated_by = user
        ticket.save()

        # Emit domain event
        from apps.tickets.domain.events import emit_ticket_assigned
        emit_ticket_assigned(
            ticket_id=ticket.id,
            ticket_title=ticket.title,
            actor=user,
            assignee_id=new_assignee.id,
            assignee_username=new_assignee.username,
            assigner_id=user.id,
            assigner_username=user.username,
        )

        old_assignee_name = old_assignee.username if old_assignee else "Unassigned"

        return AssignTicketToSelfResult.ok(
            data={
                'ticket_id': str(ticket.ticket_id),
                'title': ticket.title,
                'previous_assignee': old_assignee_name,
                'new_assignee': new_assignee.username,
                'new_assignee_id': new_assignee.id,
                'assignment_status': ticket.assignment_status,
                'message': f"Ticket reassigned from {old_assignee_name} to {new_assignee.username}",
            }
        )


class CanSelfAssignTicket:
    """
    Simple check if user can self-assign to a ticket.
    
    Returns:
        bool: True if user can self-assign the ticket
    """
    
    def check(self, user: Any, ticket_id: str) -> bool:
        """
        Check if user can self-assign the ticket.
        
        Args:
            user: User attempting to self-assign
            ticket_id: UUID of ticket to self-assign
            
        Returns:
            bool: True if authorized, False otherwise
        """
        from apps.tickets.models import Ticket
        
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_id)
        except Ticket.DoesNotExist:
            return False
        
        return can_self_assign(user, ticket)


class CanReassignTicket:
    """
    Simple check if user can reassign a ticket.
    
    Returns:
        bool: True if user can reassign the ticket
    """
    
    def check(self, user: Any, ticket_id: str) -> bool:
        """
        Check if user can reassign the ticket.
        
        Args:
            user: User attempting to reassign
            ticket_id: UUID of ticket to reassign
            
        Returns:
            bool: True if authorized, False otherwise
        """
        from apps.tickets.models import Ticket
        
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_id)
        except Ticket.DoesNotExist:
            return False
        
        return can_reassign(user, ticket)

