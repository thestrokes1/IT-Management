"""
Structured Logging Payloads for Audit-Grade Activity Logging.

This module defines structured logging patterns for common actions across
tickets, assets, projects, and users. All payloads are designed to be immutable
and human-readable at write time.

Key Principles:
- Human-readable messages generated AT WRITE TIME, not in templates
- Structured changes with before/after values
- All required fields populated: actor_display_name, actor_role, entity_display_name
- No business logic in UI - templates only render pre-computed data

Usage:
    from apps.logs.services.structured_payloads import log_ticket_status_change
    
    log_ticket_status_change(
        actor=request.user,
        ticket=ticket_instance,
        from_status='OPEN',
        to_status='IN_PROGRESS',
        request=request
    )
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json


# =============================================================================
# Change Tracking Data Classes
# =============================================================================

@dataclass
class FieldChange:
    """Represents a single field change."""
    before: Any = None
    after: Any = None
    label: str = ""  # Human-readable field name
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'before': self.before,
            'after': self.after,
            'label': self.label,
        }


@dataclass
class ChangeSet:
    """Represents multiple field changes."""
    changes: Dict[str, FieldChange] = field(default_factory=dict)
    
    def add(self, field_name: str, before: Any, after: Any, label: str = ""):
        """Add a field change."""
        self.changes[field_name] = FieldChange(
            before=before,
            after=after,
            label=label or field_name.replace('_', ' ').title()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            name: change.to_dict() 
            for name, change in self.changes.items()
        }
    
    def to_summary(self) -> Optional[str]:
        """Generate a human-readable summary of changes."""
        if not self.changes:
            return None
        
        parts = []
        for field_name, change in self.changes.items():
            label = change.label or field_name
            before = change.before
            after = change.after
            
            if before is not None and after is not None:
                parts.append(f"{label}: {before} → {after}")
            elif after is not None:
                parts.append(f"{label}: {after}")
        
        return ', '.join(parts) if parts else None


# =============================================================================
# Entity Display Name Builders
# =============================================================================

def build_ticket_display_name(ticket_id: int, title: str = None) -> str:
    """
    Build human-readable ticket display name.
    
    Examples:
    - "Ticket #19 – Printer offline"
    - "Ticket #42 – Error en servidor"
    """
    if title:
        # Truncate long titles
        title_short = title[:50] + '...' if len(title) > 50 else title
        return f"Ticket #{ticket_id} – {title_short}"
    else:
        return f"Ticket #{ticket_id}"


def build_asset_display_name(asset_id: int, name: str = None) -> str:
    """
    Build human-readable asset display name.
    
    Examples:
    - "Asset #LAPTOP-001 – MacBook Pro 16\""
    - "Asset #7"
    """
    if name:
        return f"Asset #{asset_id} – {name}"
    else:
        return f"Asset #{asset_id}"


def build_project_display_name(project_id: int, name: str = None) -> str:
    """
    Build human-readable project display name.
    
    Examples:
    - "Proyecto #3 – Migración a la Nube"
    - "Proyecto #3"
    """
    if name:
        return f"Proyecto #{project_id} – {name}"
    else:
        return f"Proyecto #{project_id}"


def build_user_display_name(user_id: int, username: str = None) -> str:
    """
    Build human-readable user display name.
    
    Examples:
    - "Usuario: juan_perez"
    - "Usuario #42"
    """
    if username:
        return f"Usuario: {username}"
    else:
        return f"Usuario #{user_id}"


# =============================================================================
# Actor Display Name Builder
# =============================================================================

def build_actor_display_name(actor) -> str:
    """
    Build human-readable actor display name for logging.
    
    Examples:
    - "Juan Pérez"
    - "admin_sistema"
    """
    if not actor:
        return "System"
    
    # Try full name first
    full_name = getattr(actor, 'full_name', None)
    if full_name:
        return full_name
    
    # Fall back to username
    username = getattr(actor, 'username', None)
    if username:
        return username
    
    return "Unknown"


def build_actor_role(actor) -> str:
    """Get actor role for logging."""
    if not actor:
        return ""
    return getattr(actor, 'role', '') or ''


# =============================================================================
# Action Verb Configuration (for UI rendering)
# =============================================================================

ACTION_VERBS = {
    # Ticket actions
    'TICKET_CREATED': 'creó el ticket',
    'TICKET_VIEWED': 'visualizó el ticket',
    'TICKET_UPDATED': 'actualizó el ticket',
    'TICKET_DELETED': 'eliminó el ticket',
    'TICKET_ASSIGNED': 'asignó el ticket',
    'TICKET_UNASSIGNED': 'desasignó el ticket',
    'TICKET_RESOLVED': 'resolvió el ticket',
    'TICKET_REOPENED': 'reabrió el ticket',
    'TICKET_CLOSED': 'cerró el ticket',
    'TICKET_STATUS_CHANGED': 'cambió el estado del ticket',
    'TICKET_PRIORITY_CHANGED': 'cambió la prioridad del ticket',
    'TICKET_ASSIGNEE_CHANGED': 'cambió el asignado del ticket',
    
    # Asset actions
    'ASSET_CREATED': 'creó el asset',
    'ASSET_VIEWED': 'visualizó el asset',
    'ASSET_UPDATED': 'actualizó el asset',
    'ASSET_DELETED': 'eliminó el asset',
    'ASSET_ASSIGNED': 'asignó el asset',
    'ASSET_UNASSIGNED': 'desasignó el asset',
    'ASSET_STATUS_CHANGED': 'cambió el estado del asset',
    
    # Project actions
    'PROJECT_CREATED': 'creó el proyecto',
    'PROJECT_VIEWED': 'visualizó el proyecto',
    'PROJECT_UPDATED': 'actualizó el proyecto',
    'PROJECT_DELETED': 'eliminó el proyecto',
    'PROJECT_COMPLETED': 'completó el proyecto',
    'PROJECT_MEMBER_ADDED': 'agregó miembro al proyecto',
    'PROJECT_MEMBER_REMOVED': 'removió miembro del proyecto',
    'PROJECT_ROLE_CHANGED': 'cambió el rol en el proyecto',
    
    # User actions
    'USER_CREATED': 'creó el usuario',
    'USER_VIEWED': 'visualizó el usuario',
    'USER_UPDATED': 'actualizó el usuario',
    'USER_DELETED': 'eliminó el usuario',
    'USER_ROLE_CHANGED': 'cambió el rol del usuario',
    'USER_DEACTIVATED': 'desactivó al usuario',
    'USER_REACTIVATED': 'reactivó al usuario',
    
    # Auth actions
    'USER_LOGIN': 'inició sesión',
    'USER_LOGOUT': 'cerró sesión',
    'PASSWORD_CHANGED': 'cambió la contraseña',
}


def get_action_verb(action_key: str) -> str:
    """Get human-readable verb for an action."""
    return ACTION_VERBS.get(action_key, action_key.replace('_', ' ').lower())


# =============================================================================
# Logging Service Functions
# =============================================================================

def _get_client_ip(request) -> Optional[str]:
    """Extract client IP from request."""
    if not request:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _get_user_agent(request) -> Optional[str]:
    """Extract user agent from request."""
    if not request:
        return None
    return request.META.get('HTTP_USER_AGENT', '')[:500]


def _extract_extra_data(actor, changes: ChangeSet = None) -> Dict[str, Any]:
    """
    Build extra_data dict with actor info and changes.
    
    This ensures all structured data is available at write time.
    """
    extra = {
        'actor_id': actor.id if actor else None,
        'actor_username': getattr(actor, 'username', None) if actor else None,
        'actor_role': build_actor_role(actor),
    }
    
    if changes:
        extra['changes'] = changes.to_dict()
        extra['changes_summary'] = changes.to_summary()
    
    return extra


# =============================================================================
# Ticket Logging Functions
# =============================================================================

def log_ticket_created(
    actor,
    ticket_id: int,
    title: str,
    priority: str = None,
    category_name: str = None,
    request=None
):
    """
    Log ticket creation with structured payload.
    
    Example Log Entry:
    "Juan Pérez creó el ticket Ticket #19 – Printer offline"
    """
    from apps.logs.models import ActivityLog
    
    entity_display_name = build_ticket_display_name(ticket_id, title)
    
    # Build changes
    changes = ChangeSet()
    changes.add('title', None, title, 'Título')
    if priority:
        changes.add('priority', None, priority, 'Prioridad')
    if category_name:
        changes.add('category', None, category_name, 'Categoría')
    
    # Generate human-readable message
    actor_name = build_actor_display_name(actor)
    human_readable = f"{actor_name} creó el ticket {entity_display_name}"
    
    ActivityLog.objects.create(
        user=actor,
        action='TICKET_CREATED',
        level='INFO',
        title=human_readable,
        description=human_readable,
        model_name='Ticket',
        object_id=ticket_id,
        object_repr=entity_display_name,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data=_extract_extra_data(actor, changes),
    )


def log_ticket_status_changed(
    actor,
    ticket_id: int,
    title: str,
    from_status: str,
    to_status: str,
    request=None
):
    """
    Log ticket status change with structured payload.
    
    Example Log Entry:
    "Juan Pérez cambió el estado del ticket Ticket #19 – Printer offline (Estado: OPEN → IN_PROGRESS)"
    
    Before (Broken):
    ❌ "Ticket updated (ID 19)"
    
    After (Fixed):
    ✅ "Juan Pérez cambió el estado del ticket Ticket #19 – Printer offline (Estado: OPEN → IN_PROGRESS)"
    """
    from apps.logs.models import ActivityLog
    
    entity_display_name = build_ticket_display_name(ticket_id, title)
    
    # Build changes
    changes = ChangeSet()
    changes.add('status', from_status, to_status, 'Estado')
    
    # Generate human-readable message
    actor_name = build_actor_display_name(actor)
    human_readable = (
        f"{actor_name} cambió el estado de {from_status} a {to_status} "
        f"en {entity_display_name}"
    )
    
    ActivityLog.objects.create(
        user=actor,
        action='TICKET_STATUS_CHANGED',
        level='INFO',
        title=human_readable,
        description=human_readable,
        model_name='Ticket',
        object_id=ticket_id,
        object_repr=entity_display_name,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data=_extract_extra_data(actor, changes),
    )


def log_ticket_assigned(
    actor,
    ticket_id: int,
    title: str,
    assignee_username: str,
    request=None
):
    """
    Log ticket assignment with structured payload.
    
    Example Log Entry:
    "Juan Pérez asignó el ticket Ticket #19 – Printer offline a María García"
    """
    from apps.logs.models import ActivityLog
    
    entity_display_name = build_ticket_display_name(ticket_id, title)
    
    # Build changes
    changes = ChangeSet()
    changes.add('assigned_to', None, assignee_username, 'Asignado a')
    
    # Generate human-readable message
    actor_name = build_actor_display_name(actor)
    human_readable = f"{actor_name} asignó {entity_display_name} a {assignee_username}"
    
    ActivityLog.objects.create(
        user=actor,
        action='TICKET_ASSIGNED',
        level='INFO',
        title=human_readable,
        description=human_readable,
        model_name='Ticket',
        object_id=ticket_id,
        object_repr=entity_display_name,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data=_extract_extra_data(actor, changes),
    )


# =============================================================================
# Asset Logging Functions
# =============================================================================

def log_asset_created(
    actor,
    asset_id: int,
    name: str,
    asset_type: str = None,
    status: str = None,
    request=None
):
    """
    Log asset creation with structured payload.
    
    Example Log Entry:
    "Juan Pérez creó el asset Asset #LAPTOP-001 – MacBook Pro 16\""
    """
    from apps.logs.models import ActivityLog
    
    entity_display_name = build_asset_display_name(asset_id, name)
    
    # Build changes
    changes = ChangeSet()
    changes.add('name', None, name, 'Nombre')
    if asset_type:
        changes.add('asset_type', None, asset_type, 'Tipo')
    if status:
        changes.add('status', None, status, 'Estado')
    
    # Generate human-readable message
    actor_name = build_actor_display_name(actor)
    human_readable = f"{actor_name} creó el asset {entity_display_name}"
    
    ActivityLog.objects.create(
        user=actor,
        action='ASSET_CREATED',
        level='INFO',
        title=human_readable,
        description=human_readable,
        model_name='Asset',
        object_id=asset_id,
        object_repr=entity_display_name,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data=_extract_extra_data(actor, changes),
    )


def log_asset_assigned(
    actor,
    asset_id: int,
    name: str,
    assignee_username: str,
    request=None
):
    """
    Log asset assignment with structured payload.
    
    Example Log Entry:
    "Juan Pérez asignó el asset Asset #LAPTOP-001 – MacBook Pro 16\" a María García"
    
    Before (Broken):
    ❌ "Asset updated (ID 7)"
    
    After (Fixed):
    ✅ "Juan Pérez asignó el asset Asset #LAPTOP-001 – MacBook Pro 16\" a María García"
    """
    from apps.logs.models import ActivityLog
    
    entity_display_name = build_asset_display_name(asset_id, name)
    
    # Build changes
    changes = ChangeSet()
    changes.add('assigned_to', None, assignee_username, 'Asignado a')
    
    # Generate human-readable message
    actor_name = build_actor_display_name(actor)
    human_readable = f"{actor_name} asignó {entity_display_name} a {assignee_username}"
    
    ActivityLog.objects.create(
        user=actor,
        action='ASSET_ASSIGNED',
        level='INFO',
        title=human_readable,
        description=human_readable,
        model_name='Asset',
        object_id=asset_id,
        object_repr=entity_display_name,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data=_extract_extra_data(actor, changes),
    )


def log_asset_status_changed(
    actor,
    asset_id: int,
    name: str,
    from_status: str,
    to_status: str,
    request=None
):
    """
    Log asset status change with structured payload.
    """
    from apps.logs.models import ActivityLog
    
    entity_display_name = build_asset_display_name(asset_id, name)
    
    # Build changes
    changes = ChangeSet()
    changes.add('status', from_status, to_status, 'Estado')
    
    # Generate human-readable message
    actor_name = build_actor_display_name(actor)
    human_readable = f"{actor_name} cambió el estado de {from_status} a {to_status} en {entity_display_name}"
    
    ActivityLog.objects.create(
        user=actor,
        action='ASSET_STATUS_CHANGED',
        level='INFO',
        title=human_readable,
        description=human_readable,
        model_name='Asset',
        object_id=asset_id,
        object_repr=entity_display_name,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data=_extract_extra_data(actor, changes),
    )


# =============================================================================
# User Logging Functions
# =============================================================================

def log_user_created(
    actor,
    user_id: int,
    username: str,
    role: str = None,
    request=None
):
    """
    Log user creation with structured payload.
    
    Example Log Entry:
    "Admin Sistema creó el usuario Usuario: carlos_rodriguez"
    """
    from apps.logs.models import ActivityLog
    
    entity_display_name = build_user_display_name(user_id, username)
    
    # Build changes
    changes = ChangeSet()
    changes.add('username', None, username, 'Usuario')
    if role:
        changes.add('role', None, role, 'Rol')
    
    # Generate human-readable message
    actor_name = build_actor_display_name(actor)
    human_readable = f"{actor_name} creó el usuario {entity_display_name}"
    
    ActivityLog.objects.create(
        user=actor,
        action='USER_CREATED',
        level='INFO',
        title=human_readable,
        description=human_readable,
        model_name='User',
        object_id=user_id,
        object_repr=entity_display_name,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data=_extract_extra_data(actor, changes),
    )


def log_user_role_changed(
    actor,
    user_id: int,
    username: str,
    from_role: str,
    to_role: str,
    request=None
):
    """
    Log user role change with structured payload.
    
    Example Log Entry:
    "Admin Sistema cambió el rol del usuario Usuario: carlos_rodriguez (Rol: TECHNICIAN → MANAGER)"
    
    Before (Broken):
    ❌ "User updated (ID 25)"
    
    After (Fixed):
    ✅ "Admin Sistema cambió el rol del usuario Usuario: carlos_rodriguez (Rol: TECHNICIAN → MANAGER)"
    
    This is SECURITY-SENSITIVE and should be logged with appropriate visibility.
    """
    from apps.logs.models import ActivityLog
    
    entity_display_name = build_user_display_name(user_id, username)
    
    # Build changes
    changes = ChangeSet()
    changes.add('role', from_role, to_role, 'Rol')
    
    # Generate human-readable message
    actor_name = build_actor_display_name(actor)
    human_readable = (
        f"{actor_name} cambió el rol de {from_role} a {to_role} "
        f"para {entity_display_name}"
    )
    
    ActivityLog.objects.create(
        user=actor,
        action='USER_ROLE_CHANGED',
        level='WARNING',  # Role changes are security-sensitive
        title=human_readable,
        description=human_readable,
        model_name='User',
        object_id=user_id,
        object_repr=entity_display_name,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data=_extract_extra_data(actor, changes),
    )


# =============================================================================
# Project Logging Functions
# =============================================================================

def log_project_created(
    actor,
    project_id: int,
    name: str,
    request=None
):
    """
    Log project creation with structured payload.
    
    Example Log Entry:
    "Juan Pérez creó el proyecto Proyecto #3 – Migración a la Nube"
    """
    from apps.logs.models import ActivityLog
    
    entity_display_name = build_project_display_name(project_id, name)
    
    # Build changes
    changes = ChangeSet()
    changes.add('name', None, name, 'Nombre')
    
    # Generate human-readable message
    actor_name = build_actor_display_name(actor)
    human_readable = f"{actor_name} creó el proyecto {entity_display_name}"
    
    ActivityLog.objects.create(
        user=actor,
        action='PROJECT_CREATED',
        level='INFO',
        title=human_readable,
        description=human_readable,
        model_name='Project',
        object_id=project_id,
        object_repr=entity_display_name,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data=_extract_extra_data(actor, changes),
    )


def log_project_member_added(
    actor,
    project_id: int,
    project_name: str,
    member_username: str,
    role: str,
    request=None
):
    """
    Log project member addition with structured payload.
    
    Example Log Entry:
    "Juan Pérez agregó a María García al proyecto Proyecto #3 como MANAGER"
    """
    from apps.logs.models import ActivityLog
    
    entity_display_name = build_project_display_name(project_id, project_name)
    
    # Build changes
    changes = ChangeSet()
    changes.add('member', None, member_username, 'Miembro agregado')
    changes.add('role', None, role, 'Rol asignado')
    
    # Generate human-readable message
    actor_name = build_actor_display_name(actor)
    human_readable = f"{actor_name} agregó a {member_username} a {entity_display_name} como {role}"
    
    ActivityLog.objects.create(
        user=actor,
        action='PROJECT_MEMBER_ADDED',
        level='INFO',
        title=human_readable,
        description=human_readable,
        model_name='Project',
        object_id=project_id,
        object_repr=entity_display_name,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data=_extract_extra_data(actor, changes),
    )


# =============================================================================
# Auth Logging Functions
# =============================================================================

def log_user_login(user, request=None):
    """
    Log user login with structured payload.
    
    Example Log Entry:
    "Juan Pérez inició sesión"
    """
    from apps.logs.models import ActivityLog
    
    actor_name = build_actor_display_name(user)
    entity_display_name = build_user_display_name(user.id, getattr(user, 'username', None))
    
    human_readable = f"{actor_name} inició sesión"
    
    ActivityLog.objects.create(
        user=user,
        action='USER_LOGIN',
        level='INFO',
        title=human_readable,
        description=human_readable,
        model_name='User',
        object_id=user.id,
        object_repr=entity_display_name,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data=_extract_extra_data(user),
    )


def log_user_logout(user, request=None):
    """
    Log user logout with structured payload.
    
    Example Log Entry:
    "Juan Pérez cerró sesión"
    """
    from apps.logs.models import ActivityLog
    
    actor_name = build_actor_display_name(user)
    entity_display_name = build_user_display_name(user.id, getattr(user, 'username', None))
    
    human_readable = f"{actor_name} cerró sesión"
    
    ActivityLog.objects.create(
        user=user,
        action='USER_LOGOUT',
        level='INFO',
        title=human_readable,
        description=human_readable,
        model_name='User',
        object_id=user.id,
        object_repr=entity_display_name,
        ip_address=_get_client_ip(request),
        user_agent=_get_user_agent(request),
        extra_data=_extract_extra_data(user),
    )

