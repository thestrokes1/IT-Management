"""
Ticket assignment use case.

Application layer for assigning tickets.
Handles authorization and transaction boundaries.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from apps.tickets.domain.services.ticket_authority import assert_can_assign_ticket


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
    Use case for assigning a ticket to a user.

    Business Rules:
    - Authorization check via domain service
    - Technician can only assign to themselves

    Input (via execute):
        user: User - User performing the assignment
        ticket_id: UUID - ID of ticket to assign
        assignee_id: int - User ID to assign the ticket to
        idempotency_key: Optional[str] - Key to prevent duplicate assignments

    Output:
        AssignTicketResult with assignment confirmation or error

    Usage:
        result = AssignTicket().execute(
            user=request.user,
            ticket_id=ticket_uuid,
            assignee_id=user_id,
            idempotency_key="assign-ticket-123"
        )

        if result.success:
            print(f"Assigned ticket to {result.data['assignee']}")
        else:
            print(f"Error: {result.error}")
    """

    def execute(
        self,
        user: Any,
        ticket_id: str,
        assignee_id: int,
        idempotency_key: Optional[str] = None,
    ) -> AssignTicketResult:
        """
        Execute ticket assignment use case.

        Args:
            user: User performing the assignment
            ticket_id: UUID string of ticket to assign
            assignee_id: User ID to assign the ticket to
            idempotency_key: Optional key to prevent duplicate assignments

        Returns:
            AssignTicketResult with assignment confirmation or error
        """
        from apps.tickets.models import Ticket
        from apps.users.models import User

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
        assert_can_assign_ticket(user, ticket, assignee)

        # Assign the ticket
        ticket.assigned_to = assignee
        ticket.updated_by = user
        ticket.save()

        return AssignTicketResult.ok(
            data={
                'ticket_id': str(ticket.ticket_id),
                'assignee': assignee.username,
                'assignee_id': assignee.id,
                'message': f"Ticket assigned to {assignee.username}",
            }
        )


class AssignTicketToTeam:
    """
    Use case for assigning a ticket to a team.

    Business Rules:
    - Authorization check via domain service

    Input (via execute):
        user: User - User performing the assignment
        ticket_id: UUID - ID of ticket to assign
        team: str - Team name to assign the ticket to
        idempotency_key: Optional[str] - Key to prevent duplicate assignments

    Output:
        AssignTicketResult with assignment confirmation or error
    """

    def execute(
        self,
        user: Any,
        ticket_id: str,
        team: str,
        idempotency_key: Optional[str] = None,
    ) -> AssignTicketResult:
        """
        Execute ticket team assignment use case.

        Args:
            user: User performing the assignment
            ticket_id: UUID string of ticket to assign
            team: Team name to assign the ticket to
            idempotency_key: Optional key to prevent duplicate assignments

        Returns:
            AssignTicketResult with assignment confirmation or error
        """
        from apps.tickets.models import Ticket

        # Get ticket
        try:
            ticket = Ticket.objects.get(ticket_id=ticket_id)
        except Ticket.DoesNotExist:
            return AssignTicketResult.fail("Ticket not found")

        # For team assignment, check update permission (no specific assignee)
        from apps.tickets.domain.services.ticket_authority import assert_can_update_ticket
        assert_can_update_ticket(user, ticket)

        # Assign to team
        ticket.assigned_to = None
        ticket.assigned_team = team
        ticket.updated_by = user
        ticket.save()

        return AssignTicketResult.ok(
            data={
                'ticket_id': str(ticket.ticket_id),
                'team': team,
                'message': f"Ticket assigned to team: {team}",
            }
        )

