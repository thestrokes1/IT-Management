"""
Activity Adapter Service for IT Management Platform.

Transforms ActivityLog model instances into UI-ready data structures.
遵循 Clean Architecture - adapters prepare data for presentation layer.

Key Principles:
- Transforms model data for template/API consumption
- Generates human-readable text at adaptation time
- Handles backward compatibility for legacy logs
- No business logic - pure data transformation

THIS IS THE SINGLE CANONICAL SOURCE for UI log representations.
All views MUST use ActivityAdapter.to_ui() to create UI objects.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from django.utils import timezone
from django.utils.timesince import timesince


# =============================================================================
# UI Data Transfer Objects
# =============================================================================

@dataclass
class ActivityUIData:
    """
    Frontend-ready activity data for Recent Activity UI.
    
    All fields are pre-computed for template rendering.
    No template logic or business decisions allowed here.
    
    This is the SINGLE canonical UI representation for log entries.
    Views MUST use ActivityAdapter.to_ui() to create these objects.
    """
    # Identifiers
    log_id: str
    timestamp: datetime
    timestamp_iso: str
    timestamp_relative: str  # e.g., "5 minutes ago"
    formatted_timestamp: str   # e.g., "Feb 05, 2026 14:30"
    time_ago: str           # e.g., "2 hours ago"
    
    # Actor (WHO) - always null-safe
    actor_id: Optional[int]
    actor_name: str         # Human-readable name (never "Unknown ()")
    actor_role: str         # Human-readable role
    actor_url: Optional[str]  # /users/{id}/
    
    # Action (WHAT - verb phrase)
    action_key: str  # TICKET_STATUS_CHANGED
    action_verb: str  # "creó el ticket"
    action_icon: str  # "fa-plus-circle"
    action_color: str  # "text-green-600"
    action_bg_color: str  # "bg-green-100"
    
    # Entity (WHICH - target noun phrase)
    entity_type: str  # Ticket, Asset, Project, User
    entity_id: Optional[int]
    entity_display_name: str  # "Ticket #19 – Printer offline"
    entity_url: Optional[str]  # /tickets/19/
    
    # Narrative (complete sentence for display)
    narrative: str  # "John created a new ticket"
    
    # Severity (null-safe)
    severity: str  # INFO, WARNING, ERROR
    severity_label: str  # "Info", "Warning", "Error"
    severity_icon: str  # "fa-info-circle"
    severity_color: str  # "text-blue-500 bg-blue-100"
    
    # Intent (why the action was performed)
    intent: str  # workflow, sla_risk, security, system
    intent_label: str  # "Workflow", "SLA Risk", etc.
    intent_color: str  # "bg-blue-100 text-blue-800"
    
    # IP Address
    ip_address: Optional[str]
    
    # Changes (CONTEXT - optional before/after)
    changes_summary: Optional[str]  # "Estado: ABIERTO → RESUELTO"
    changes_detail: Optional[Dict[str, Any]]  # Full JSON for detail view
    
    # Category for styling
    category: str  # TICKET, ASSET, PROJECT, USER, SECURITY, SYSTEM
    
    # Computed UI flags
    is_clickable: bool
    is_error: bool
    has_details: bool
    
    class Meta:
        # Allow dict-like access for template compatibility
        slots = True


# =============================================================================
# Action Configuration - Source of Truth for UI Display
# =============================================================================

ACTION_CONFIG = {
    # Ticket Actions
    'TICKET_CREATED': {
        'verb': 'creó el ticket',
        'icon': 'fa-plus-circle',
        'color': 'text-green-600',
        'bg_color': 'bg-green-100',
        'entity_type': 'Ticket',
    },
    'TICKET_VIEWED': {
        'verb': 'visualizó el ticket',
        'icon': 'fa-eye',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
        'entity_type': 'Ticket',
    },
    'TICKET_UPDATED': {
        'verb': 'actualizó el ticket',
        'icon': 'fa-edit',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
        'entity_type': 'Ticket',
    },
    'TICKET_DELETED': {
        'verb': 'eliminó el ticket',
        'icon': 'fa-trash',
        'color': 'text-red-600',
        'bg_color': 'bg-red-100',
        'entity_type': 'Ticket',
    },
    'TICKET_STATUS_CHANGED': {
        'verb': 'cambió el estado del ticket',
        'icon': 'fa-exchange-alt',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
        'entity_type': 'Ticket',
    },
    'TICKET_PRIORITY_CHANGED': {
        'verb': 'cambió la prioridad del ticket',
        'icon': 'fa-exclamation-circle',
        'color': 'text-orange-600',
        'bg_color': 'bg-orange-100',
        'entity_type': 'Ticket',
    },
    'TICKET_ASSIGNED': {
        'verb': 'asignó el ticket',
        'icon': 'fa-user-plus',
        'color': 'text-purple-600',
        'bg_color': 'bg-purple-100',
        'entity_type': 'Ticket',
    },
    'TICKET_UNASSIGNED': {
        'verb': 'desasignó el ticket',
        'icon': 'fa-user-minus',
        'color': 'text-gray-600',
        'bg_color': 'bg-gray-100',
        'entity_type': 'Ticket',
    },
    'TICKET_RESOLVED': {
        'verb': 'resolvió el ticket',
        'icon': 'fa-check-circle',
        'color': 'text-green-600',
        'bg_color': 'bg-green-100',
        'entity_type': 'Ticket',
    },
    'TICKET_CLOSED': {
        'verb': 'cerró el ticket',
        'icon': 'fa-times-circle',
        'color': 'text-gray-600',
        'bg_color': 'bg-gray-100',
        'entity_type': 'Ticket',
    },
    'TICKET_REOPENED': {
        'verb': 'reabrió el ticket',
        'icon': 'fa-rotate-right',
        'color': 'text-yellow-600',
        'bg_color': 'bg-yellow-100',
        'entity_type': 'Ticket',
    },
    
    # Asset Actions
    'ASSET_CREATED': {
        'verb': 'creó el asset',
        'icon': 'fa-desktop',
        'color': 'text-green-600',
        'bg_color': 'bg-green-100',
        'entity_type': 'Asset',
    },
    'ASSET_VIEWED': {
        'verb': 'visualizó el asset',
        'icon': 'fa-eye',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
        'entity_type': 'Asset',
    },
    'ASSET_UPDATED': {
        'verb': 'actualizó el asset',
        'icon': 'fa-edit',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
        'entity_type': 'Asset',
    },
    'ASSET_DELETED': {
        'verb': 'eliminó el asset',
        'icon': 'fa-trash',
        'color': 'text-red-600',
        'bg_color': 'bg-red-100',
        'entity_type': 'Asset',
    },
    'ASSET_ASSIGNED': {
        'verb': 'asignó el asset',
        'icon': 'fa-hand-paper',
        'color': 'text-orange-600',
        'bg_color': 'bg-orange-100',
        'entity_type': 'Asset',
    },
    'ASSET_UNASSIGNED': {
        'verb': 'desasignó el asset',
        'icon': 'fa-hand-paper',
        'color': 'text-gray-600',
        'bg_color': 'bg-gray-100',
        'entity_type': 'Asset',
    },
    'ASSET_STATUS_CHANGED': {
        'verb': 'cambió el estado del asset',
        'icon': 'fa-exchange-alt',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
        'entity_type': 'Asset',
    },
    
    # Project Actions
    'PROJECT_CREATED': {
        'verb': 'creó el proyecto',
        'icon': 'fa-project-diagram',
        'color': 'text-green-600',
        'bg_color': 'bg-green-100',
        'entity_type': 'Project',
    },
    'PROJECT_VIEWED': {
        'verb': 'visualizó el proyecto',
        'icon': 'fa-eye',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
        'entity_type': 'Project',
    },
    'PROJECT_UPDATED': {
        'verb': 'actualizó el proyecto',
        'icon': 'fa-edit',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
        'entity_type': 'Project',
    },
    'PROJECT_DELETED': {
        'verb': 'eliminó el proyecto',
        'icon': 'fa-trash',
        'color': 'text-red-600',
        'bg_color': 'bg-red-100',
        'entity_type': 'Project',
    },
    'PROJECT_COMPLETED': {
        'verb': 'completó el proyecto',
        'icon': 'fa-check-double',
        'color': 'text-green-600',
        'bg_color': 'bg-green-100',
        'entity_type': 'Project',
    },
    'PROJECT_MEMBER_ADDED': {
        'verb': 'agregó miembro al proyecto',
        'icon': 'fa-user-plus',
        'color': 'text-purple-600',
        'bg_color': 'bg-purple-100',
        'entity_type': 'Project',
    },
    'PROJECT_MEMBER_REMOVED': {
        'verb': 'removió miembro del proyecto',
        'icon': 'fa-user-minus',
        'color': 'text-red-600',
        'bg_color': 'bg-red-100',
        'entity_type': 'Project',
    },
    'PROJECT_ROLE_CHANGED': {
        'verb': 'cambió el rol en el proyecto',
        'icon': 'fa-user-shield',
        'color': 'text-orange-600',
        'bg_color': 'bg-orange-100',
        'entity_type': 'Project',
    },
    
    # User Actions
    'USER_CREATED': {
        'verb': 'creó el usuario',
        'icon': 'fa-user-plus',
        'color': 'text-green-600',
        'bg_color': 'bg-green-100',
        'entity_type': 'User',
    },
    'USER_VIEWED': {
        'verb': 'visualizó el usuario',
        'icon': 'fa-eye',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
        'entity_type': 'User',
    },
    'USER_UPDATED': {
        'verb': 'actualizó el usuario',
        'icon': 'fa-edit',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
        'entity_type': 'User',
    },
    'USER_DELETED': {
        'verb': 'eliminó el usuario',
        'icon': 'fa-trash',
        'color': 'text-red-600',
        'bg_color': 'bg-red-100',
        'entity_type': 'User',
    },
    'USER_ROLE_CHANGED': {
        'verb': 'cambió el rol del usuario',
        'icon': 'fa-user-shield',
        'color': 'text-red-600',
        'bg_color': 'bg-red-100',
        'entity_type': 'User',
    },
    'USER_DEACTIVATED': {
        'verb': 'desactivó al usuario',
        'icon': 'fa-user-slash',
        'color': 'text-red-600',
        'bg_color': 'bg-red-100',
        'entity_type': 'User',
    },
    'USER_REACTIVATED': {
        'verb': 'reactivó al usuario',
        'icon': 'fa-user-check',
        'color': 'text-green-600',
        'bg_color': 'bg-green-100',
        'entity_type': 'User',
    },
    
    # Auth Actions
    'USER_LOGIN': {
        'verb': 'inició sesión',
        'icon': 'fa-sign-in-alt',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
        'entity_type': 'User',
    },
    'USER_LOGOUT': {
        'verb': 'cerró sesión',
        'icon': 'fa-sign-out-alt',
        'color': 'text-gray-600',
        'bg_color': 'bg-gray-100',
        'entity_type': 'User',
    },
    'PASSWORD_CHANGED': {
        'verb': 'cambió la contraseña',
        'icon': 'fa-key',
        'color': 'text-orange-600',
        'bg_color': 'bg-orange-100',
        'entity_type': 'User',
    },
    
    # Generic Actions (fallback)
    'CREATE': {
        'verb': 'creó',
        'icon': 'fa-plus',
        'color': 'text-green-600',
        'bg_color': 'bg-green-100',
        'entity_type': None,
    },
    'UPDATE': {
        'verb': 'actualizó',
        'icon': 'fa-edit',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
        'entity_type': None,
    },
    'DELETE': {
        'verb': 'eliminó',
        'icon': 'fa-trash',
        'color': 'text-red-600',
        'bg_color': 'bg-red-100',
        'entity_type': None,
    },
    'LOGIN': {
        'verb': 'inició sesión',
        'icon': 'fa-sign-in-alt',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
        'entity_type': None,
    },
    'LOGOUT': {
        'verb': 'cerró sesión',
        'icon': 'fa-sign-out-alt',
        'color': 'text-gray-600',
        'bg_color': 'bg-gray-100',
        'entity_type': None,
    },
}


# =============================================================================
# Severity Configuration
# =============================================================================

SEVERITY_CONFIG = {
    'INFO': {
        'label': 'Info',
        'icon': 'fa-info-circle',
        'color': 'text-blue-500 bg-blue-100',
    },
    'WARNING': {
        'label': 'Warning',
        'icon': 'fa-exclamation-triangle',
        'color': 'text-yellow-500 bg-yellow-100',
    },
    'ERROR': {
        'label': 'Error',
        'icon': 'fa-times-circle',
        'color': 'text-red-500 bg-red-100',
    },
    'CRITICAL': {
        'label': 'Critical',
        'icon': 'fa-exclamation-circle',
        'color': 'text-red-700 bg-red-100',
    },
    'SECURITY': {
        'label': 'Security',
        'icon': 'fa-shield-alt',
        'color': 'text-red-700 bg-red-100',
    },
}


# =============================================================================
# Intent Configuration
# =============================================================================

INTENT_CONFIG = {
    'workflow': {
        'label': 'Workflow',
        'color': 'bg-blue-100 text-blue-800',
    },
    'sla_risk': {
        'label': 'SLA Risk',
        'color': 'bg-orange-100 text-orange-800',
    },
    'security': {
        'label': 'Security',
        'color': 'bg-red-100 text-red-800',
    },
    'system': {
        'label': 'System',
        'color': 'bg-gray-100 text-gray-800',
    },
}


# =============================================================================
# Category Configuration
# =============================================================================

CATEGORY_CONFIG = {
    'TICKET': {
        'icon': 'fa-ticket-alt',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
    },
    'ASSET': {
        'icon': 'fa-desktop',
        'color': 'text-green-600',
        'bg_color': 'bg-green-100',
    },
    'PROJECT': {
        'icon': 'fa-project-diagram',
        'color': 'text-purple-600',
        'bg_color': 'bg-purple-100',
    },
    'USER': {
        'icon': 'fa-user',
        'color': 'text-orange-600',
        'bg_color': 'bg-orange-100',
    },
    'SECURITY': {
        'icon': 'fa-shield-alt',
        'color': 'text-red-600',
        'bg_color': 'bg-red-100',
    },
    'SYSTEM': {
        'icon': 'fa-cog',
        'color': 'text-gray-600',
        'bg_color': 'bg-gray-100',
    },
}


# =============================================================================
# URL Builders
# =============================================================================

ENTITY_URL_MAP = {
    'Ticket': ('frontend:ticket-detail', 'tickets'),
    'Asset': ('frontend:asset-detail', 'assets'),
    'Project': ('frontend:project-detail', 'projects'),
    'User': ('frontend:user-detail', 'users'),
    'ticket': ('frontend:ticket-detail', 'tickets'),
    'asset': ('frontend:asset-detail', 'assets'),
    'project': ('frontend:project-detail', 'projects'),
    'user': ('frontend:user-detail', 'users'),
}


def build_entity_url(entity_type: str, entity_id: Optional[int]) -> Optional[str]:
    """Build URL for entity detail page."""
    if not entity_id:
        return None
    
    # Normalize entity type
    normalized_type = entity_type.capitalize()
    url_info = ENTITY_URL_MAP.get(normalized_type) or ENTITY_URL_MAP.get(entity_type.lower())
    
    if url_info:
        return f"/{url_info[1]}/{entity_id}/"
    
    return None


def build_actor_url(actor_id: Optional[int]) -> Optional[str]:
    """Build URL for actor/user profile page."""
    if not actor_id:
        return None
    return f"/users/{actor_id}/"


# =============================================================================
# Change Summary Generator
# =============================================================================

def summarize_changes(changes: Optional[Dict[str, Any]]) -> Optional[str]:
    """Generate a human-readable summary of changes."""
    if not changes or not isinstance(changes, dict):
        return None
    
    # Try to get changes from extra_data first
    if 'changes' in changes:
        changes = changes['changes']
    
    parts = []
    for field_name, change in changes.items():
        if isinstance(change, dict):
            before = change.get('before')
            after = change.get('after')
            label = change.get('label', field_name)
            
            if before is not None and after is not None:
                parts.append(f"{label}: {before} → {after}")
            elif after is not None:
                parts.append(f"{label}: {after}")
        else:
            parts.append(f"{field_name}: {change}")
    
    return ', '.join(parts) if parts else None


# =============================================================================
# Narrative Generator
# =============================================================================

def generate_narrative(actor_name: str, action_verb: str, entity_type: str, entity_id: Optional[int] = None) -> str:
    """Generate a complete narrative sentence for the log entry."""
    if entity_type and entity_id:
        return f"{actor_name} {action_verb} {entity_type} #{entity_id}"
    elif entity_type:
        return f"{actor_name} {action_verb} {entity_type.lower()}"
    else:
        return f"{actor_name} {action_verb}"


# =============================================================================
# Main Adapter Class
# =============================================================================

class ActivityAdapter:
    """
    Service to adapt ActivityLog model instances for UI rendering.
    
    Usage:
        ui_data = ActivityAdapter.to_ui(activity_log_instance)
        
        # In template:
        {{ ui_data.narrative }}
        {{ ui_data.actor_name }} {{ ui_data.action_verb }} {{ ui_data.entity_display_name }}
    
    THIS IS THE SINGLE CANONICAL SOURCE for UI log representations.
    All views MUST use this method to create UI objects.
    """
    
    @staticmethod
    def to_ui(activity_log) -> ActivityUIData:
        """
        Transform ActivityLog model to UI-ready structure.
        
        All values are pre-computed and null-safe.
        Never returns None for required fields.
        
        Args:
            activity_log: ActivityLog model instance
            
        Returns:
            ActivityUIData: Pre-computed UI data
        """
        extra_data = activity_log.extra_data or {}
        
        # --- Actor (WHO) - null-safe ---
        actor_id = (
            activity_log.user_id or 
            extra_data.get('actor_id')
        )
        # Use actor_name from extra_data or FK, never return "Unknown"
        if activity_log.user:
            actor_name = activity_log.user.username
        else:
            actor_name = extra_data.get('actor_username') or 'System'
        
        # Use actor_role from FK or extra_data, never empty
        if activity_log.user:
            actor_role = activity_log.user.role or 'Viewer'
        else:
            actor_role = extra_data.get('actor_role') or ''
        
        actor_url = build_actor_url(actor_id)
        
        # --- Entity (WHICH) - null-safe ---
        entity_type = (
            activity_log.model_name or 
            extra_data.get('entity_type') or 
            'Unknown'
        )
        entity_id = activity_log.object_id
        
        # Build entity display name: repr > fallback > id
        if activity_log.object_repr:
            entity_display_name = activity_log.object_repr
        elif extra_data.get('entity_display_name'):
            entity_display_name = extra_data.get('entity_display_name')
        elif entity_type and entity_id:
            entity_display_name = f"{entity_type.title()} #{entity_id}"
        elif activity_log.title:
            entity_display_name = activity_log.title
        elif entity_type:
            entity_display_name = entity_type
        else:
            entity_display_name = 'System'
        
        entity_url = build_entity_url(entity_type, entity_id)
        
        # --- Action (WHAT) ---
        action_key = activity_log.action or 'UNKNOWN'
        action_config = ACTION_CONFIG.get(action_key, {
            'verb': action_key.replace('_', ' ').lower().capitalize(),
            'icon': 'fa-circle',
            'color': 'text-gray-600',
            'bg_color': 'bg-gray-100',
        })
        
        action_verb = action_config['verb']
        
        # --- Severity ---
        level = activity_log.level or 'INFO'
        severity_config = SEVERITY_CONFIG.get(level, {
            'label': level,
            'icon': 'fa-circle',
            'color': 'text-gray-500 bg-gray-100',
        })
        
        # --- Intent ---
        intent = activity_log.intent or 'workflow'
        intent_config = INTENT_CONFIG.get(intent, {
            'label': intent.title(),
            'color': 'bg-gray-100 text-gray-800',
        })
        
        # --- Category ---
        if activity_log.category:
            category = activity_log.category.name.upper()
        else:
            category = extra_data.get('category', entity_type.upper())
        
        # --- Changes ---
        changes = extra_data.get('changes') if isinstance(extra_data, dict) else None
        changes_summary = (
            extra_data.get('changes_summary') or 
            summarize_changes(changes) or
            summarize_changes(extra_data)
        )
        
        # --- Narrative ---
        narrative = generate_narrative(actor_name, action_verb, entity_type, entity_id)
        
        # --- Timestamps ---
        timestamp = activity_log.timestamp
        timestamp_iso = timestamp.isoformat()
        # Get relative time, handle edge cases
        try:
            timestamp_relative = timesince(timestamp, timezone.now())
            if ',' in timestamp_relative:
                timestamp_relative = timestamp_relative.split(',')[0] + ' ago'
            else:
                timestamp_relative = timestamp_relative + ' ago'
        except Exception:
            timestamp_relative = 'recently'
        
        formatted_timestamp = timestamp.strftime('%b %d, %Y %H:%M')
        
        # --- Computed flags ---
        is_clickable = bool(entity_url and entity_id)
        is_error = level in ('ERROR', 'CRITICAL')
        has_details = bool(changes_summary or extra_data)
        
        # --- IP Address ---
        ip_address = activity_log.ip_address
        
        return ActivityUIData(
            log_id=str(activity_log.log_id),
            timestamp=timestamp,
            timestamp_iso=timestamp_iso,
            timestamp_relative=timestamp_relative,
            formatted_timestamp=formatted_timestamp,
            time_ago=timestamp_relative,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_role=actor_role,
            actor_url=actor_url,
            action_key=action_key,
            action_verb=action_verb,
            action_icon=action_config['icon'],
            action_color=action_config['color'],
            action_bg_color=action_config['bg_color'],
            entity_type=entity_type,
            entity_id=entity_id,
            entity_display_name=entity_display_name,
            entity_url=entity_url,
            narrative=narrative,
            severity=level,
            severity_label=severity_config['label'],
            severity_icon=severity_config['icon'],
            severity_color=severity_config['color'],
            intent=intent,
            intent_label=intent_config['label'],
            intent_color=intent_config['color'],
            ip_address=ip_address,
            changes_summary=changes_summary,
            changes_detail=changes,
            category=category,
            is_clickable=is_clickable,
            is_error=is_error,
            has_details=has_details,
        )
    
    @staticmethod
    def to_dict(activity_log) -> Dict[str, Any]:
        """Transform ActivityLog model to dictionary for API."""
        ui_data = ActivityAdapter.to_ui(activity_log)
        
        return {
            'log_id': ui_data.log_id,
            'timestamp': ui_data.timestamp_iso,
            'actor': {
                'id': ui_data.actor_id,
                'name': ui_data.actor_name,
                'role': ui_data.actor_role,
                'url': ui_data.actor_url,
            },
            'action': {
                'key': ui_data.action_key,
                'verb': ui_data.action_verb,
                'icon': ui_data.action_icon,
                'color': ui_data.action_color,
            },
            'entity': {
                'type': ui_data.entity_type,
                'id': ui_data.entity_id,
                'display_name': ui_data.entity_display_name,
                'url': ui_data.entity_url,
            },
            'narrative': ui_data.narrative,
            'severity': {
                'level': ui_data.severity,
                'label': ui_data.severity_label,
                'icon': ui_data.severity_icon,
                'color': ui_data.severity_color,
            },
            'ip_address': ui_data.ip_address,
            'changes_summary': ui_data.changes_summary,
            'category': ui_data.category,
            'is_error': ui_data.is_error,
        }
    
    @staticmethod
    def adapt_queryset(queryset) -> List[ActivityUIData]:
        """Adapt a queryset of ActivityLog instances."""
        return [ActivityAdapter.to_ui(log) for log in queryset]


# =============================================================================
# Convenience Functions for Views
# =============================================================================

def get_recent_activities_for_dashboard(user, limit: int = 10) -> List[ActivityUIData]:
    """Get recent activities formatted for dashboard display."""
    from apps.logs.models import ActivityLog
    from django.db.models import Q
    
    qs = ActivityLog.objects.select_related('user', 'category')
    
    user_role = getattr(user, 'role', 'VIEWER') if user else None
    is_admin = user and (
        user.is_superuser or 
        user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
    )
    
    if not is_admin and user:
        qs = qs.filter(
            Q(user=user) |
            Q(extra_data__actor_id=user.id)
        )
    
    activities = qs.order_by('-timestamp')[:limit]
    return ActivityAdapter.adapt_queryset(activities)


def get_activity_for_detail(log_id: str) -> Optional[ActivityUIData]:
    """Get a single activity formatted for detail view."""
    from apps.logs.models import ActivityLog
    
    try:
        activity = ActivityLog.objects.select_related('user', 'category').get(log_id=log_id)
        return ActivityAdapter.to_ui(activity)
    except ActivityLog.DoesNotExist:
        return None

