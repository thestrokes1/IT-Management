"""
Activity Service Layer for IT Management Platform.

Provides high-level operations for activity logging that follow
the current data workflow patterns.

Usage:
    from apps.logs.services.activity_service import ActivityService
    
    service = ActivityService()
    service.log_ticket_action(
        action='ticket_created',
        ticket=ticket_instance,
        actor=request.user,
        metadata={'priority': 'HIGH'}
    )
"""
# NOTE: get_activities_for_dashboard is deprecated.
# Use get_activity_logs() and map explicitly in views.

import logging
from typing import Optional, List, Dict, Any, Type
from datetime import datetime, timedelta
from uuid import UUID
from functools import wraps

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Count, Q
from django.utils.timesince import timesince
from django.conf import settings

from apps.logs.models import ActivityLog, LogCategory
from apps.logs.dto import (
    ActivityDetailDTO,
    ActivitySummaryDTO,
    ActivityCreateDTO,
    TimelineEntryDTO,
    TimelineDTO,
)
from apps.logs.enums import ActivityLevel, TargetType
from apps.logs.services.diff_utils import (
    generate_diff,
    TICKET_FIELD_MAPPING,
    ASSET_FIELD_MAPPING,
    PROJECT_FIELD_MAPPING,
    USER_FIELD_MAPPING,
    log_entity_update,
)

User = get_user_model()

# Named logger for this service
logger = logging.getLogger("logs.service")


def _is_debug_enabled() -> bool:
    """Check if debug logging is enabled.
    
    Returns True only when:
    - DEBUG=True in settings
    - LOGS_DEBUG=True in settings
    """
    return getattr(settings, 'DEBUG', False) and getattr(settings, 'LOGS_DEBUG', False)


# =============================================================================
# Action Label Mapping
# =============================================================================

# Human-readable labels for activity actions
ACTION_LABELS = {
    # Ticket actions
    'TICKET_CREATED': 'Created ticket',
    'TICKET_VIEWED': 'Viewed ticket',
    'TICKET_UPDATED': 'Updated ticket',
    'TICKET_DELETED': 'Deleted ticket',
    'TICKET_ASSIGNED': 'Assigned ticket',
    'TICKET_UNASSIGNED': 'Unassigned ticket',
    'TICKET_RESOLVED': 'Resolved ticket',
    'TICKET_REOPENED': 'Reopened ticket',
    'TICKET_CLOSED': 'Closed ticket',
    'TICKET_CANCELLED': 'Cancelled ticket',
    'TICKET_ESCALATED': 'Escalated ticket',
    'TICKET_COMMENT_ADDED': 'Added comment',
    'TICKET_ATTACHMENT_ADDED': 'Added attachment',
    'TICKET_PRIORITY_CHANGED': 'Changed priority',
    'TICKET_STATUS_CHANGED': 'Changed status',
    'TICKET_ASSIGNEE_CHANGED': 'Changed assignee',
    
    # Asset actions
    'ASSET_CREATED': 'Created asset',
    'ASSET_VIEWED': 'Viewed asset',
    'ASSET_UPDATED': 'Updated asset',
    'ASSET_DELETED': 'Deleted asset',
    'ASSET_ASSIGNED': 'Assigned asset',
    'ASSET_RETURNED': 'Returned asset',
    'ASSET_MAINTENANCE_SCHEDULED': 'Scheduled maintenance',
    'ASSET_STATUS_CHANGED': 'Changed status',
    'ASSET_LOCATION_CHANGED': 'Changed location',
    'ASSET_CHECKED_OUT': 'Checked out',
    'ASSET_CHECKED_IN': 'Checked in',
    
    # Project actions
    'PROJECT_CREATED': 'Created project',
    'PROJECT_VIEWED': 'Viewed project',
    'PROJECT_UPDATED': 'Updated project',
    'PROJECT_DELETED': 'Deleted project',
    'PROJECT_COMPLETED': 'Completed project',
    'PROJECT_CANCELLED': 'Cancelled project',
    'PROJECT_MEMBER_ADDED': 'Added member',
    'PROJECT_MEMBER_REMOVED': 'Removed member',
    'PROJECT_ROLE_CHANGED': 'Changed role',
    'PROJECT_TASK_CREATED': 'Created task',
    'PROJECT_TASK_COMPLETED': 'Completed task',
    
    # User actions
    'USER_CREATED': 'Created user',
    'USER_LOGIN': 'Logged in',
    'USER_LOGOUT': 'Logged out',
    'USER_PASSWORD_CHANGED': 'Changed password',
    'USER_ROLE_CHANGED': 'Changed role',
    'USER_DEACTIVATED': 'Deactivated user',
    'USER_REACTIVATED': 'Reactivated user',
    'USER_PROFILE_UPDATED': 'Updated profile',
    
    # Generic actions
    'CREATE': 'Created',
    'UPDATE': 'Updated',
    'DELETE': 'Deleted',
    'LOGIN': 'Logged in',
    'LOGOUT': 'Logged out',
    'SEARCH': 'Searched',
    'DOWNLOAD': 'Downloaded',
    'UPLOAD': 'Uploaded',
    'EXPORT': 'Exported',
    'IMPORT': 'Imported',
    'API_CALL': 'API call',
    'SYSTEM_ACTION': 'System action',
    'SECURITY_EVENT': 'Security event',
    'ERROR': 'Error',
    'READ': 'Viewed',
}


