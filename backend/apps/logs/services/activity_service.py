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

import logging
from typing import Optional, List, Dict, Any

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.conf import settings

from apps.logs.models import ActivityLog
from apps.core.domain.roles import is_admin_role

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
            is_admin_role(user_role)
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

