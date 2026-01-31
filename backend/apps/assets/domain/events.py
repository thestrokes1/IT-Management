"""
Asset Domain Events.

Defines domain events for asset lifecycle actions.
Events are emitted after successful transaction commit.
Event handlers write ActivityLog and AssetAuditLog.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from apps.core.events import DomainEvent, EventDispatcher


# =============================================================================
# Asset Event Types (standalone - cannot extend Enum)
# =============================================================================

class AssetEventType:
    """Asset event type constants as strings."""
    ASSET_ASSIGNED = "asset.assigned"
    ASSET_UNASSIGNED = "asset.unassigned"
    ASSET_UPDATED = "asset.updated"
    ASSET_STATUS_CHANGED = "asset.status_changed"
    
    # For backward compatibility - return value for comparisons
    @classmethod
    def values(cls):
        return [
            cls.ASSET_ASSIGNED,
            cls.ASSET_UNASSIGNED,
            cls.ASSET_UPDATED,
            cls.ASSET_STATUS_CHANGED,
        ]


# =============================================================================
# Asset Domain Events
# =============================================================================

@dataclass
class AssetEvent(DomainEvent):
    """Base class for all asset domain events."""
    asset_id: int = 0
    asset_name: str = ""
    entity_type: str = "Asset"
    
    def __post_init__(self):
        self.entity_id = self.asset_id


@dataclass
class AssetAssigned(AssetEvent):
    """Event fired when an asset is assigned."""
    event_type: str = AssetEventType.ASSET_ASSIGNED
    assignee_id: Optional[int] = None
    assignee_username: str = ""
    assigner_id: Optional[int] = None
    assigner_username: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata = {
            'assignee_id': self.assignee_id,
            'assignee_username': self.assignee_username,
            'assigner_id': self.assigner_id,
            'assigner_username': self.assigner_username,
        }


@dataclass
class AssetUnassigned(AssetEvent):
    """Event fired when an asset is unassigned."""
    event_type: str = AssetEventType.ASSET_UNASSIGNED
    previous_assignee_id: Optional[int] = None
    previous_assignee_username: str = ""
    unassigner_id: Optional[int] = None
    unassigner_username: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata = {
            'previous_assignee_id': self.previous_assignee_id,
            'previous_assignee_username': self.previous_assignee_username,
            'unassigner_id': self.unassigner_id,
            'unassigner_username': self.unassigner_username,
        }


@dataclass
class AssetUpdated(AssetEvent):
    """Event fired when an asset is updated."""
    event_type: str = AssetEventType.ASSET_UPDATED
    changes: Dict[str, tuple] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata = {
            'changes': {k: {'old': str(v[0]), 'new': str(v[1])} for k, v in self.changes.items()}
        }


@dataclass
class AssetStatusChanged(AssetEvent):
    """Event fired when an asset status changes."""
    event_type: str = AssetEventType.ASSET_STATUS_CHANGED
    from_status: str = ""
    to_status: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata = {
            'from_status': self.from_status,
            'to_status': self.to_status,
        }


# =============================================================================
# Event Handlers
# =============================================================================

class AssetEventHandlers:
    """
    Event handlers for asset domain events.
    
    These handlers write ActivityLog and AssetAuditLog records.
    No side effects inside entities - all side effects here.
    """
    
    @staticmethod
    def handle_asset_assigned(event: AssetAssigned) -> None:
        """Handle asset assignment event."""
        from apps.core.services.activity_logger import log_activity, ActivityAction
        from apps.assets.models import AssetAuditLog
        
        # Write ActivityLog
        log_activity(
            actor=event.actor,
            action=ActivityAction.ASSET_ASSIGNED,
            target_type='asset',
            target_id=event.asset_id,
            metadata={
                'name': event.asset_name,
                'assignee_id': event.assignee_id,
                'assignee_username': event.assignee_username,
            }
        )
        
        # Write AssetAuditLog
        AssetAuditLog.objects.create(
            asset_id=event.asset_id,
            user=event.actor,
            action='ASSIGNED',
            description=f'Asset assigned to {event.assignee_username}',
            new_values={'assigned_to': event.assignee_username}
        )
    
    @staticmethod
    def handle_asset_unassigned(event: AssetUnassigned) -> None:
        """Handle asset unassignment event."""
        from apps.core.services.activity_logger import log_activity, ActivityAction
        from apps.assets.models import AssetAuditLog
        
        # Write ActivityLog
        log_activity(
            actor=event.actor,
            action=ActivityAction.ASSET_RETURNED,
            target_type='asset',
            target_id=event.asset_id,
            metadata={
                'name': event.asset_name,
                'previous_assignee_id': event.previous_assignee_id,
                'previous_assignee_username': event.previous_assignee_username,
            }
        )
        
        # Write AssetAuditLog
        AssetAuditLog.objects.create(
            asset_id=event.asset_id,
            user=event.actor,
            action='UNASSIGNED',
            description=f'Asset unassigned from {event.previous_assignee_username}',
            old_values={'assigned_to': event.previous_assignee_username}
        )
    
    @staticmethod
    def handle_asset_updated(event: AssetUpdated) -> None:
        """Handle asset update event."""
        from apps.core.services.activity_logger import log_activity, ActivityAction
        from apps.assets.models import AssetAuditLog
        
        log_activity(
            actor=event.actor,
            action=ActivityAction.ASSET_UPDATED,
            target_type='asset',
            target_id=event.asset_id,
            metadata={
                'name': event.asset_name,
                'changes': event.metadata.get('changes', {}),
            }
        )
        
        # Write AssetAuditLog
        changes = event.metadata.get('changes', {})
        old_values = {k: v['old'] for k, v in changes.items()}
        new_values = {k: v['new'] for k, v in changes.items()}
        AssetAuditLog.objects.create(
            asset_id=event.asset_id,
            user=event.actor,
            action='UPDATED',
            description=f'Asset updated',
            old_values=old_values,
            new_values=new_values
        )
    
    @staticmethod
    def handle_asset_status_changed(event: AssetStatusChanged) -> None:
        """Handle asset status change event."""
        from apps.core.services.activity_logger import log_activity, ActivityAction
        from apps.assets.models import AssetAuditLog
        
        log_activity(
            actor=event.actor,
            action=ActivityAction.ASSET_STATUS_CHANGED,
            target_type='asset',
            target_id=event.asset_id,
            metadata={
                'name': event.asset_name,
                'from_status': event.from_status,
                'to_status': event.to_status,
            }
        )
        
        # Write AssetAuditLog
        AssetAuditLog.objects.create(
            asset_id=event.asset_id,
            user=event.actor,
            action='STATUS_CHANGED',
            description=f'Asset status changed from {event.from_status} to {event.to_status}',
            old_values={'status': event.from_status},
            new_values={'status': event.to_status}
        )


# =============================================================================
# Event Dispatcher Setup
# =============================================================================

def setup_asset_event_handlers() -> None:
    """
    Register asset event handlers with the global event dispatcher.
    
    Call this during application startup to register handlers.
    """
    dispatcher = EventDispatcher()
    
    # Register asset event handlers
    dispatcher.register(AssetEventType.ASSET_ASSIGNED, AssetEventHandlers.handle_asset_assigned)
    dispatcher.register(AssetEventType.ASSET_UNASSIGNED, AssetEventHandlers.handle_asset_unassigned)
    dispatcher.register(AssetEventType.ASSET_UPDATED, AssetEventHandlers.handle_asset_updated)
    dispatcher.register(AssetEventType.ASSET_STATUS_CHANGED, AssetEventHandlers.handle_asset_status_changed)


# =============================================================================
# Convenience Functions for Emitting Events
# =============================================================================

def emit_asset_assigned(
    asset_id: int,
    asset_name: str,
    actor: Any,
    assignee_id: Optional[int],
    assignee_username: str,
    assigner_id: Optional[int] = None,
    assigner_username: str = ""
) -> None:
    """Emit an asset assigned event."""
    event = AssetAssigned(
        asset_id=asset_id,
        asset_name=asset_name,
        actor=actor,
        assignee_id=assignee_id,
        assignee_username=assignee_username,
        assigner_id=assigner_id or (actor.id if actor else None),
        assigner_username=assigner_username or (actor.username if actor else ""),
    )
    EventDispatcher().dispatch(event)


def emit_asset_unassigned(
    asset_id: int,
    asset_name: str,
    actor: Any,
    previous_assignee_id: Optional[int],
    previous_assignee_username: str,
    unassigner_id: Optional[int] = None,
    unassigner_username: str = ""
) -> None:
    """Emit an asset unassigned event."""
    event = AssetUnassigned(
        asset_id=asset_id,
        asset_name=asset_name,
        actor=actor,
        previous_assignee_id=previous_assignee_id,
        previous_assignee_username=previous_assignee_username,
        unassigner_id=unassigner_id or (actor.id if actor else None),
        unassigner_username=unassigner_username or (actor.username if actor else ""),
    )
    EventDispatcher().dispatch(event)


def emit_asset_updated(
    asset_id: int,
    asset_name: str,
    actor: Any,
    changes: Dict[str, tuple]
) -> None:
    """Emit an asset updated event."""
    event = AssetUpdated(
        asset_id=asset_id,
        asset_name=asset_name,
        actor=actor,
        changes=changes,
    )
    EventDispatcher().dispatch(event)


def emit_asset_status_changed(
    asset_id: int,
    asset_name: str,
    actor: Any,
    from_status: str,
    to_status: str
) -> None:
    """Emit an asset status changed event."""
    event = AssetStatusChanged(
        asset_id=asset_id,
        asset_name=asset_name,
        actor=actor,
        from_status=from_status,
        to_status=to_status,
    )
    EventDispatcher().dispatch(event)