# =============================================================================
# Activity Service
# =============================================================================

class ActivityService:
    def get_activity_logs(
            self,
            *,
            user=None,
            search=None,
            user_id=None,
            username=None,
            action=None,
            category=None,
            start_date=None,
            end_date=None,
            hour_from=None,
            hour_to=None,
            actor_role=None,
            limit=None
        ):
        """Get activity logs with filtering.
        
        For admin users (SUPERADMIN, IT_ADMIN, MANAGER), all activities are visible.
        For regular users, only their own activities or assigned activities are visible.
        
        Debug logging (filters, SQL, counts) is only shown when LOGS_DEBUG=True.
        
        Args:
            actor_role: Filter by actor_role stored in extra_data JSON field.
        """
        debug_enabled = _is_debug_enabled()
        
        if debug_enabled:
            logger.debug(f"[LOGS_DEBUG] Received filters: user_id={user.id if user else None}, "
                        f"search={search}, action={action}, actor_role={actor_role}, limit={limit}")
        
        qs = ActivityLog.objects.select_related('user', 'category')

        # =========================================================================
        # RBAC - Visibility rules applied FIRST
        # =========================================================================
        user_role = getattr(user, 'role', 'VIEWER') if user else None
        is_admin = user and (
            user.is_superuser or 
            user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
        )
        
        if debug_enabled:
            logger.debug(f"[LOGS_DEBUG] is_admin={is_admin}, user_role={user_role}")
        
        if not is_admin:
            if user:
                qs = qs.filter(
                    Q(user=user) |
                    Q(extra_data__assigned_to=user.id)
                )
            else:
                qs = qs.none()

        # =========================================================================
        # Apply filters AFTER RBAC
        # =========================================================================
        
        # User ID filter
        if user_id:
            qs = qs.filter(user_id=user_id)

        # Username filter
        if username:
            search_term = username.strip().lower()
            qs = qs.filter(
                Q(user__username__icontains=search_term) |
                Q(extra_data__actor_username__icontains=search_term) |
                Q(extra_data__assignee_username__icontains=search_term) |
                Q(extra_data__previous_assignee_username__icontains=search_term) |
                Q(extra_data__unassigned_username__icontains=search_term) |
                Q(extra_data__username__icontains=search_term)
            )

        # Action filter
        if action:
            qs = qs.filter(action__icontains=action)

        # Category filter
        if category:
            qs = qs.filter(category__name__icontains=category)

        # Actor role filter
        if actor_role:
            search_term = actor_role.strip()
            qs = qs.filter(
                Q(extra_data__actor_role__icontains=search_term) |
                Q(extra_data__role__icontains=search_term)
            )

        # Search filter
        if search:
            search_q = Q(
                Q(user__username__icontains=search) |
                Q(action__icontains=search) |
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(object_repr__icontains=search)
            )
            qs = qs.filter(search_q)

        # Date range
        if start_date:
            qs = qs.filter(timestamp__date__gte=start_date)
        if end_date:
            qs = qs.filter(timestamp__date__lte=end_date)

        # Hour range filtering
        if hour_from or hour_to:
            from django.db.models.functions import ExtractHour
            qs = qs.annotate(hour=ExtractHour('timestamp'))

            if hour_from:
                qs = qs.filter(hour__gte=int(hour_from))
            if hour_to:
                qs = qs.filter(hour__lte=int(hour_to))

        # Final ordering
        qs = qs.order_by('-timestamp')

        # =========================================================================
        # Debug logging (only when LOGS_DEBUG=True)
        # =========================================================================
        if debug_enabled:
            final_count = qs.count()
            logger.debug(f"[LOGS_DEBUG] Final queryset count: {final_count}")
            # Note: Full SQL query is NOT logged by default - only count

        # Apply limit AFTER all filters
        return qs[:limit] if limit else qs

    def log_ticket_action(
        self,
        action: str,
        ticket: Any,
        actor: Any,
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Any] = None,
        level: str = 'INFO',
    ) -> ActivityLog:
        """Log a ticket-related action."""
        return self._create_activity(
            actor=actor,
            action=action,
            target_type='ticket',
            target_id=ticket.id,
            target_name=str(ticket),
            description=self._get_action_label(action),
            metadata=metadata or {},
            request=request,
            level=level,
        )

    def log_ticket_created(
        self,
        ticket: Any,
        actor: Any,
        request: Optional[Any] = None,
    ) -> ActivityLog:
        """Log ticket creation."""
        return self.log_ticket_action(
            action='TICKET_CREATED',
            ticket=ticket,
            actor=actor,
            metadata={
                'title': ticket.title,
                'priority': ticket.priority,
                'category': str(ticket.category) if ticket.category else None,
            },
            request=request,
        )

    def log_ticket_status_changed(
        self,
        ticket: Any,
        actor: Any,
        from_status: str,
        to_status: str,
        request: Optional[Any] = None,
    ) -> ActivityLog:
        """Log ticket status change."""
        return self.log_ticket_action(
            action='TICKET_STATUS_CHANGED',
            ticket=ticket,
            actor=actor,
            metadata={
                'from_status': from_status,
                'to_status': to_status,
            },
            request=request,
        )

    def log_ticket_assigned(
        self,
        ticket: Any,
        actor: Any,
        assignee: Any,
        request: Optional[Any] = None,
    ) -> ActivityLog:
        """Log ticket assignment."""
        return self.log_ticket_action(
            action='TICKET_ASSIGNED',
            ticket=ticket,
            actor=actor,
            metadata={
                'assignee_id': assignee.id,
                'assignee_username': assignee.username,
            },
            request=request,
        )

    def log_ticket_resolved(
        self,
        ticket: Any,
        actor: Any,
        request: Optional[Any] = None,
    ) -> ActivityLog:
        """Log ticket resolution."""
        return self.log_ticket_action(
            action='TICKET_RESOLVED',
            ticket=ticket,
            actor=actor,
            metadata={
                'resolution_time_hours': ticket.resolution_hours,
            },
            request=request,
        )

    def log_asset_action(
        self,
        action: str,
        asset: Any,
        actor: Any,
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Any] = None,
        level: str = 'INFO',
    ) -> ActivityLog:
        """Log an asset-related action."""
        return self._create_activity(
            actor=actor,
            action=action,
            target_type='asset',
            target_id=asset.id,
            target_name=str(asset),
            description=self._get_action_label(action),
            metadata=metadata or {},
            request=request,
            level=level,
        )

    def log_asset_created(
        self,
        asset: Any,
        actor: Any,
        request: Optional[Any] = None,
    ) -> ActivityLog:
        """Log asset creation."""
        return self.log_asset_action(
            action='ASSET_CREATED',
            asset=asset,
            actor=actor,
            metadata={
                'name': asset.name,
                'asset_type': getattr(asset, 'asset_type', None),
                'category': str(asset.category) if getattr(asset, 'category', None) else None,
                'status': getattr(asset, 'status', None),
                'serial_number': getattr(asset, 'serial_number', None),
            },
            request=request,
        )

    def log_asset_assigned(
        self,
        asset: Any,
        actor: Any,
        assignee: Any,
        request: Optional[Any] = None,
    ) -> ActivityLog:
        """Log asset assignment."""
        return self.log_asset_action(
            action='ASSET_ASSIGNED',
            asset=asset,
            actor=actor,
            metadata={
                'assignee_id': assignee.id,
                'assignee_username': assignee.username,
            },
            request=request,
        )

    def log_project_action(
        self,
        action: str,
        project: Any,
        actor: Any,
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Any] = None,
        level: str = 'INFO',
    ) -> ActivityLog:
        """Log a project-related action."""
        return self._create_activity(
            actor=actor,
            action=action,
            target_type='project',
            target_id=project.id,
            target_name=str(project),
            description=self._get_action_label(action),
            metadata=metadata or {},
            request=request,
            level=level,
        )

    def log_project_created(
        self,
        project: Any,
        actor: Any,
        request: Optional[Any] = None,
    ) -> ActivityLog:
        """Log project creation."""
        return self.log_project_action(
            action='PROJECT_CREATED',
            project=project,
            actor=actor,
            metadata={
                'name': project.name,
                'status': project.status,
            },
            request=request,
        )

    def log_user_action(
        self,
        action: str,
        target_user: Any,
        actor: Any,
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Any] = None,
        level: str = 'INFO',
    ) -> ActivityLog:
        """Log a user-related action."""
        return self._create_activity(
            actor=actor,
            action=action,
            target_type='user',
            target_id=target_user.id,
            target_name=str(target_user),
            description=self._get_action_label(action),
            metadata=metadata or {},
            request=request,
            level=level,
        )

    def log_user_login(
        self,
        user: Any,
        request: Optional[Any] = None,
    ) -> ActivityLog:
        """Log user login."""
        return self._create_activity(
            actor=user,
            action='USER_LOGIN',
            target_type='user',
            target_id=user.id,
            target_name=str(user),
            description=self._get_action_label('USER_LOGIN'),
            metadata={},
            request=request,
            level='INFO',
        )

    def log_user_logout(
        self,
        user: Any,
        request: Optional[Any] = None,
    ) -> ActivityLog:
        """Log user logout."""
        return self._create_activity(
            actor=user,
            action='USER_LOGOUT',
            target_type='user',
            target_id=user.id,
            target_name=str(user),
            description=self._get_action_label('USER_LOGOUT'),
            metadata={},
            request=request,
            level='INFO',
        )

    def get_recent_activities(
        self,
        user: Any,
        limit: int = 10,
        activity_types: Optional[List[str]] = None,
        include_system: bool = False,
    ) -> QuerySet:
        """Get recent activities for a user."""
        qs = ActivityLog.objects.select_related('user', 'category').order_by('-timestamp')
        
        if activity_types:
            qs = qs.filter(action__in=activity_types)
        
        if not include_system:
            qs = qs.exclude(user__isnull=True)
        
        return qs[:limit]

    def get_activities_for_dashboard(
        self,
        user: Any,
        limit: int = 10,
    ) -> List[ActivityDetailDTO]:
        """Get activities formatted for dashboard display."""
        activities = self.get_recent_activities(user, limit=limit)
        
        result = []
        for activity in activities:
            result.append(ActivityDetailDTO(
                log_id=activity.log_id,
                timestamp=activity.timestamp,
                actor_username=activity.user.username if activity.user else 'System',
                actor_role=activity.user.role if activity.user else 'SYSTEM',
                action=activity.action,
                action_label=self._get_action_label(activity.action),
                target_type=activity.model_name or '',
                target_id=activity.object_id,
                target_name=activity.object_repr or '',
                description=activity.description,
                metadata=activity.extra_data or {},
                ip_address=activity.ip_address,
                level=activity.level,
            ))
        
        return result

    def get_activity_summary(
        self,
        user: Any,
        days: int = 30,
    ) -> ActivitySummaryDTO:
        """Get activity summary statistics."""
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        qs = ActivityLog.objects.filter(timestamp__gte=start_date)
        
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        
        return ActivitySummaryDTO(
            total_activities_today=qs.filter(timestamp__gte=today_start).count(),
            total_activities_week=qs.filter(timestamp__gte=week_start).count(),
            total_activities_month=qs.count(),
        )

    def get_activity_timeline(
        self,
        user: Any,
        days: int = 7,
        limit: int = 100,
    ) -> TimelineDTO:
        """Get activity timeline for charts."""
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        activities = ActivityLog.objects.filter(
            timestamp__gte=start_date
        ).select_related('user').order_by('-timestamp')[:limit]
        
        timeline = TimelineDTO()
        
        for activity in activities:
            entry = TimelineEntryDTO(
                timestamp=activity.timestamp,
                entry_type='activity',
                title=self._get_action_label(activity.action),
                description=activity.description,
                icon=self._get_icon_for_action(activity.action),
                icon_color=self._get_icon_color_for_level(activity.level),
                badge=activity.level,
                badge_color=self._get_badge_color_for_level(activity.level),
                metadata={
                    'user': activity.user.username if activity.user else 'System',
                    'action': activity.action,
                },
            )
            timeline.add_entry(entry)
        
        return timeline

    def get_user_activity(
        self,
        target_user: Any,
        actor: Any,
        days: int = 30,
        limit: int = 50,
    ) -> QuerySet:
        """Get activities performed by or on a specific user."""
        start_date = timezone.now() - timedelta(days=days)
        
        return ActivityLog.objects.filter(
            Q(user=target_user) | Q(object_id=target_user.id),
            timestamp__gte=start_date
        ).select_related('user').order_by('-timestamp')[:limit]

    @transaction.atomic
    def _create_activity(
        self,
        actor: Any,
        action: str,
        target_type: str,
        target_id: Optional[int],
        target_name: str,
        description: str,
        metadata: Dict[str, Any],
        request: Optional[Any],
        level: str,
        event_type: str = '',
        severity: str = 'INFO',
        intent: str = 'workflow',
    ) -> ActivityLog:
        """
        Internal method to create an activity log entry.
        
        This method captures all actor information at log creation time,
        ensuring logs remain readable even if users are deleted.
        """
        try:
            # Determine actor type - user, system, automation, or api
            if actor is None:
                actor_type = 'system'
            elif getattr(actor, 'is_authenticated', False):
                actor_type = 'user'
            else:
                actor_type = 'system'
            
            # Capture actor information at creation time (immutable)
            actor_id = str(getattr(actor, 'id', None)) if actor else None
            actor_name = getattr(actor, 'username', None) if actor else 'System'
            actor_role = getattr(actor, 'role', 'VIEWER') if actor else 'SYSTEM'
            
            # Ensure actor_name is never empty
            if not actor_name:
                actor_name = 'System'
            
            # Build enriched metadata
            enriched_metadata = {
                'actor_id': actor_id,
                'actor_username': actor_name,
                'actor_role': actor_role,
                **metadata,
            }
            
            return ActivityLog.objects.create(
                # Actor information - IMMUTABLE, captured at creation time
                actor_type=actor_type,
                actor_id=actor_id,
                actor_name=actor_name,
                actor_role=actor_role,
                
                # Event information
                event_type=event_type or action,
                severity=severity,
                intent=intent,
                
                # Entity information
                entity_type=target_type,
                entity_id=target_id,
                
                # Legacy FK (deprecated but kept for backward compatibility)
                user=actor,
                
                action=action,
                level=level,
                title=description,
                description=description,
                model_name=target_type,
                object_id=target_id,
                object_repr=target_name,
                ip_address=self._get_client_ip(request),
                user_agent=self._get_user_agent(request),
                extra_data=enriched_metadata,
            )
        except Exception as e:
            # Log error properly without exposing internals in production
            logger.error(f"ActivityLog creation failed: action={action}, target_type={target_type}")
            logger.exception(e)  # Full traceback only in debug logs
            raise

    def _get_action_label(self, action: str) -> str:
        """Get human-readable label for an action."""
        return ACTION_LABELS.get(action, action.replace('_', ' ').title())

    def _get_client_ip(self, request: Optional[Any]) -> Optional[str]:
        """Extract client IP from request."""
        if not request:
            return None
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def _get_user_agent(self, request: Optional[Any]) -> str:
        """Extract user agent from request. Returns empty string if not available."""
        if not request:
            return ''
        return request.META.get('HTTP_USER_AGENT', '')

    def _get_icon_for_action(self, action: str) -> str:
        """Get icon class for an action."""
        icons = {
            'TICKET_CREATED': 'fa-ticket-alt',
            'TICKET_ASSIGNED': 'fa-user-plus',
            'TICKET_RESOLVED': 'fa-check-circle',
            'ASSET_CREATED': 'fa-desktop',
            'ASSET_ASSIGNED': 'fa-hand-paper',
            'PROJECT_CREATED': 'fa-project-diagram',
            'USER_CREATED': 'fa-user-plus',
            'USER_LOGIN': 'fa-sign-in-alt',
            'USER_LOGOUT': 'fa-sign-out-alt',
        }
        return icons.get(action, 'fa-circle')

    def _get_icon_color_for_level(self, level: str) -> str:
        """Get icon color for a log level."""
        colors = {
            'DEBUG': 'text-gray-400',
            'INFO': 'text-blue-500',
            'WARNING': 'text-yellow-500',
            'ERROR': 'text-red-500',
            'CRITICAL': 'text-red-700',
        }
        return colors.get(level, 'text-gray-400')

    def _get_badge_color_for_level(self, level: str) -> str:
        """Get badge color class for a log level."""
        colors = {
            'DEBUG': 'bg-gray-100 text-gray-800',
            'INFO': 'bg-blue-100 text-blue-800',
            'WARNING': 'bg-yellow-100 text-yellow-800',
            'ERROR': 'bg-red-100 text-red-800',
            'CRITICAL': 'bg-red-100 text-red-800',
        }
        return colors.get(level, 'bg-gray-100 text-gray-800')

    # =========================================================================
    # Causal Log Chaining Methods
    # =========================================================================

    def create_chained_log(
        self,
        parent_log_id: UUID,
        action: str,
        actor: Any,
        target_type: str,
        target_id: Optional[int],
        target_name: str,
        description: str,
        chain_type: str = 'CAUSED',
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Any] = None,
        level: str = 'INFO',
    ) -> ActivityLog:
        """
        Create a log entry that is chained to a parent log.
        
        This enables causal chains like:
        - Asset failure → Ticket created → Technician assigned → SLA breach → Escalation
        
        Args:
            parent_log_id: The log_id of the parent log this chain links to
            action: The action type (e.g., 'CREATE', 'UPDATE')
            actor: The user/system performing the action
            target_type: Type of entity ('ticket', 'asset', 'project', 'user')
            target_id: ID of the affected entity
            target_name: String representation of the entity
            description: Human-readable description
            chain_type: Type of causal relationship (CAUSED, ESCALATED, RESOLVED, etc.)
            metadata: Additional metadata
            request: Optional request for IP address
            level: Log level (INFO, WARNING, ERROR)
            
        Returns:
            The created ActivityLog instance with chain metadata
            
        Example:
            >>> # Asset failure detected
            >>> failure_log = service.log_asset_action(
            ...     action='ASSET_FAILURE',
            ...     asset=asset,
            ...     actor=system_user,
            ...     metadata={'error': 'Disk failure'},
            ... )
            >>> 
            >>> # Ticket created - chained to failure
            >>> ticket_log = service.create_chained_log(
            ...     parent_log_id=failure_log.log_id,
            ...     action='TICKET_CREATED',
            ...     actor=system_user,
            ...     target_type='ticket',
            ...     target_id=ticket.id,
            ...     target_name=str(ticket),
            ...     description='Auto-created ticket for asset failure',
            ...     chain_type='CAUSED',
            ... )
        """
        # Get parent log to calculate chain depth
        try:
            parent_log = ActivityLog.objects.get(log_id=parent_log_id)
            chain_depth = parent_log.chain_depth + 1
        except ActivityLog.DoesNotExist:
            chain_depth = 0
        
