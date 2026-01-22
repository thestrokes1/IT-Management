"""
Centralized Activity Logger Service.

Provides a unified interface for logging all user actions across
tickets, assets, and projects. No business logic inside - pure logging.

Usage:
    from apps.core.services.activity_logger import log_activity

    # Log a ticket creation
    log_activity(
        actor=request.user,
        action='ticket_created',
        target_type='ticket',
        target_id=ticket.id,
        metadata={'title': ticket.title, 'priority': ticket.priority}
    )

    # Log an asset update
    log_activity(
        actor=request.user,
        action='asset_updated',
        target_type='asset',
        target_id=asset.id,
        metadata={'changes': {'status': ['available', 'in_use']}}
    )
"""

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

User = get_user_model()


# =============================================================================
# Action Constants - Human-readable labels for all actions
# =============================================================================

class ActivityAction:
    """Human-readable action labels for activity logging."""
    
    # Ticket actions
    TICKET_CREATED = 'ticket_created'
    TICKET_VIEWED = 'ticket_viewed'
    TICKET_UPDATED = 'ticket_updated'
    TICKET_DELETED = 'ticket_deleted'
    TICKET_ASSIGNED = 'ticket_assigned'
    TICKET_UNASSIGNED = 'ticket_unassigned'
    TICKET_RESOLVED = 'ticket_resolved'
    TICKET_REOPENED = 'ticket_reopened'
    TICKET_CLOSED = 'ticket_closed'
    TICKET_CANCELLED = 'ticket_cancelled'
    TICKET_ESCALATED = 'ticket_escalated'
    TICKET_COMMENT_ADDED = 'ticket_comment_added'
    TICKET_ATTACHMENT_ADDED = 'ticket_attachment_added'
    TICKET_PRIORITY_CHANGED = 'ticket_priority_changed'
    TICKET_STATUS_CHANGED = 'ticket_status_changed'
    TICKET_ASSIGNEE_CHANGED = 'ticket_assignee_changed'
    
    # Asset actions
    ASSET_CREATED = 'asset_created'
    ASSET_VIEWED = 'asset_viewed'
    ASSET_UPDATED = 'asset_updated'
    ASSET_DELETED = 'asset_deleted'
    ASSET_ASSIGNED = 'asset_assigned'
    ASSET_RETURNED = 'asset_returned'
    ASSET_MAINTENANCE_SCHEDULED = 'asset_maintenance_scheduled'
    ASSET_STATUS_CHANGED = 'asset_status_changed'
    ASSET_LOCATION_CHANGED = 'asset_location_changed'
    ASSET_CHECKED_OUT = 'asset_checked_out'
    ASSET_CHECKED_IN = 'asset_checked_in'
    
    # Project actions
    PROJECT_CREATED = 'project_created'
    PROJECT_VIEWED = 'project_viewed'
    PROJECT_UPDATED = 'project_updated'
    PROJECT_DELETED = 'project_deleted'
    PROJECT_COMPLETED = 'project_completed'
    PROJECT_CANCELLED = 'project_cancelled'
    PROJECT_MEMBER_ADDED = 'project_member_added'
    PROJECT_MEMBER_REMOVED = 'project_member_removed'
    PROJECT_ROLE_CHANGED = 'project_role_changed'
    PROJECT_TASK_CREATED = 'project_task_created'
    PROJECT_TASK_COMPLETED = 'project_task_completed'
    
    # User actions
    USER_CREATED = 'user_created'
    USER_LOGIN = 'user_login'
    USER_LOGOUT = 'user_logout'
    USER_PASSWORD_CHANGED = 'user_password_changed'
    USER_ROLE_CHANGED = 'user_role_changed'
    USER_DEACTIVATED = 'user_deactivated'
    USER_REACTIVATED = 'user_reactivated'
    USER_PROFILE_UPDATED = 'user_profile_updated'


