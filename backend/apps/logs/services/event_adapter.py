"""
EventAdapter - Adapter pattern for normalizing logs to structured events.

Provides backward-compatible access to log entries by normalizing
legacy fields to the structured event format. Older logs that lack
fields will fall back gracefully without crashing.

Usage:
    adapter = EventAdapter(log_entry)
    event = adapter.to_structured_event()
    
    # Access structured fields with fallbacks
    category = adapter.get_event_category()
    actor_snapshot = adapter.get_actor_snapshot()
    target_snapshot = adapter.get_target_snapshot()
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from apps.logs.models import ActivityLog
from apps.logs.enums import EventCategory


@dataclass
class StructuredEvent:
    """
    Normalized structured event representation.
    
    All logs are normalized to this format for consistent access.
    """
    log_id: UUID
    event_category: str
    event_code: str
    severity: str
    occurred_at: datetime
    actor_snapshot: Dict[str, Any]
    target_snapshot: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: str = ''
    title: str = ''
    
    # Legacy fields (for backward compatibility)
    legacy_action: str = ''
    legacy_level: str = ''
    legacy_user_id: Optional[int] = None
    legacy_ip_address: Optional[str] = None
    
    # Display properties
    SEVERITY_LABELS = {
        'INFO': 'Info',
        'WARNING': 'Warning',
        'ERROR': 'Error',
        'CRITICAL': 'Critical',
    }
    
    ROLE_LABELS = {
        'SUPERADMIN': 'Super Admin',
        'IT_ADMIN': 'IT Admin',
        'MANAGER': 'Manager',
        'TECHNICIAN': 'Technician',
        'VIEWER': 'Viewer',
    }
    
    @property
    def is_security_event(self) -> bool:
        return self.event_category == EventCategory.SECURITY.value
    
    @property
    def is_error_event(self) -> bool:
        return self.severity in ['ERROR', 'CRITICAL']
    
    @property
    def actor_id(self) -> Optional[str]:
        return self.actor_snapshot.get('id')
    
    @property
    def actor_name(self) -> str:
        return self.actor_snapshot.get('name', 'Unknown')
    
    @property
    def actor_role(self) -> str:
        return self.actor_snapshot.get('role', 'VIEWER')
    
    @property
    def severity_display(self) -> str:
        """Get human-readable severity label."""
        return self.SEVERITY_LABELS.get(self.severity, self.severity)
    
    @property
    def actor_role_display(self) -> str:
        """Get human-readable role label."""
        return self.ROLE_LABELS.get(self.actor_role, self.actor_role)
    
    @property
    def target_type(self) -> Optional[str]:
        return self.target_snapshot.get('type') if self.target_snapshot else None
    
    @property
    def target_id(self) -> Optional[int]:
        return self.target_snapshot.get('id') if self.target_snapshot else None
    
    @property
    def target_name(self) -> Optional[str]:
        """Get human-readable target name from snapshot."""
        if not self.target_snapshot:
            return None
        # Use 'repr' if available, otherwise combine type and id
        repr_val = self.target_snapshot.get('repr')
        if repr_val:
            return repr_val
        # Fallback: create name from type and id
        target_type = self.target_snapshot.get('type')
        target_id = self.target_snapshot.get('id')
        if target_type and target_id:
            return f"{target_type.title()} #{target_id}"
        return target_type or None
    
    @property
    def ip_address(self) -> Optional[str]:
        """Get IP address from legacy field."""
        return self.legacy_ip_address


class EventAdapter:
    """
    Adapter for normalizing ActivityLog entries to structured events.
    
    Handles backward compatibility by gracefully falling back for
    older logs that lack the new structured fields.
    """
    
    def __init__(self, log_entry: ActivityLog):
        """
        Initialize adapter with a log entry.
        
        Args:
            log_entry: ActivityLog instance to adapt
        """
        self._log = log_entry
    
    def to_structured_event(self) -> StructuredEvent:
        """
        Convert log entry to structured event format.
        
        Returns:
            StructuredEvent with all fields normalized
        """
        return StructuredEvent(
            log_id=self._log.log_id,
            event_category=self.get_event_category(),
            event_code=self.get_event_code(),
            severity=self.get_severity(),
            occurred_at=self._log.timestamp,
            actor_snapshot=self.get_actor_snapshot(),
            target_snapshot=self.get_target_snapshot(),
            metadata=self.get_metadata(),
            description=self._log.description or '',
            title=self._log.title or '',
            legacy_action=self._log.action or '',
            legacy_level=self._log.level or 'INFO',
            legacy_user_id=self._log.user.id if self._log.user else None,
            legacy_ip_address=self._log.ip_address,
        )
    
    def get_event_category(self) -> str:
        """
        Get event category with fallback logic.
        
        Returns:
            Event category string (ACTIVITY, SECURITY, SYSTEM, AUDIT, ERROR)
        """
        # Check for structured field first
        if hasattr(self._log, 'event_category') and self._log.event_category:
            return self._log.event_category
        
        # Fallback: infer from legacy action
        if self._log.action:
            return EventCategory.from_action(self._log.action).value
        
        # Fallback: infer from legacy level
        if self._log.level:
            return EventCategory.from_level(self._log.level).value
        
        # Default
        return EventCategory.ACTIVITY.value
    
    def get_event_code(self) -> str:
        """
        Get machine-readable event code.
        
        Returns:
            Event code string (e.g., 'TICKET_CREATED', 'USER_LOGIN')
        """
        # Check for structured field first
        if hasattr(self._log, 'event_type') and self._log.event_type:
            return self._log.event_type
        
        # Fallback: use legacy action
        return self._log.action or 'UNKNOWN'
    
    def get_severity(self) -> str:
        """
        Get severity level with fallback logic.
        
        Returns:
            Severity string (INFO, WARNING, ERROR, CRITICAL)
        """
        # Check for structured field first
        if hasattr(self._log, 'severity') and self._log.severity:
            return self._log.severity
        
        # Fallback: map legacy level to severity
        level_severity_map = {
            'DEBUG': 'INFO',
            'INFO': 'INFO',
            'WARNING': 'WARNING',
            'ERROR': 'ERROR',
            'CRITICAL': 'CRITICAL',
        }
        return level_severity_map.get(self._log.level, 'INFO')
    
    def get_actor_snapshot(self) -> Dict[str, Any]:
        """
        Get actor snapshot (immutable at log time).
        
        Returns:
            Dictionary with actor information
        """
        # Check for structured field first
        if hasattr(self._log, 'actor_snapshot') and self._log.actor_snapshot:
            return self._log.actor_snapshot
        
        # Fallback: build from legacy actor fields
        snapshot = {
            'type': getattr(self._log, 'actor_type', 'user'),
            'id': getattr(self._log, 'actor_id', None),
            'name': getattr(self._log, 'actor_name', None),
            'role': getattr(self._log, 'actor_role', None),
        }
        
        # If legacy actor fields are empty, try FK
        if not snapshot['name'] and self._log.user:
            snapshot['name'] = self._log.user.username
            snapshot['id'] = str(self._log.user.id)
            snapshot['role'] = getattr(self._log.user, 'role', 'VIEWER')
        
        # Clean up None values
        return {k: v for k, v in snapshot.items() if v is not None}
    
    def get_target_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        Get target snapshot (what was affected).
        
        Returns:
            Dictionary with target information or None
        """
        # Check for structured field first
        if hasattr(self._log, 'target_snapshot') and self._log.target_snapshot:
            return self._log.target_snapshot
        
        # Fallback: build from legacy entity fields
        entity_type = self._log.entity_type or self._log.model_name
        entity_id = self._log.entity_id or self._log.object_id
        
        if not entity_type:
            return None
        
        snapshot = {
            'type': entity_type.lower() if entity_type else None,
            'id': entity_id,
            'repr': self._log.object_repr or None,
        }
        
        # Clean up None values
        return {k: v for k, v in snapshot.items() if v is not None}
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get event metadata.
        
        Returns:
            Dictionary with additional metadata
        """
        # Check for structured field first
        if hasattr(self._log, 'metadata') and self._log.metadata:
            return self._log.metadata
        
        # Fallback: use extra_data
        return self._log.extra_data or {}
    
    def get_category_label(self) -> str:
        """
        Get human-readable category label.
        
        Returns:
            Formatted category label
        """
        category = self.get_event_category()
        labels = {
            'ACTIVITY': 'Activity',
            'SECURITY': 'Security',
            'SYSTEM': 'System',
            'AUDIT': 'Audit',
            'ERROR': 'Error',
        }
        return labels.get(category, category)
    
    def get_severity_label(self) -> str:
        """
        Get human-readable severity label.
        
        Returns:
            Formatted severity label
        """
        severity = self.get_severity()
        labels = {
            'INFO': 'Info',
            'WARNING': 'Warning',
            'ERROR': 'Error',
            'CRITICAL': 'Critical',
        }
        return labels.get(severity, severity)
    
    def get_severity_color(self) -> str:
        """
        Get Tailwind color class for severity.
        
        Returns:
            Color class string
        """
        severity = self.get_severity()
        colors = {
            'INFO': 'bg-blue-100 text-blue-800',
            'WARNING': 'bg-yellow-100 text-yellow-800',
            'ERROR': 'bg-red-100 text-red-800',
            'CRITICAL': 'bg-red-100 text-red-800',
        }
        return colors.get(severity, 'bg-gray-100 text-gray-800')
    
    def get_category_color(self) -> str:
        """
        Get Tailwind color class for category.
        
        Returns:
            Color class string
        """
        category = self.get_event_category()
        return EventCategory(category).color_class
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary with all structured event data
        """
        event = self.to_structured_event()
        return {
            'log_id': str(event.log_id),
            'event_category': event.event_category,
            'event_code': event.event_code,
            'severity': event.severity,
            'occurred_at': event.occurred_at.isoformat(),
            'actor_snapshot': event.actor_snapshot,
            'target_snapshot': event.target_snapshot,
            'metadata': event.metadata,
            'description': event.description,
            'title': event.title,
            'is_security_event': event.is_security_event,
            'is_error_event': event.is_error_event,
            'actor_name': event.actor_name,
            'actor_role': event.actor_role,
        }