# Build chain metadata
        chain_metadata = {
            'parent_log_id': str(parent_log_id),
            'chain_type': chain_type,
            **(metadata or {}),
        }
        
        return self._create_activity(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            description=description,
            metadata=chain_metadata,
            request=request,
            level=level,
            event_type=action,
            severity=level,
            intent='workflow',
        )

    def get_log_chain(self, root_log_id: UUID) -> List[ActivityLog]:
        """
        Get the full chain of logs starting from a root log.
        
        Retrieves all logs in the causal chain by following parent_log_id references.
        
        Args:
            root_log_id: The log_id of the root (oldest) log in the chain
            
        Returns:
            List of ActivityLogs ordered from root to leaf (oldest to newest)
            
        Example:
            >>> chain = service.get_log_chain(root_log_id)
            >>> for log in chain:
            ...     print(f"{log.timestamp}: {log.description}")
        """
        # First, get the root log and find all descendants
        # We need to traverse the tree - start with the root and find all children
        chain = []
        visited = set()
        
        def traverse_from_root(log_id: UUID):
            """Recursively get all logs in the chain starting from root."""
            if log_id in visited:
                return
            visited.add(log_id)
            
            try:
                log = ActivityLog.objects.get(log_id=log_id)
                chain.append(log)
                
                # Find all children (logs that have this as parent)
                children = ActivityLog.objects.filter(
                    parent_log_id=log_id
                ).order_by('timestamp')
                
                for child in children:
                    traverse_from_root(child.log_id)
            except ActivityLog.DoesNotExist:
                pass
        
        # Start traversal from root
        traverse_from_root(root_log_id)
        
        # Sort by timestamp to get chronological order
        return sorted(chain, key=lambda x: x.timestamp)

    def get_log_chain_by_leaf(self, leaf_log_id: UUID) -> List[ActivityLog]:
        """
        Get the full chain of logs ending at a specific leaf log.
        
        Useful when you have the newest log and want to trace back to the root.
        
        Args:
            leaf_log_id: The log_id of the leaf (newest) log in the chain
            
        Returns:
            List of ActivityLogs ordered from root to leaf (oldest to newest)
        """
        chain = []
        visited = set()
        
        def traverse_to_root(log_id: UUID):
            """Recursively get all logs from leaf back to root."""
            if log_id in visited:
                return
            visited.add(log_id)
            
            try:
                log = ActivityLog.objects.get(log_id=log_id)
                chain.append(log)
                
                # Go to parent if exists
                if log.parent_log_id:
                    traverse_to_root(log.parent_log_id)
            except ActivityLog.DoesNotExist:
                pass
        
        traverse_to_root(leaf_log_id)
        
        # Reverse to get root-to-leaf order
        return list(reversed(chain))

    def get_entity_log_chain(
        self,
        entity_type: str,
        entity_id: int,
        limit: int = 50,
    ) -> List[ActivityLog]:
        """
        Get all log entries for an entity, organized by causal chains.
        
        Groups logs by their chain relationships to show the full history
        of an entity with causal connections visible.
        
        Args:
            entity_type: Type of entity ('ticket', 'asset', 'project', 'user')
            entity_id: ID of the entity
            limit: Maximum number of logs to return
            
        Returns:
            List of ActivityLogs with chain information for UI rendering
        """
        # Get all logs for this entity
        logs = ActivityLog.objects.filter(
            entity_type=entity_type,
            entity_id=entity_id
        ).order_by('-timestamp')[:limit]
        
        # Organize into chains
        chains = {}
        orphan_logs = []
        
        for log in logs:
            if log.parent_log_id:
                # Part of a chain - group by root
                root_id = self._find_root_id(log.log_id)
                if root_id not in chains:
                    chains[root_id] = []
                chains[root_id].append(log)
            else:
                # Root or orphan - may start a chain
                orphan_logs.append(log)
        
        # Sort each chain by timestamp
        for root_id in chains:
            chains[root_id] = sorted(chains[root_id], key=lambda x: x.timestamp)
        
        return {
            'chains': chains,
            'orphan_logs': sorted(orphan_logs, key=lambda x: x.timestamp, reverse=True),
            'total_chains': len(chains),
            'total_orphans': len(orphan_logs),
        }

    def _find_root_id(self, log_id: UUID) -> UUID:
        """Find the root log_id for a given log by traversing up the chain."""
        try:
            log = ActivityLog.objects.get(log_id=log_id)
            if log.parent_log_id:
                return self._find_root_id(log.parent_log_id)
            return log_id
        except ActivityLog.DoesNotExist:
            return log_id

    # =========================================================================
    # Diff-aware logging methods
    # =========================================================================

    def log_entity_update(
        self,
        action: str,
        old_instance: Any,
        new_instance: Any,
        actor: Any,
        entity_type: str,
        field_mapping: Optional[Dict[str, str]] = None,
        request: Optional[Any] = None,
        level: str = 'INFO',
    ) -> ActivityLog:
        """
        Log an entity update with full diff information.
        
        This method generates a detailed diff between old and new instances,
        storing the changes in extra_data for display in the logs UI.
        
        Args:
            action: The action type (e.g., 'TICKET_UPDATED', 'ASSET_UPDATED')
            old_instance: The original instance before changes
            new_instance: The updated instance after changes
            actor: The user performing the update
            entity_type: Type of entity ('ticket', 'asset', 'project', 'user')
            field_mapping: Custom field name mappings for display
            request: Optional request for IP address
            level: Log level (INFO, WARNING, ERROR)
            
        Returns:
            The created ActivityLog instance
            
        Example:
            >>> service.log_entity_update(
            ...     action='TICKET_UPDATED',
            ...     old_instance=ticket_before,
            ...     new_instance=ticket_after,
            ...     actor=request.user,
            ...     entity_type='ticket',
            ...     field_mapping=TICKET_FIELD_MAPPING,
            ...     request=request,
            ... )
        """
        # Use default field mappings based on entity type
        if field_mapping is None:
            mapping_map = {
                'ticket': TICKET_FIELD_MAPPING,
                'asset': ASSET_FIELD_MAPPING,
                'project': PROJECT_FIELD_MAPPING,
                'user': USER_FIELD_MAPPING,
            }
            field_mapping = mapping_map.get(entity_type, {})
        
        # Generate diff using the diff_utils function
        diff = generate_diff(
            old_instance,
            new_instance,
            field_mapping=field_mapping,
        )
        
        # Build description based on changes
        if diff.has_changes:
            changes_str = ', '.join(diff.changed_fields)
            description = f"Updated {entity_type}: {changes_str}"
        else:
            description = f"Updated {entity_type} (no changes detected)"
        
        # Build metadata with diff
        metadata = {
            'diff': diff.to_dict(),
            'change_count': diff.change_count,
        }
        
        # Create the activity log
        return self._create_activity(
            actor=actor,
            action=action,
            target_type=entity_type,
            target_id=diff.entity_id,
            target_name=str(new_instance),
            description=description,
            metadata=metadata,
            request=request,
            level=level,
            event_type=action,
            severity=level,
            intent='workflow',
        )