# Human-readable labels for actions
ACTION_LABELS = {
    # Tickets
    ActivityAction.TICKET_CREATED: 'Created ticket',
    ActivityAction.TICKET_VIEWED: 'Viewed ticket',
    ActivityAction.TICKET_UPDATED: 'Updated ticket',
    ActivityAction.TICKET_DELETED: 'Deleted ticket',
    ActivityAction.TICKET_ASSIGNED: 'Assigned ticket',
    ActivityAction.TICKET_UNASSIGNED: 'Unassigned ticket',
    ActivityAction.TICKET_RESOLVED: 'Resolved ticket',
    ActivityAction.TICKET_REOPENED: 'Reopened ticket',
    ActivityAction.TICKET_CLOSED: 'Closed ticket',
    ActivityAction.TICKET_CANCELLED: 'Cancelled ticket',
    ActivityAction.TICKET_ESCALATED: 'Escalated ticket',
    ActivityAction.TICKET_COMMENT_ADDED: 'Added comment to ticket',
    ActivityAction.TICKET_ATTACHMENT_ADDED: 'Added attachment to ticket',
    ActivityAction.TICKET_PRIORITY_CHANGED: 'Changed ticket priority',
    ActivityAction.TICKET_STATUS_CHANGED: 'Changed ticket status',
    ActivityAction.TICKET_ASSIGNEE_CHANGED: 'Changed ticket assignee',
    
    # Assets
    ActivityAction.ASSET_CREATED: 'Created asset',
    ActivityAction.ASSET_VIEWED: 'Viewed asset',
    ActivityAction.ASSET_UPDATED: 'Updated asset',
    ActivityAction.ASSET_DELETED: 'Deleted asset',
    ActivityAction.ASSET_ASSIGNED: 'Assigned asset',
    ActivityAction.ASSET_RETURNED: 'Returned asset',
    ActivityAction.ASSET_MAINTENANCE_SCHEDULED: 'Scheduled asset maintenance',
    ActivityAction.ASSET_STATUS_CHANGED: 'Changed asset status',
    ActivityAction.ASSET_LOCATION_CHANGED: 'Changed asset location',
    ActivityAction.ASSET_CHECKED_OUT: 'Checked out asset',
    ActivityAction.ASSET_CHECKED_IN: 'Checked in asset',
    
    # Projects
    ActivityAction.PROJECT_CREATED: 'Created project',
    ActivityAction.PROJECT_VIEWED: 'Viewed project',
    ActivityAction.PROJECT_UPDATED: 'Updated project',
    ActivityAction.PROJECT_DELETED: 'Deleted project',
    ActivityAction.PROJECT_COMPLETED: 'Completed project',
    ActivityAction.PROJECT_CANCELLED: 'Cancelled project',
    ActivityAction.PROJECT_MEMBER_ADDED: 'Added project member',
    ActivityAction.PROJECT_MEMBER_REMOVED: 'Removed project member',
    ActivityAction.PROJECT_ROLE_CHANGED: 'Changed project role',
    ActivityAction.PROJECT_TASK_CREATED: 'Created project task',
    ActivityAction.PROJECT_TASK_COMPLETED: 'Completed project task',
    
    # Users
    ActivityAction.USER_CREATED: 'Created user',
    ActivityAction.USER_LOGIN: 'User logged in',
    ActivityAction.USER_LOGOUT: 'User logged out',
    ActivityAction.USER_PASSWORD_CHANGED: 'Changed password',
    ActivityAction.USER_ROLE_CHANGED: 'Changed user role',
    ActivityAction.USER_DEACTIVATED: 'Deactivated user',
    ActivityAction.USER_REACTIVATED: 'Reactivated user',
    ActivityAction.USER_PROFILE_UPDATED: 'Updated profile',
}


@dataclass
class ActivityLogEntry:
    """
    Data class representing an activity log entry.
    
    All fields are optional to allow flexible logging.
    """
    actor: Optional[Any] = None
    action: str = ''
    target_type: str = ''
    target_id: Optional[int] = None
    metadata: Dict = field(default_factory=dict)
    title: str = ''
    description: str = ''
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    level: str = 'INFO'


def _get_action_label(action: str) -> str:
    """Get human-readable label for an action."""
    return ACTION_LABELS.get(action, action.replace('_', ' ').title())


def _build_title(entry: ActivityLogEntry) -> str:
    """Build human-readable title for the log entry."""
    if entry.title:
        return entry.title
    
    actor_name = entry.actor.username if entry.actor else 'System'
    label = _get_action_label(entry.action)
    
    if entry.target_type and entry.target_id:
        return f"{actor_name} {label} ({entry.target_type}: {entry.target_id})"
    return f"{actor_name} {label}"


def _build_description(entry: ActivityLogEntry) -> str:
    """Build human-readable description for the log entry."""
    if entry.description:
        return entry.description
    
    # Generate description from metadata
    if entry.metadata:
        parts = []
        for key, value in entry.metadata.items():
            if isinstance(value, dict):
                # Show changed fields
                if 'from' in value and 'to' in value:
                    parts.append(f"{key}: {value['from']} → {value['to']}")
            else:
                parts.append(f"{key}: {value}")
        
        if parts:
            return '; '.join(parts)
    
    return ''


def log_activity(
    actor: Optional[Any] = None,
    action: str = '',
    target_type: str = '',
    target_id: Optional[int] = None,
    metadata: Optional[Dict] = None,
    title: str = '',
    description: str = '',
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    level: str = 'INFO',
    request: Optional[Any] = None,
) -> int:
    """
    Log an activity event.
    
    This is the main entry point for activity logging. All parameters are optional
    except for action, which is required.
    
    Args:
        actor: User performing the action (None for system actions)
        action: Action constant from ActivityAction class
        target_type: Type of target (e.g., 'ticket', 'asset', 'project')
        target_id: ID of the target object
        metadata: Additional context as key-value pairs
        title: Custom title (auto-generated if not provided)
        description: Custom description (auto-generated if not provided)
        ip_address: Client IP address
        user_agent: Client user agent
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        request: Django request object (extracts IP and user agent if not provided)
    
    Returns:
        int: The ID of the created ActivityLog entry
    
    Example:
        log_activity(
            actor=request.user,
            action=ActivityAction.TICKET_CREATED,
            target_type='ticket',
            target_id=ticket.id,
            metadata={'priority': ticket.priority, 'category': ticket.category.name}
        )
    """
    from apps.logs.models import ActivityLog
    
    # Extract request info if provided
    if request:
        if not ip_address:
            ip_address = get_client_ip(request)
        if not user_agent:
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    
    # Build entry
    entry = ActivityLogEntry(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata=metadata or {},
        title=title,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        level=level,
    )
    
    # Create the log entry
    log = ActivityLog.objects.create(
        user=actor,
        action=action,
        level=level,
        title=_build_title(entry),
        description=_build_description(entry),
        model_name=target_type,
        object_id=target_id,
        object_repr=str(target_id) if target_id else '',
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else '',
        extra_data=metadata or {},
    )
    
    return log.id


