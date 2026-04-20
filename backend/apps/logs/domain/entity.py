"""
Activity Log Domain Entity.

Framework-agnostic domain entity for activity logging.
Follows Clean Architecture - no Django ORM dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
import json


# =============================================================================
# Action Types (Domain Enums)
# =============================================================================

class ActionType:
    """Activity action types."""
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    DELETED = "DELETED"
    STATUS_CHANGED = "STATUS_CHANGED"
    ASSIGNED = "ASSIGNED"
    UNASSIGNED = "UNASSIGNED"
    RESOLVED = "RESOLVED"
    REOPENED = "REOPENED"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    
    @classmethod
    def choices(cls):
        return [
            cls.CREATED, cls.UPDATED, cls.DELETED,
            cls.STATUS_CHANGED, cls.ASSIGNED, cls.UNASSIGNED,
            cls.RESOLVED, cls.REOPENED, cls.LOGIN, cls.LOGOUT,
        ]


class EntityType:
    """Entity types that can be logged."""
    ASSET = "Asset"
    TICKET = "Ticket"
    PROJECT = "Project"
    USER = "User"
    
    @classmethod
    def choices(cls):
        return [cls.ASSET, cls.TICKET, cls.PROJECT, cls.USER]


# =============================================================================
# Domain Entity
# =============================================================================

@dataclass
class ActivityLogEntity:
    """
    Activity Log Domain Entity.
    
    Represents a single activity/log entry in the system.
    This is a pure domain entity with no framework dependencies.
    
    Attributes:
        id: Unique identifier (UUID)
        entity_type: Type of entity (Asset, Ticket, Project, User)
        entity_id: ID of the affected entity
        action_type: Type of action performed
        performed_by: User ID who performed the action
        changes: JSON field storing before/after diff
        timestamp: When the action occurred
        description: Human-readable message
    """
    id: UUID = field(default_factory=uuid4)
    entity_type: str = ""
    entity_id: Any = None
    action_type: str = ""
    performed_by: Optional[str] = None  # User ID as string
    changes: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    description: str = ""
    
    # Extended metadata
    performed_by_username: str = ""
    performed_by_role: str = ""
    
    def __post_init__(self):
        """Validate entity after initialization."""
        if self.entity_type and self.entity_type not in EntityType.choices():
            raise ValueError(f"Invalid entity_type: {self.entity_type}")
        if self.action_type and self.action_type not in ActionType.choices():
            # Allow custom action types
            pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': str(self.id),
            'entity_type': self.entity_type,
            'entity_id': str(self.entity_id) if self.entity_id else None,
            'action_type': self.action_type,
            'performed_by': self.performed_by,
            'performed_by_username': self.performed_by_username,
            'performed_by_role': self.performed_by_role,
            'changes': self.changes,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            'description': self.description,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActivityLogEntity':
        """Create entity from dictionary."""
        return cls(
            id=UUID(data['id']) if 'id' in data else uuid4(),
            entity_type=data.get('entity_type', ''),
            entity_id=data.get('entity_id'),
            action_type=data.get('action_type', ''),
            performed_by=data.get('performed_by'),
            performed_by_username=data.get('performed_by_username', ''),
            performed_by_role=data.get('performed_by_role', ''),
            changes=data.get('changes', {}),
            timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else datetime.utcnow(),
            description=data.get('description', ''),
        )
    
    def has_changes(self) -> bool:
        """Check if this log has change information."""
        return bool(self.changes)
    
    def get_change(self, field: str) -> Optional[Dict[str, Any]]:
        """Get change details for a specific field."""
        return self.changes.get(field)


# =============================================================================
# Value Objects
# =============================================================================

@dataclass
class FieldChange:
    """Represents a change to a single field."""
    field_name: str
    old_value: Any
    new_value: Any
    
    @property
    def has_changed(self) -> bool:
        return self.old_value != self.new_value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'from': self.old_value,
            'to': self.new_value,
        }


@dataclass
class Changes:
    """Collection of field changes."""
    changes: Dict[str, FieldChange] = field(default_factory=dict)
    
    def add_change(self, field: str, old_value: Any, new_value: Any) -> None:
        """Add a field change."""
        self.changes[field] = FieldChange(field_name=field, old_value=old_value, new_value=new_value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            field: change.to_dict()
            for field, change in self.changes.items()
            if change.has_changed
        }
    
    @property
    def has_changes(self) -> bool:
        return any(change.has_changed for change in self.changes.values())


# =============================================================================
# Domain Events (for Activity Logging)
# =============================================================================

@dataclass
class EntityCreated:
    """Domain event for entity creation."""
    event_type: str = "entity.created"
    entity_type: str = ""
    entity_id: Any = None
    performed_by: Any = None
    new_state: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class EntityUpdated:
    """Domain event for entity update."""
    event_type: str = "entity.updated"
    entity_type: str = ""
    entity_id: Any = None
    performed_by: Any = None
    previous_state: Dict[str, Any] = field(default_factory=dict)
    new_state: Dict[str, Any] = field(default_factory=dict)
    changes: Dict[str, tuple] = field(default_factory=dict)
    description: str = ""


@dataclass
class EntityDeleted:
    """Domain event for entity deletion."""
    event_type: str = "entity.deleted"
    entity_type: str = ""
    entity_id: Any = None
    performed_by: Any = None
    previous_state: Dict[str, Any] = field(default_factory=dict)
    description: str = ""


@dataclass
class EntityStatusChanged:
    """Domain event for status change."""
    event_type: str = "entity.status_changed"
    entity_type: str = ""
    entity_id: Any = None
    performed_by: Any = None
    from_status: str = ""
    to_status: str = ""
    description: str = ""


@dataclass
class EntityAssigned:
    """Domain event for assignment."""
    event_type: str = "entity.assigned"
    entity_type: str = ""
    entity_id: Any = None
    performed_by: Any = None
    assigned_to: Any = None
    assigned_to_username: str = ""
    previous_assignee: Any = None
    previous_assignee_username: str = ""
    description: str = ""

