"""
Ticket Query Service Layer for IT Management Platform.

Provides high-level ticket fetching operations following Clean Architecture principles.
Separates business logic from view layer for better maintainability and testing.

Usage:
    from apps.tickets.services.ticket_query_service import TicketQueryService
    
    service = TicketQueryService()
    tickets = service.get_user_tickets(
        user=request.user,
        status_filter='OPEN',
        priority_filter='HIGH'
    )
"""

from typing import Optional, List, Dict, Any, Tuple
from django.db.models import QuerySet, Q, Count, Case, When, IntegerField
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator, Page

from apps.tickets.models import Ticket


class TicketQueryService:
    """
    Service layer for fetching and filtering tickets.
    
    Implements Clean Architecture by:
    - Encapsulating ticket fetching logic in a service class
    - Handling RBAC enforcement within the service
    - Providing clean interface for view layer
    - Supporting filtering, pagination, and statistics
    
    RBAC Rules:
    - Admins (SUPERADMIN, IT_ADMIN, MANAGER): Can see all tickets they created or were assigned
    - Regular users: Can only see tickets they created or were assigned
    - Viewers: Limited view based on assignment
    
    Attributes:
        default_page_size: Default number of tickets per page (10)
        max_page_size: Maximum tickets per page (50)
    """
    
    default_page_size = 10
    max_page_size = 50
    
    def get_user_tickets(
        self,
        *,
        user,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        page: int = 1,
        page_size: Optional[int] = None,
        order_by: str = '-created_at'
    ) -> Dict[str, Any]:
        """
        Fetch tickets for a user with optional filtering and pagination.
        
        This method retrieves tickets where:
        1. The user created the ticket (ticket.created_by = user)
        2. OR the user was assigned the ticket (ticket.assigned_to = user)
        
        Plus optional status and priority filters.
        
        Args:
            user: The authenticated user making the request
            status_filter: Optional status to filter by (e.g., 'OPEN', 'RESOLVED')
            priority_filter: Optional priority to filter by (e.g., 'HIGH', 'CRITICAL')
            page: Page number for pagination (1-indexed)
            page_size: Number of tickets per page (default: 10, max: 50)
            order_by: Field to order by (default: '-created_at' for newest first)
        
        Returns:
            Dictionary containing:
            - 'tickets': List of ticket dictionaries with full details
            - 'page': Current page number
            - 'page_size': Items per page
            - 'total_count': Total number of matching tickets
            - 'total_pages': Total number of pages
            - 'has_next': Whether there is a next page
            - 'has_previous': Whether there is a previous page
        
        Raises:
            ValueError: If page_size exceeds max_page_size
        
        Example:
            >>> service = TicketQueryService()
            >>> result = service.get_user_tickets(
            ...     user=request.user,
            ...     status_filter='OPEN',
            ...     priority_filter='HIGH',
            ...     page=1,
            ...     page_size=10
            ... )
            >>> result['tickets']  # List of ticket dicts
            >>> result['total_count']  # Total matching tickets
        """
        # Validate and set page size
        if page_size is None:
            page_size = self.default_page_size
        page_size = min(page_size, self.max_page_size)
        page = max(1, page)  # Ensure page is at least 1
        
        # Build the base query for tickets created OR assigned to user
        # Using Q objects for OR logic
        base_query = Q(created_by=user) | Q(assigned_to=user)
        
        # Apply status filter if provided
        if status_filter:
            base_query &= Q(status=status_filter)
        
        # Apply priority filter if provided
        if priority_filter:
            base_query &= Q(priority=priority_filter)
        
        # Fetch tickets with optimized queries
        # select_related reduces database hits for foreign keys
        tickets_qs = Ticket.objects.filter(base_query).select_related(
            'created_by', 'assigned_to', 'category', 'updated_by'
        ).order_by(order_by)
        
        # Get total count before pagination
        total_count = tickets_qs.count()
        
        # Create paginator
        paginator = Paginator(tickets_qs, page_size)
        
        # Get the requested page
        try:
            page_obj = paginator.page(page)
        except Exception:
            # If page is out of range, return first page
            page_obj = paginator.page(1)
            page = 1
        
        # Convert tickets to dictionaries for template rendering
        tickets_list = [
            self._ticket_to_dict(ticket) for ticket in page_obj.object_list
        ]
        
        return {
            'tickets': tickets_list,
            'page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    
    def get_user_tickets_queryset(
        self,
        *,
        user,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> QuerySet:
        """
        Get a queryset of tickets for a user (for simple use cases).
        
        This is a simpler interface for when you just need the QuerySet
        rather than the full pagination dictionary.
        
        Args:
            user: The authenticated user
            status_filter: Optional status to filter by
            priority_filter: Optional priority to filter by
            limit: Optional limit to number of tickets
        
        Returns:
            Django QuerySet of tickets
        
        Example:
            >>> service = TicketQueryService()
            >>> tickets = service.get_user_tickets_queryset(
            ...     user=request.user,
            ...     status_filter='OPEN'
            ... )[:5]
        """
        base_query = Q(created_by=user) | Q(assigned_to=user)
        
        if status_filter:
            base_query &= Q(status=status_filter)
        
        if priority_filter:
            base_query &= Q(priority=priority_filter)
        
        qs = Ticket.objects.filter(base_query).select_related(
            'created_by', 'assigned_to', 'category', 'updated_by'
        ).order_by('-created_at')
        
        if limit:
            return qs[:limit]
        return qs
    
    def get_user_ticket_stats(
        self,
        *,
        user
    ) -> Dict[str, int]:
        """
        Calculate statistics for a user's tickets.
        
        Returns counts for:
        - Total tickets (created or assigned)
        - Created tickets count
        - Assigned tickets count
        - Resolved tickets count
        - Open tickets count
        - Can reopen count (resolved or closed)
        
        Args:
            user: The authenticated user
        
        Returns:
            Dictionary with statistics counts
        
        Example:
            >>> service = TicketQueryService()
            >>> stats = service.get_user_ticket_stats(user=request.user)
            >>> stats['total']  # Total tickets
            >>> stats['resolved']  # Resolved tickets count
        """
        # Base query for user's tickets
        user_tickets_query = Q(created_by=user) | Q(assigned_to=user)
        
        # Calculate all statistics
        total = Ticket.objects.filter(user_tickets_query).distinct().count()
        created = Ticket.objects.filter(created_by=user).count()
        assigned = Ticket.objects.filter(assigned_to=user).count()
        resolved = Ticket.objects.filter(
            user_tickets_query,
            status='RESOLVED'
        ).distinct().count()
        open_count = Ticket.objects.filter(
            user_tickets_query,
            status__in=['NEW', 'OPEN', 'IN_PROGRESS']
        ).distinct().count()
        can_reopen = Ticket.objects.filter(
            user_tickets_query,
            status__in=['RESOLVED', 'CLOSED']
        ).distinct().count()
        
        return {
            'total': total,
            'created': created,
            'assigned': assigned,
            'resolved': resolved,
            'open': open_count,
            'can_reopen': can_reopen,
        }
    
    def can_user_reopen_ticket(
        self,
        *,
        user
    ) -> bool:
        """
        Check if a user has permission to reopen tickets.
        
        RBAC: Only admins (SUPERADMIN, IT_ADMIN, MANAGER) can reopen tickets.
        
        Args:
            user: The authenticated user
        
        Returns:
            Boolean indicating if user can reopen tickets
        """
        if not user:
            return False
        
        user_role = getattr(user, 'role', 'VIEWER') if user else None
        
        return user.is_superuser or user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
    
    def get_available_filters(
        self,
        *,
        user
    ) -> Dict[str, List[str]]:
        """
        Get available filter options based on user's tickets.
        
        Returns status and priority choices that actually exist
        in the user's tickets (for populating filter dropdowns).
        
        Args:
            user: The authenticated user
        
        Returns:
            Dictionary with 'statuses' and 'priorities' lists
        
        Example:
            >>> service = TicketQueryService()
            >>> filters = service.get_available_filters(user=request.user)
            >>> filters['statuses']  # ['OPEN', 'RESOLVED', ...]
            >>> filters['priorities']  # ['HIGH', 'MEDIUM', ...]
        """
        user_tickets_query = Q(created_by=user) | Q(assigned_to=user)
        
        # Get distinct statuses from user's tickets
        # Remove duplicates using set() to ensure uniqueness, then sort
        statuses = sorted(set(
            Ticket.objects.filter(user_tickets_query)
            .values_list('status', flat=True)
            .distinct()
        ))
        
        # Get distinct priorities from user's tickets
        # Remove duplicates using set() to ensure uniqueness, then sort
        priorities = sorted(set(
            Ticket.objects.filter(user_tickets_query)
            .values_list('priority', flat=True)
            .distinct()
        ))
        
        return {
            'statuses': statuses,
            'priorities': priorities,
        }
    
    def _ticket_to_dict(self, ticket: Ticket) -> Dict[str, Any]:
        """
        Convert a Ticket model instance to a dictionary for template rendering.
        
        Args:
            ticket: The Ticket model instance
        
        Returns:
            Dictionary with ticket data for templates
        """
        return {
            'id': ticket.id,
            'title': ticket.title,
            'status': ticket.status,
            'priority': ticket.priority,
            'category': ticket.category.name if ticket.category else None,
            'created_at': ticket.created_at,
            'updated_at': ticket.updated_at,
            'created_by': {
                'id': ticket.created_by.id if ticket.created_by else None,
                'username': ticket.created_by.username if ticket.created_by else 'System',
            },
            'updated_by': {
                'id': ticket.updated_by.id if ticket.updated_by else None,
                'username': ticket.updated_by.username if ticket.updated_by else None,
            },
            'assigned_to': {
                'id': ticket.assigned_to.id if ticket.assigned_to else None,
                'username': ticket.assigned_to.username if ticket.assigned_to else None,
            },
            'status_display': ticket.get_status_display(),
            'priority_display': ticket.get_priority_display(),
        }
