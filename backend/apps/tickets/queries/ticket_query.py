# Ticket query class for read-only database operations.
# This class follows CQRS principles - only reads data, never mutates state.

from django.db.models import QuerySet
from typing import List, Dict, Any, Optional


class TicketQuery:
    """
    Query class for Ticket model.
    All methods are read-only - they NEVER mutate state.
    Returns querysets/dictionaries, never HttpResponse.
    """
    
    @staticmethod
    def get_all() -> QuerySet:
        """
        Get all tickets with related data.
        Returns: QuerySet of Ticket objects
        """
        from apps.tickets.models import Ticket
        return Ticket.objects.select_related(
            'created_by', 'assigned_to', 'category', 'ticket_type'
        ).order_by('-created_at')[:50]
    
    @staticmethod
    def get_by_id(ticket_id: int) -> Optional['Ticket']:
        """
        Get a single ticket by ID.
        Args:
            ticket_id: The ID of the ticket to retrieve
        Returns: Ticket object or None
        """
        from apps.tickets.models import Ticket
        from django.shortcuts import get_object_or_404
        try:
            return get_object_or_404(
                Ticket.objects.select_related('created_by', 'assigned_to'),
                id=ticket_id
            )
        except (Ticket.DoesNotExist, ValueError):
            return None
    
    @staticmethod
    def get_with_details(ticket_id: int) -> Optional['Ticket']:
        """
        Get a ticket with all details (category, type, assigned_to, created_by).
        Args:
            ticket_id: The ID of the ticket to retrieve
        Returns: Ticket object with prefetched relations or None
        """
        from apps.tickets.models import Ticket
        from django.shortcuts import get_object_or_404
        try:
            return get_object_or_404(
                Ticket.objects.select_related('category', 'ticket_type', 'assigned_to', 'created_by'),
                id=ticket_id
            )
        except (Ticket.DoesNotExist, ValueError):
            return None
    
    @staticmethod
    def get_categories() -> QuerySet:
        """
        Get all active ticket categories.
        Returns: QuerySet of TicketCategory objects
        """
        from apps.tickets.models import TicketCategory
        return TicketCategory.objects.filter(is_active=True)
    
    @staticmethod
    def get_types() -> QuerySet:
        """
        Get all active ticket types.
        Returns: QuerySet of TicketType objects
        """
        from apps.tickets.models import TicketType
        return TicketType.objects.filter(is_active=True)
    
    @staticmethod
    def get_status_choices() -> List[tuple]:
        """
        Get ticket status choices.
        Returns: List of (value, display_name) tuples
        """
        from apps.tickets.models import Ticket
        return Ticket.STATUS_CHOICES
    
    @staticmethod
    def get_priority_choices() -> List[tuple]:
        """
        Get ticket priority choices.
        Returns: List of (value, display_name) tuples
        """
        from apps.tickets.models import Ticket
        return Ticket.PRIORITY_CHOICES
    
    @staticmethod
    def get_active_users() -> QuerySet:
        """
        Get all active users (for assignment selection).
        Returns: QuerySet of User objects
        """
        from apps.users.models import User
        return User.objects.filter(is_active=True)
    
    @staticmethod
    def get_for_dashboard() -> Dict[str, Any]:
        """
        Get ticket statistics for dashboard.
        Returns: Dictionary with ticket counts by status
        """
        from apps.tickets.models import Ticket
        return {
            'total': Ticket.objects.count(),
            'new': Ticket.objects.filter(status='NEW').count(),
            'open': Ticket.objects.filter(status='OPEN').count(),
            'in_progress': Ticket.objects.filter(status='IN_PROGRESS').count(),
            'resolved': Ticket.objects.filter(status='RESOLVED').count(),
            'closed': Ticket.objects.filter(status='CLOSED').count(),
        }
    
    @staticmethod
    def get_open_tickets() -> QuerySet:
        """
        Get all open tickets (for user assignment).
        Returns: QuerySet of Ticket objects
        """
        from apps.tickets.models import Ticket
        return Ticket.objects.filter(
            status__in=['NEW', 'OPEN', 'IN_PROGRESS']
        ).select_related('category', 'assigned_to', 'created_by').order_by('-priority', '-created_at')
    
    @staticmethod
    def get_by_requester(requester_id: int) -> QuerySet:
        """
        Get tickets by requester ID.
        Args:
            requester_id: The ID of the user who requested the tickets
        Returns: QuerySet of Ticket objects
        """
        from apps.tickets.models import Ticket
        return Ticket.objects.filter(
            requester_id=requester_id
        ).select_related('category', 'ticket_type', 'assigned_to').order_by('-created_at')
    
    @staticmethod
    def get_by_assignee(assignee_id: int) -> QuerySet:
        """
        Get tickets by assignee ID.
        Args:
            assignee_id: The ID of the user assigned to the tickets
        Returns: QuerySet of Ticket objects
        """
        from apps.tickets.models import Ticket
        return Ticket.objects.filter(
            assigned_to_id=assignee_id
        ).select_related('category', 'ticket_type', 'created_by').order_by('-created_at')