def adapt_log(log_entry: ActivityLog) -> StructuredEvent:
    """
    Convenience function to adapt a log entry.
    
    Args:
        log_entry: ActivityLog instance
        
    Returns:
        StructuredEvent instance
    """
    return EventAdapter(log_entry).to_structured_event()


def adapt_logs(log_entries: List[ActivityLog]) -> List[StructuredEvent]:
    """
    Convenience function to adapt multiple log entries.
    
    Args:
        log_entries: List of ActivityLog instances
        
    Returns:
        List of StructuredEvent instances
    """
    return [adapt_log(log) for log in log_entries]


class LogAdapterMixin:
    """
    Mixin for adding structured event access to existing views.
    
    Usage:
        class MyView(LogAdapterMixin, TemplateView):
            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                logs = ActivityLog.objects.all()[:10]
                context['structured_events'] = [self.adapt_log(log) for log in logs]
                return context
    """
    
    def adapt_log(self, log_entry: ActivityLog) -> StructuredEvent:
        """Adapt a single log entry."""
        return adapt_log(log_entry)
    
    def adapt_logs(self, log_entries: List[ActivityLog]) -> List[StructuredEvent]:
        """Adapt multiple log entries."""
        return adapt_logs(log_entries)
    
    def get_structured_events(
        self, 
        queryset,
        limit: int = 100
    ) -> List[StructuredEvent]:
        """
        Get structured events from a queryset.
        
        Args:
            queryset: ActivityLog queryset
            limit: Maximum number of events
            
        Returns:
            List of StructuredEvent instances
        """
        logs = list(queryset[:limit])
        return self.adapt_logs(logs)
