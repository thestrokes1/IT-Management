"""
Use case for assigning a ticket to another user.

Authorization is enforced via domain service with strict RBAC.
Only users with can_assign permission can assign tickets to others.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from apps.tickets.domain.services.ticket_authority import (
    can_assign,
    assert_can_assign,
)
from apps.core.domain.authorization import AuthorizationError


@dataclass
class AssignTicketResult:
    """Result of ticket assignment use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Dict) -> 'AssignTicketResult':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'AssignTicketResult':
        return cls(success=False, error=error)


class AssignTicket:
    """
    Use case for assigning a ticket to another user.
    
    Business Rules:
    - Only users with can_assign permission can assign tickets
    - SUPERADMIN, MANAGER, IT_ADMIN can assign any ticket
    - TECHNICIAN cannot assign tickets to others
    - Assignee can be any active user
    
    Input (via execute):
        user: User - User performing the assignment
        ticket_id: UUID - ID of ticket to assign
        assignee_id: int - User ID of the assignee
        
    Output:
        AssignTicketResult with assignment confirmation or error
        
    Usage:
        result = AssignTicket().execute(
            user=request.user,
            ticket_id=ticket_uuid,
            assignee_id=target_user.id
        )
        
        if result.success:
            print(f"Assigned ticket: {result.data['title']}")
        else:
            print(f"Error: {result.error}")
    """

    def execute(
        self,
        user: Any,
        ticket_id: str,
        assignee_id: int,
    ) -> AssignTicketResult:
        """
        Execute ticket assignment use case.

        Args:
            user: User performing the assignment
            ticket_id: UUID string of ticket to assign
            assignee_id: User ID of the assignee

        Returns:
            AssignTicketResult with assignment confirmation or error
        """
        from apps.tickets.models import Ticket
        from apps.users.models import User
        from django.utils import timezone
        
        # Get ticket
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_id)
        except Ticket.DoesNotExist:
            return AssignTicketResult.fail("Ticket not found")

        # Get assignee
        try:
            assignee = User.objects.get(id=assignee_id)
        except User.DoesNotExist:
            return AssignTicketResult.fail("Assignee not found")

        # Authorization check - raises AuthorizationError if not authorized
        try:
            assert_can_assign(user, ticket, assignee)
        except AuthorizationError as e:
            return AssignTicketResult.fail(str(e))

        # Store old assignee for event
        old_assignee = ticket.assigned_to
        old_assignment_status = ticket.assignment_status
        
        # Perform assignment
        ticket.assigned_to = assignee
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
            assignee_id=assignee.id,
            assignee_username=assignee.username,
            assigner_id=user.id,
            assigner_username=user.username,
        )

        old_assignee_name = old_assignee.username if old_assignee else "Unassigned"

        return AssignTicketResult.ok(
            data={
                'ticket_id': str(ticket.ticket_id),
                'title': ticket.title,
                'previous_assignee': old_assignee_name,
                'new_assignee': assignee.username,
                'new_assignee_id': assignee.id,
                'previous_assignment_status': old_assignment_status,
                'new_assignment_status': ticket.assignment_status,
                'status': ticket.status,
                'message': f"Ticket assigned from {old_assignee_name} to {assignee.username}",
            }
        )


class UnassignTicket:
    """
    Use case for unassigning a ticket.
    
    Business Rules:
    - Only users with can_unassign permission can unassign tickets
    - SUPERADMIN, MANAGER, IT_ADMIN can unassign any ticket
    - TECHNICIAN cannot unassign tickets
    
    Input (via execute):
        user: User - User performing the unassignment
        ticket_id: UUID - ID of ticket to unassign
        
    Output:
        AssignTicketResult with unassignment confirmation or error
    """

    def execute(
        self,
        user: Any,
        ticket_id: str,
    ) -> AssignTicketResult:
        """
        Execute ticket unassignment use case.

        Args:
            user: User performing the unassignment
            ticket_id: UUID string of ticket to unassign

        Returns:
            AssignTicketResult with unassignment confirmation or error
        """
        from apps.tickets.models import Ticket
        from django.utils import timezone
        
        # Get ticket
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_id)
        except Ticket.DoesNotExist:
            return AssignTicketResult.fail("Ticket not found")

        # Check if ticket is already unassigned
        if ticket.assigned_to is None:
            return AssignTicketResult.fail("Ticket is already unassigned")

        # Authorization check
        from apps.tickets.domain.services.ticket_authority import (
            assert_can_unassign,
        )
        try:
            assert_can_unassign(user, ticket)
        except AuthorizationError as e:
            return AssignTicketResult.fail(str(e))

        # Store old assignee for event
        old_assignee = ticket.assigned_to
        old_assignee_name = old_assignee.username if old_assignee else "Unassigned"
        
        # Perform unassignment
        ticket.assigned_to = None
        ticket.assignment_status = 'UNASSIGNED'
        ticket.updated_by = user
        ticket.save()

        # Emit domain event
        from apps.tickets.domain.events import emit_ticket_unassigned
        emit_ticket_unassigned(
            ticket_id=ticket.id,
            ticket_title=ticket.title,
            actor=user,
            unassigned_user_id=old_assignee.id if old_assignee else None,
            unassigned_username=old_assignee_name,
        )

        return AssignTicketResult.ok(
            data={
                'ticket_id': str(ticket.ticket_id),
                'title': ticket.title,
                'unassigned_from': old_assignee_name,
                'new_assignment_status': ticket.assignment_status,
                'status': ticket.status,
                'message': f"Ticket unassigned from {old_assignee_name}",
            }
        )