def log_activity_atomic(
    actor: Optional[Any] = None,
    action: str = '',
    target_type: str = '',
    target_id: Optional[int] = None,
    metadata: Optional[Dict] = None,
    **kwargs
) -> int:
    """
    Log an activity within a database transaction.
    
    Use this when the activity should be rolled back if the transaction fails.
    
    Args:
        Same as log_activity()
    
    Returns:
        int: The ID of the created ActivityLog entry
    """
    with transaction.atomic():
        return log_activity(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata,
            **kwargs
        )


def get_client_ip(request: Any) -> Optional[str]:
    """
    Extract client IP address from request.
    
    Handles proxied requests by checking X-Forwarded-For header.
    
    Args:
        request: Django request object
    
    Returns:
        str: Client IP address or None
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the chain (original client)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# =============================================================================
# Convenience functions for common logging patterns
# =============================================================================

def log_ticket_created(actor: Any, ticket: Any, request: Optional[Any] = None) -> int:
    """Log ticket creation."""
    return log_activity(
        actor=actor,
        action=ActivityAction.TICKET_CREATED,
        target_type='ticket',
        target_id=ticket.id,
        metadata={
            'title': ticket.title,
            'priority': ticket.priority,
            'category': ticket.category.name if ticket.category else None,
        },
        request=request,
    )


def log_ticket_status_changed(
    actor: Any,
    ticket: Any,
    from_status: str,
    to_status: str,
    request: Optional[Any] = None
) -> int:
    """Log ticket status change."""
    return log_activity(
        actor=actor,
        action=ActivityAction.TICKET_STATUS_CHANGED,
        target_type='ticket',
        target_id=ticket.id,
        metadata={
            'from_status': from_status,
            'to_status': to_status,
        },
        request=request,
    )


def log_ticket_resolved(actor: Any, ticket: Any, request: Optional[Any] = None) -> int:
    """Log ticket resolution."""
    return log_activity(
        actor=actor,
        action=ActivityAction.TICKET_RESOLVED,
        target_type='ticket',
        target_id=ticket.id,
        metadata={
            'resolution_time_hours': ticket.resolution_hours,
        },
        request=request,
    )


def log_ticket_reopened(
    actor: Any,
    ticket: Any,
    reason: str,
    request: Optional[Any] = None
) -> int:
    """Log ticket reopening."""
    return log_activity(
        actor=actor,
        action=ActivityAction.TICKET_REOPENED,
        target_type='ticket',
        target_id=ticket.id,
        metadata={
            'reason': reason,
        },
        request=request,
    )


def log_asset_created(actor: Any, asset: Any, request: Optional[Any] = None) -> int:
    """Log asset creation."""
    return log_activity(
        actor=actor,
        action=ActivityAction.ASSET_CREATED,
        target_type='asset',
        target_id=asset.id,
        metadata={
            'name': asset.name,
            'asset_type': asset.asset_type if hasattr(asset, 'asset_type') else None,
            'serial_number': asset.serial_number if hasattr(asset, 'serial_number') else None,
        },
        request=request,
    )


def log_asset_status_changed(
    actor: Any,
    asset: Any,
    from_status: str,
    to_status: str,
    request: Optional[Any] = None
) -> int:
    """Log asset status change."""
    return log_activity(
        actor=actor,
        action=ActivityAction.ASSET_STATUS_CHANGED,
        target_type='asset',
        target_id=asset.id,
        metadata={
            'from_status': from_status,
            'to_status': to_status,
        },
        request=request,
    )


def log_project_created(actor: Any, project: Any, request: Optional[Any] = None) -> int:
    """Log project creation."""
    return log_activity(
        actor=actor,
        action=ActivityAction.PROJECT_CREATED,
        target_type='project',
        target_id=project.id,
        metadata={
            'name': project.name,
            'status': project.status,
        },
        request=request,
    )


def log_project_member_added(
    actor: Any,
    project: Any,
    member: Any,
    role: str,
    request: Optional[Any] = None
) -> int:
    """Log project member addition."""
    return log_activity(
        actor=actor,
        action=ActivityAction.PROJECT_MEMBER_ADDED,
        target_type='project',
        target_id=project.id,
        metadata={
            'member_id': member.id,
            'member_username': member.username,
            'role': role,
        },
        request=request,
    )

