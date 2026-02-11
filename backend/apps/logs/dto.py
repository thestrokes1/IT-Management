"""
Data Transfer Objects for Activity Logging.

Provides structured data classes for activity and security event data
that can be used across services, views, and templates.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
from uuid import UUID


# =============================================================================
# Activity Log DTOs
# =============================================================================

@dataclass
class ActivityDetailDTO:
    """DTO for detailed activity information."""
    log_id: UUID
    timestamp: datetime
    actor_username: str
    actor_role: str
    action: str
    action_label: str
    target_type: str
    target_id: Optional[int]
    target_name: str
    description: str
    metadata: Dict[str, Any]
    ip_address: Optional[str]
    level: str
    severity_badge: str = field(init=False)
    
    def __post_init__(self):
        self.severity_badge = self._get_severity_class(self.level)
    
    @staticmethod
    def _get_severity_class(level: str) -> str:
        severity_map = {
            'DEBUG': 'bg-gray-100 text-gray-800',
            'INFO': 'bg-blue-100 text-blue-800',
            'WARNING': 'bg-yellow-100 text-yellow-800',
            'ERROR': 'bg-red-100 text-red-800',
            'CRITICAL': 'bg-red-100 text-red-800',
        }
        return severity_map.get(level, 'bg-gray-100 text-gray-800')
    
    @property
    def is_error(self) -> bool:
        return self.level in ['ERROR', 'CRITICAL']
    
    @property
    def formatted_timestamp(self) -> str:
        return self.timestamp.strftime('%Y-%m-%d %H:%M')


@dataclass
class ActivitySummaryDTO:
    """DTO for activity summary statistics."""
    total_activities_today: int = 0
    total_activities_week: int = 0
    total_activities_month: int = 0
    activities_by_type: Dict[str, int] = field(default_factory=dict)
    activities_by_level: Dict[str, int] = field(default_factory=dict)
    activities_by_user: Dict[str, int] = field(default_factory=dict)
    top_actions: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def activity_growth_rate(self) -> float:
        if self.total_activities_week == 0:
            return 0.0
        return round(
            (self.total_activities_week - self.total_activities_today * 7) 
            / max(self.total_activities_today * 7, 1) * 100, 
            2
        )


@dataclass
class ActivityCreateDTO:
    """DTO for creating new activity entries."""
    actor_id: Optional[int] = None
    action: str = ''
    target_type: str = ''
    target_id: Optional[int] = None
    target_name: str = ''
    description: str = ''
    metadata: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: str = ''
    level: str = 'INFO'
    category_id: Optional[int] = None
    
    def validate(self) -> List[str]:
        errors = []
        if not self.action:
            errors.append('Action is required')
        if not self.description:
            errors.append('Description is required')
        if self.level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            errors.append(f'Invalid level: {self.level}')
        return errors


# =============================================================================
# Security Event DTOs
# =============================================================================

@dataclass
class SecurityEventDetailDTO:
    """DTO for detailed security event information."""
    event_id: UUID
    detected_at: datetime
    event_type: str
    event_type_label: str
    severity: str
    severity_badge: str = field(init=False)
    status: str
    status_badge: str = field(init=False)
    title: str
    description: str
    affected_user: Optional[str]
    source_ip: Optional[str]
    assigned_to: Optional[str]
    resolution_notes: Optional[str]
    is_critical: bool = field(init=False)
    requires_attention: bool = field(init=False)
    
    def __post_init__(self):
        self.severity_badge = self._get_severity_class(self.severity)
        self.status_badge = self._get_status_class(self.status)
        self.is_critical = self.severity == 'CRITICAL'
        self.requires_attention = self.status in ['OPEN', 'INVESTIGATING']
    
    @staticmethod
    def _get_severity_class(severity: str) -> str:
        severity_map = {
            'LOW': 'bg-blue-100 text-blue-800',
            'MEDIUM': 'bg-yellow-100 text-yellow-800',
            'HIGH': 'bg-orange-100 text-orange-800',
            'CRITICAL': 'bg-red-100 text-red-800',
        }
        return severity_map.get(severity, 'bg-gray-100 text-gray-800')
    
    @staticmethod
    def _get_status_class(status: str) -> str:
        status_map = {
            'OPEN': 'bg-red-100 text-red-800',
            'INVESTIGATING': 'bg-yellow-100 text-yellow-800',
            'RESOLVED': 'bg-green-100 text-green-800',
            'FALSE_POSITIVE': 'bg-gray-100 text-gray-800',
            'CLOSED': 'bg-gray-100 text-gray-600',
        }
        return status_map.get(status, 'bg-gray-100 text-gray-800')
    
    @property
    def formatted_detected_at(self) -> str:
        return self.detected_at.strftime('%Y-%m-%d %H:%M')
    
    @property
    def time_since_detection(self) -> str:
        from django.utils.timesince import timesince
        return timesince(self.detected_at)


@dataclass
class SecurityEventSummaryDTO:
    """DTO for security events summary."""
    total_open: int = 0
    total_investigating: int = 0
    total_resolved: int = 0
    total_critical: int = 0
    total_high: int = 0
    events_by_type: Dict[str, int] = field(default_factory=dict)
    events_by_severity: Dict[str, int] = field(default_factory=dict)
    recent_critical: List[SecurityEventDetailDTO] = field(default_factory=list)
    
    @property
    def total_active(self) -> int:
        return self.total_open + self.total_investigating
    
    @property
    def is_healthy(self) -> bool:
        return self.total_critical == 0
    
    @property
    def severity_score(self) -> int:
        score = 0
        score += self.total_critical * 25
        score += self.total_high * 10
        score += self.total_open * 5
        score += self.total_investigating * 3
        return min(score, 100)


# =============================================================================
# Timeline DTOs
# =============================================================================

@dataclass
class TimelineEntryDTO:
    """DTO for timeline entries."""
    timestamp: datetime
    entry_type: str
    title: str
    description: str
    icon: str
    icon_color: str
    badge: Optional[str] = None
    badge_color: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def formatted_time(self) -> str:
        return self.timestamp.strftime('%H:%M')
    
    @property
    def formatted_date(self) -> str:
        return self.timestamp.strftime('%b %d, %Y')


@dataclass
class TimelineDTO:
    """DTO for timeline data."""
    entries: List[TimelineEntryDTO] = field(default_factory=list)
    has_more: bool = False
    next_cursor: Optional[str] = None
    
    @property
    def entry_count(self) -> int:
        return len(self.entries)
    
    def add_entry(self, entry: TimelineEntryDTO):
        self.entries.append(entry)
    
    def sort_by_timestamp(self, ascending: bool = False):
        self.entries.sort(
            key=lambda x: x.timestamp, 
            reverse=not ascending
        )


# =============================================================================
# Explainable Log Entry DTOs
# =============================================================================

@dataclass
class LogEntryDTO:
    """DTO for explainable log entries in the UI."""
    log_id: str
    timestamp: datetime
    actor_name: str
    actor_role: str
    actor_type: str
    event_type: str
    event_label: str
    action: str
    description: str
    entity_type: str
    entity_id: Optional[int]
    entity_name: str
    severity: str
    severity_label: str
    severity_icon: str
    severity_color: str
    intent: str
    intent_label: str
    intent_color: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)
    is_expanded: bool = False
    has_details: bool = False
    
    def __post_init__(self):
        self.event_label = self._get_event_label(self.event_type or self.action)
        self.severity_label = self._get_severity_label(self.severity)
        self.severity_icon = self._get_severity_icon(self.severity)
        self.severity_color = self._get_severity_color(self.severity)
        self.intent_label = self._get_intent_label(self.intent)
        self.intent_color = self._get_intent_color(self.intent)
        self.has_details = bool(self.extra_data)
    
    @staticmethod
    def _get_event_label(event_type: str) -> str:
        labels = {
            'TICKET_CREATED': 'Created ticket',
            'TICKET_UPDATED': 'Updated ticket',
            'TICKET_ASSIGNED': 'Assigned ticket',
            'TICKET_RESOLVED': 'Resolved ticket',
            'TICKET_REOPENED': 'Reopened ticket',
            'TICKET_CLOSED': 'Closed ticket',
            'ASSET_CREATED': 'Created asset',
            'ASSET_UPDATED': 'Updated asset',
            'ASSET_ASSIGNED': 'Assigned asset',
            'ASSET_RETURNED': 'Returned asset',
            'PROJECT_CREATED': 'Created project',
            'PROJECT_UPDATED': 'Updated project',
            'PROJECT_COMPLETED': 'Completed project',
            'USER_CREATED': 'Created user',
            'USER_LOGIN': 'User logged in',
            'USER_LOGOUT': 'User logged out',
            'USER_ROLE_CHANGED': 'Changed user role',
            'SYSTEM_STARTUP': 'System started',
            'SYSTEM_SHUTDOWN': 'System stopped',
            'BATCH_PROCESS_STARTED': 'Batch job started',
            'BATCH_PROCESS_COMPLETED': 'Batch job completed',
            'BATCH_PROCESS_FAILED': 'Batch job failed',
            'SECURITY_ALERT': 'Security alert',
            'FAILED_LOGIN': 'Failed login attempt',
            'UNAUTHORIZED_ACCESS': 'Unauthorized access',
            'CREATE': 'Created',
            'UPDATE': 'Updated',
            'DELETE': 'Deleted',
            'LOGIN': 'Logged in',
            'LOGOUT': 'Logged out',
        }
        return labels.get(event_type, event_type.replace('_', ' ').title())
    
    @staticmethod
    def _get_severity_label(severity: str) -> str:
        labels = {
            'INFO': 'Info',
            'WARNING': 'Warning',
            'ERROR': 'Error',
            'SECURITY': 'Security',
        }
        return labels.get(severity, severity)
    
    @staticmethod
    def _get_severity_icon(severity: str) -> str:
        icons = {
            'INFO': 'fa-info-circle',
            'WARNING': 'fa-exclamation-triangle',
            'ERROR': 'fa-times-circle',
            'SECURITY': 'fa-shield-alt',
        }
        return icons.get(severity, 'fa-circle')
    
    @staticmethod
    def _get_severity_color(severity: str) -> str:
        colors = {
            'INFO': 'text-blue-500 bg-blue-100',
            'WARNING': 'text-yellow-500 bg-yellow-100',
            'ERROR': 'text-red-500 bg-red-100',
            'SECURITY': 'text-red-700 bg-red-100',
        }
        return colors.get(severity, 'text-gray-500 bg-gray-100')
    
    @staticmethod
    def _get_intent_label(intent: str) -> str:
        labels = {
            'workflow': 'Workflow',
            'sla_risk': 'SLA Risk',
            'security': 'Security',
            'system': 'System',
        }
        return labels.get(intent, intent.title())
    
    @staticmethod
    def _get_intent_color(intent: str) -> str:
        colors = {
            'workflow': 'bg-blue-100 text-blue-800',
            'sla_risk': 'bg-orange-100 text-orange-800',
            'security': 'bg-red-100 text-red-800',
            'system': 'bg-gray-100 text-gray-800',
        }
        return colors.get(intent, 'bg-gray-100 text-gray-800')
    
    @property
    def formatted_timestamp(self) -> str:
        return self.timestamp.strftime('%b %d, %Y %H:%M')
    
    @property
    def time_ago(self) -> str:
        from django.utils.timesince import timesince
        return timesince(self.timestamp)
    
    @property
    def actor_display(self) -> str:
        return f"{self.actor_name} ({self.actor_role})"
    
    @property
    def entity_display(self) -> str:
        if self.entity_type and self.entity_id:
            return f"{self.entity_type.capitalize()} #{self.entity_id}"
        return self.entity_name or self.entity_type or 'System'


@dataclass
class LogEntryDiffDTO:
    """DTO for rendering field-level diffs in templates."""
    entity_type: str
    entity_id: Optional[int]
    changes: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0
    
    @property
    def change_count(self) -> int:
        return len(self.changes)
    
    @property
    def changes_summary(self) -> str:
        if not self.changes:
            return "No changes"
        fields = [c['field'] for c in self.changes]
        return ", ".join(fields)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'changes': self.changes,
            'change_count': self.change_count,
        }
    
    @classmethod
    def from_extra_data(cls, extra_data: Dict[str, Any]) -> Optional['LogEntryDiffDTO']:
        diff_data = extra_data.get('diff')
        if not diff_data:
            return None
        
        return cls(
            entity_type=diff_data.get('entity_type', ''),
            entity_id=diff_data.get('entity_id'),
            changes=diff_data.get('changes', []),
        )


# =============================================================================
# Security Event Create DTO
# =============================================================================

@dataclass(frozen=True)
class SecurityEventCreateDTO:
    """DTO for creating new security events."""
    event_type: str
    severity: str
    actor_type: str
    actor_display_name: str
    narrative_message: str
    actor_role_snapshot: Optional[str] = None
    target_type: Optional[str] = None
    target_identifier: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        errors = []
        if not self.event_type:
            errors.append('event_type is required')
        if not self.severity:
            errors.append('severity is required')
        if not self.actor_type:
            errors.append('actor_type is required')
        if not self.actor_display_name:
            errors.append('actor_display_name is required')
        if not self.narrative_message:
            errors.append('narrative_message is required')
        
        valid_severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        if self.severity and self.severity not in valid_severities:
            errors.append(f'Invalid severity: {self.severity}. Must be one of {valid_severities}')
        
        valid_actor_types = ['user', 'system', 'automation', 'api', 'anonymous']
        if self.actor_type and self.actor_type not in valid_actor_types:
            errors.append(f'Invalid actor_type: {self.actor_type}. Must be one of {valid_actor_types}')
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'severity': self.severity,
            'actor_type': self.actor_type,
            'actor_display_name': self.actor_display_name,
            'actor_role_snapshot': self.actor_role_snapshot,
            'target_type': self.target_type,
            'target_identifier': self.target_identifier,
            'narrative_message': self.narrative_message,
            'extra_data': self.extra_data,
        }


# =============================================================================
# Security Event Update DTO
# =============================================================================

@dataclass
class SecurityEventUpdateDTO:
    """DTO for updating security events."""
    status: Optional[str] = None
    resolution_notes: Optional[str] = None
    assigned_to: Optional[str] = None
    severity: Optional[str] = None
    
    def validate(self) -> List[str]:
        errors = []
        if self.status:
            valid_statuses = ['OPEN', 'INVESTIGATING', 'RESOLVED', 'FALSE_POSITIVE', 'CLOSED']
            if self.status not in valid_statuses:
                errors.append(f'Invalid status: {self.status}. Must be one of {valid_statuses}')
        
        if self.severity:
            valid_severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            if self.severity not in valid_severities:
                errors.append(f'Invalid severity: {self.severity}. Must be one of {valid_severities}')
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        result = {}
        if self.status is not None:
            result['status'] = self.status
        if self.resolution_notes is not None:
            result['resolution_notes'] = self.resolution_notes
        if self.assigned_to is not None:
            result['assigned_to'] = self.assigned_to
        if self.severity is not None:
            result['severity'] = self.severity
        return result


# =============================================================================
# Structured Event DTO - Unified Event Format
# =============================================================================

@dataclass
class StructuredEventDTO:
    """
    DTO for normalized structured events.
    
    This is the canonical format for all log entries, providing:
    - event_category: ACTIVITY, SECURITY, SYSTEM, AUDIT, ERROR
    - event_code: Machine-readable code (e.g., 'TICKET_CREATED')
    - severity: INFO, WARNING, CRITICAL
    - occurred_at: Immutable timestamp
    - actor_snapshot: Dict with actor info (id, name, role)
    - target_snapshot: Optional Dict with target info
    - metadata: Additional JSON data
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
    
    @property
    def is_security_event(self) -> bool:
        return self.event_category == 'SECURITY'
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'log_id': str(self.log_id),
            'event_category': self.event_category,
            'event_code': self.event_code,
            'severity': self.severity,
            'occurred_at': self.occurred_at.isoformat(),
            'actor_snapshot': self.actor_snapshot,
            'target_snapshot': self.target_snapshot,
            'metadata': self.metadata,
            'description': self.description,
            'title': self.title,
            'is_security_event': self.is_security_event,
            'is_error_event': self.is_error_event,
            'actor_name': self.actor_name,
            'actor_role': self.actor_role,
        }
    
    @classmethod
    def from_activity_log(cls, log) -> 'StructuredEventDTO':
        """
        Create DTO from ActivityLog model.
        
        This provides backward compatibility by extracting/deriving
        structured fields from legacy ActivityLog fields.
        """
        from apps.logs.enums import EventCategory
        
        # Determine event_category
        if hasattr(log, 'event_category') and log.event_category:
            event_category = log.event_category
        elif log.action:
            event_category = EventCategory.from_action(log.action).value
        else:
            event_category = EventCategory.ACTIVITY.value
        
        # Determine event_code
        if hasattr(log, 'event_type') and log.event_type:
            event_code = log.event_type
        else:
            event_code = log.action or 'UNKNOWN'
        
        # Determine severity
        if hasattr(log, 'severity') and log.severity:
            severity = log.severity
        else:
            level_severity_map = {
                'DEBUG': 'INFO',
                'INFO': 'INFO',
                'WARNING': 'WARNING',
                'ERROR': 'ERROR',
                'CRITICAL': 'CRITICAL',
            }
            severity = level_severity_map.get(log.level, 'INFO')
        
        # Build actor_snapshot
        actor_snapshot = {}
        if hasattr(log, 'actor_snapshot') and log.actor_snapshot:
            actor_snapshot = log.actor_snapshot
        else:
            actor_snapshot = {
                'type': getattr(log, 'actor_type', 'user'),
                'id': getattr(log, 'actor_id', None),
                'name': getattr(log, 'actor_name', None),
                'role': getattr(log, 'actor_role', None),
            }
            if not actor_snapshot['name'] and log.user:
                actor_snapshot['name'] = log.user.username
                actor_snapshot['id'] = str(log.user.id)
                actor_snapshot['role'] = getattr(log.user, 'role', 'VIEWER')
            actor_snapshot = {k: v for k, v in actor_snapshot.items() if v is not None}
        
        # Build target_snapshot
        target_snapshot = None
        entity_type = log.entity_type or log.model_name
        entity_id = log.entity_id or log.object_id
        if entity_type:
            target_snapshot = {
                'type': entity_type.lower(),
                'id': entity_id,
                'repr': log.object_repr or None,
            }
            target_snapshot = {k: v for k, v in target_snapshot.items() if v is not None}
        
        return cls(
            log_id=log.log_id,
            event_category=event_category,
            event_code=event_code,
            severity=severity,
            occurred_at=log.timestamp,
            actor_snapshot=actor_snapshot,
            target_snapshot=target_snapshot,
            metadata=getattr(log, 'metadata', None) or log.extra_data or {},
            description=log.description or '',
            title=log.title or '',
        )
