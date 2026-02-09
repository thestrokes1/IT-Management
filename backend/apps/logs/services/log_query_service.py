"""
LogQueryService - Query-first design for structured event retrieval.

Provides a clean interface for querying logs without Django ORM logic
in templates. All methods return QuerySets for deferred execution.

Usage:
    service = LogQueryService()
    logs = service.filter_by_category('SECURITY').filter_by_date_range(start, end)
    logs = service.filter_by_actor_role('IT_ADMIN').filter_by_target('ticket', 123)
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from django.db.models import QuerySet, Q
from django.utils import timezone

from apps.logs.models import ActivityLog
from apps.logs.enums import EventCategory


class LogQueryService:
    """
    Service for querying activity logs with a clean, query-first interface.
    
    All filtering methods return the QuerySet for method chaining.
    No ORM logic in templates - use this service in views.
    """
    
    def __init__(self, user=None):
        """
        Initialize the query service.
        
        Args:
            user: Optional user for RBAC filtering
        """
        self._queryset = ActivityLog.objects.all()
        self._user = user
        self._filters_applied: List[str] = []
    
    def all(self) -> QuerySet:
        """Get base queryset with all logs."""
        return self._queryset
    
    def filter_by_category(
        self, 
        categories: Union[str, List[str], EventCategory, List[EventCategory]]
    ) -> 'LogQueryService':
        """
        Filter logs by event category.
        
        Args:
            categories: Single category, list of categories, or EventCategory enum(s)
            
        Returns:
            Self for method chaining
            
        Examples:
            service.filter_by_category('SECURITY')
            service.filter_by_category(['ACTIVITY', 'AUDIT'])
            service.filter_by_category(EventCategory.SECURITY)
        """
        if isinstance(categories, str):
            categories = [categories]
        elif isinstance(categories, EventCategory):
            categories = [categories.value]
        elif isinstance(categories, list):
            # Convert any EventCategory to value
            categories = [c.value if isinstance(c, EventCategory) else c for c in categories]
        
        self._queryset = self._queryset.filter(event_type__in=categories)
        self._filters_applied.append(f"category={categories}")
        return self
    
    def filter_by_actor_role(self, roles: Union[str, List[str]]) -> 'LogQueryService':
        """
        Filter logs by actor role.
        
        Args:
            roles: Single role or list of roles
            
        Returns:
            Self for method chaining
        """
        if isinstance(roles, str):
            roles = [roles]
        
        self._queryset = self._queryset.filter(actor_role__in=roles)
        self._filters_applied.append(f"actor_role={roles}")
        return self
    
    def filter_by_date_range(
        self, 
        start_date: Optional[Union[datetime, date, str]] = None,
        end_date: Optional[Union[datetime, date, str]] = None
    ) -> 'LogQueryService':
        """
        Filter logs by date range.
        
        Args:
            start_date: Start of range (inclusive)
            end_date: End of range (inclusive)
            
        Returns:
            Self for method chaining
            
        Examples:
            service.filter_by_date_range('2024-01-01', '2024-01-31')
            service.filter_by_date_range(datetime(2024, 1, 1), datetime(2024, 1, 31))
        """
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            self._queryset = self._queryset.filter(timestamp__gte=start_date)
            self._filters_applied.append(f"start_date={start_date}")
        
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            # Include the entire day
            end_date = datetime.combine(end_date, datetime.max.time())
            self._queryset = self._queryset.filter(timestamp__lte=end_date)
            self._filters_applied.append(f"end_date={end_date}")
        
        return self
    
    def filter_by_target(
        self, 
        entity_type: str, 
        entity_id: Optional[int] = None
    ) -> 'LogQueryService':
        """
        Filter logs by target entity.
        
        Args:
            entity_type: Type of entity (e.g., 'ticket', 'asset', 'project')
            entity_id: Optional specific entity ID
            
        Returns:
            Self for method chaining
        """
        self._queryset = self._queryset.filter(entity_type__iexact=entity_type)
        
        if entity_id:
            self._queryset = self._queryset.filter(entity_id=entity_id)
        
        self._filters_applied.append(f"target={entity_type}:{entity_id}")
        return self
    
    def filter_by_severity(
        self, 
        severities: Union[str, List[str]]
    ) -> 'LogQueryService':
        """
        Filter logs by severity level.
        
        Args:
            severities: Single severity or list of severities
            
        Returns:
            Self for method chaining
        """
        if isinstance(severities, str):
            severities = [severities]
        
        self._queryset = self._queryset.filter(severity__in=severities)
        self._filters_applied.append(f"severity={severities}")
        return self
    
    def filter_by_action(
        self, 
        actions: Union[str, List[str]]
    ) -> 'LogQueryService':
        """
        Filter logs by action type.
        
        Args:
            actions: Single action or list of actions
            
        Returns:
            Self for method chaining
        """
        if isinstance(actions, str):
            actions = [actions]
        
        self._queryset = self._queryset.filter(action__in=actions)
        self._filters_applied.append(f"action={actions}")
        return self
    
    def filter_by_actor(
        self, 
        actor_id: Optional[str] = None,
        actor_name: Optional[str] = None,
        actor_type: Optional[str] = None
    ) -> 'LogQueryService':
        """
        Filter logs by actor attributes.
        
        Args:
            actor_id: Actor ID (user ID for users)
            actor_name: Actor name (username) - uses exact match (case-insensitive)
                       Searches both activity_log.user.username and extra_data['actor_username']
            actor_type: Type of actor ('user', 'system', 'automation', 'api')
            
        Returns:
            Self for method chaining
        """
        if actor_id:
            self._queryset = self._queryset.filter(
                Q(actor_id=actor_id) | Q(user_id=actor_id)
            )
        
        if actor_name:
            # Search for actor_name in both:
            # 1. activity_log.user.username (FK relationship)
            # 2. extra_data['actor_username'] (stored JSON)
            self._queryset = self._queryset.filter(
                Q(actor_name__iexact=actor_name) |  # Stored actor_name field
                Q(user__username__iexact=actor_name) |  # FK relationship
                Q(extra_data__actor_username__iexact=actor_name)  # JSON field
            )
        
        if actor_type:
            self._queryset = self._queryset.filter(actor_type=actor_type)
        
        self._filters_applied.append(f"actor=({actor_id}, {actor_name}, {actor_type})")
        return self
    
    def filter_by_ip_address(
        self, 
        ip_address: str,
        include_prefix: bool = False
    ) -> 'LogQueryService':
        """
        Filter logs by IP address.
        
        Args:
            ip_address: IP address to match
            include_prefix: If True, match IP address prefix (for subnet)
            
        Returns:
            Self for method chaining
        """
        if include_prefix:
            self._queryset = self._queryset.filter(ip_address__startswith=ip_address)
        else:
            self._queryset = self._queryset.filter(ip_address=ip_address)
        
        self._filters_applied.append(f"ip={ip_address}")
        return self
    
    def search(self, search_term: str) -> 'LogQueryService':
        """
        Full-text search across log content.
        
        Args:
            search_term: Term to search for
            
        Returns:
            Self for method chaining
        """
        self._queryset = self._queryset.filter(
            Q(title__icontains=search_term) |
            Q(description__icontains=search_term) |
            Q(actor_name__icontains=search_term) |
            Q(extra_data__icontains=search_term)
        )
        self._filters_applied.append(f"search={search_term}")
        return self
    
    def order_by(
        self, 
        field: str = '-timestamp',
        nulls_last: bool = False
    ) -> 'LogQueryService':
        """
        Order the queryset.
        
        Args:
            field: Field to order by (use '-' prefix for descending)
            nulls_last: If True, null values appear last
            
        Returns:
            Self for method chaining
        """
        if nulls_last:
            # Django doesn't have native nulls_last, use F() expressions
            from django.db.models import F, Case, When, Value, IntegerField
            self._queryset = self._queryset.annotate(
                null_order=Case(
                    When(**{f"{field}__isnull": True}, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).order_by('null_order', field)
        else:
            self._queryset = self._queryset.order_by(field)
        
        return self
    
    def limit(self, count: int) -> QuerySet:
        """
        Limit results and return QuerySet.
        
        Args:
            count: Maximum number of results
            
        Returns:
            QuerySet with limit applied
        """
        return self._queryset[:count]
    
    def count(self) -> int:
        """Return count of matching logs."""
        return self._queryset.count()
    
    def exists(self) -> bool:
        """Check if any logs match the criteria."""
        return self._queryset.exists()
    
    def first(self):
        """Get first matching log or None."""
        return self._queryset.first()
    
    def get_queryset(self) -> QuerySet:
        """Get the current queryset (for advanced operations)."""
        return self._queryset
    
    def get_applied_filters(self) -> List[str]:
        """Get list of filters that have been applied."""
        return self._filters_applied.copy()
    
    def clear_filters(self) -> 'LogQueryService':
        """Clear all filters and reset to base queryset."""
        self._queryset = ActivityLog.objects.all()
        self._filters_applied = []
        return self
    
    # =========================================================================
    # Convenience methods for common queries
    # =========================================================================
    
    def get_recent_activity(
        self, 
        limit: int = 10,
        category: Optional[str] = None
    ) -> QuerySet:
        """
        Get recent activity logs.
        
        Args:
            limit: Maximum number of results
            category: Optional category filter
            
        Returns:
            QuerySet of recent logs
        """
        queryset = self.order_by('-timestamp')._queryset
        
        if category:
            queryset = queryset.filter(event_type=category)
        
        return queryset[:limit]
    
    def get_security_events(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> QuerySet:
        """
        Get security events within date range.
        
        Args:
            start_date: Start of range
            end_date: End of range
            
        Returns:
            QuerySet of security events
        """
        queryset = self._queryset.filter(
            event_type=EventCategory.SECURITY.value
        )
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.order_by('-timestamp')
    
    def get_user_activity(
        self, 
        user_id: str,
        limit: int = 50
    ) -> QuerySet:
        """
        Get activity logs for a specific user.
        
        Args:
            user_id: The user's ID
            limit: Maximum number of results
            
        Returns:
            QuerySet of user's activity
        """
        return self.filter_by_actor(actor_id=user_id).order_by('-timestamp')[:limit]
    
    def get_entity_history(
        self, 
        entity_type: str,
        entity_id: int,
        limit: int = 100
    ) -> QuerySet:
        """
        Get activity history for a specific entity.
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            limit: Maximum number of results
            
        Returns:
            QuerySet of entity history
        """
        return self.filter_by_target(entity_type, entity_id).order_by('-timestamp')[:limit]
    
    def get_error_logs(
        self, 
        start_date: Optional[datetime] = None,
        limit: int = 50
    ) -> QuerySet:
        """
        Get error and critical logs.
        
        Args:
            start_date: Optional start date filter
            limit: Maximum number of results
            
        Returns:
            QuerySet of error logs
        """
        queryset = self._queryset.filter(
            Q(severity='ERROR') | Q(severity='CRITICAL')
        )
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        
        return queryset.order_by('-timestamp')[:limit]
    
    def get_statistics(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated statistics for the current filter.
        
        Args:
            start_date: Optional start date
            end_date: Optional end date
            
        Returns:
            Dictionary with statistics
        """
        queryset = self._queryset
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return {
            'total_count': queryset.count(),
            'by_category': queryset.values('event_type').annotate(
                count=models.Count('id')
            ),
            'by_severity': queryset.values('severity').annotate(
                count=models.Count('id')
            ),
            'by_action': queryset.values('action').annotate(
                count=models.Count('id')
            ),
            'by_actor': queryset.values('actor_name').annotate(
                count=models.Count('id')
            ).order_by('-count')[:10],
        }
