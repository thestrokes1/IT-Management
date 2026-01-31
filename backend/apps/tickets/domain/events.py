"""
Ticket Domain Events.

Defines domain events for ticket lifecycle actions.
Events are emitted after successful transaction commit.
Event handlers write ActivityLog and StatusHistory.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from apps.core.events import DomainEvent, EventDispatcher


# =============================================================================
# Ticket Event Types (standalone - cannot extend Enum)
# =============================================================================

class TicketEventType:
    """Ticket event type constants as strings."""
    TICKET_ASSIGNED = "ticket.assigned"
    TICKET_UNASSIGNED = "ticket.unassigned"
    TICKET_UPDATED = "ticket.updated"
    TICKET_RESOLVED = "ticket.resolved"
    TICKET_REOPENED = "ticket.reopened"
    TICKET_STATUS_CHANGED = "ticket.status_changed"
    
    @classmethod
    def values(cls):
        return [
            cls.TICKET_ASSIGNED,
            cls.TICKET_UNASSIGNED,
            cls.TICKET_UPDATED,
            cls.TICKET_RESOLVED,
            cls.TICKET_REOPENED,
            cls.TICKET_STATUS_CHANGED,
        ]


# =============================================================================
# Ticket Domain Events
# =============================================================================

@dataclass
class TicketEvent(DomainEvent):
    """Base class for all ticket domain events."""
    ticket_id: int = 0
    ticket_title: str = ""
    entity_type: str = "Ticket"
    
    def __post_init__(self):
        self.entity_id = self.ticket_id


@dataclass
class TicketAssigned(TicketEvent):
    """Event fired when a ticket is assigned."""
    event_type: str = TicketEventType.TICKET_ASSIGNED
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
class TicketUpdated(TicketEvent):
    """Event fired when a ticket is updated."""
    event_type: str = TicketEventType.TICKET_UPDATED
    changes: Dict[str, tuple] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata = {
            'changes': {k: {'old': str(v[0]), 'new': str(v[1])} for k, v in self.changes.items()}
        }


@dataclass
class TicketResolved(TicketEvent):
    """Event fired when a ticket is resolved."""
    event_type: str = TicketEventType.TICKET_RESOLVED
    resolution_summary: str = ""
    resolution_time_hours: Optional[float] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata = {
            'resolution_summary': self.resolution_summary,
            'resolution_time_hours': self.resolution_time_hours,
        }


@dataclass
class TicketReopened(TicketEvent):
    """Event fired when a ticket is reopened."""
    event_type: str = TicketEventType.TICKET_REOPENED
    reason: str = ""
    previous_status: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata = {
            'reason': self.reason,
            'previous_status': self.previous_status,
        }


@dataclass
class TicketStatusChanged(TicketEvent):
    """Event fired when a ticket status changes."""
    event_type: str = TicketEventType.TICKET_STATUS_CHANGED
    from_status: str = ""
    to_status: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata = {
            'from_status': self.from_status,
            'to_status': self.to_status,
        }


@dataclass
class TicketUnassigned(TicketEvent):
    """Event fired when a ticket is unassigned."""
    event_type: str = TicketEventType.TICKET_UNASSIGNED
    unassigned_user_id: Optional[int] = None
    unassigned_username: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata = {
            'unassigned_user_id': self.unassigned_user_id,
            'unassigned_username': self.unassigned_username,
        }


# =============================================================================
# Event Handlers
# =============================================================================

class TicketEventHandlers:
    """
    Event handlers for ticket domain events.
    
    These handlers write ActivityLog and StatusHistory records.
    No side effects inside entities - all side effects here.
    """
    
    @staticmethod
    def handle_ticket_assigned(event: TicketAssigned) -> None:
        """Handle ticket assignment event."""
        from apps.core.services.activity_logger import log_activity, ActivityAction
        from apps.tickets.models import TicketStatusHistory
        
        # Write ActivityLog
        log_activity(
            actor=event.actor,
            action=ActivityAction.TICKET_ASSIGNED,
            target_type='ticket',
            target_id=event.ticket_id,
            metadata={
                'title': event.ticket_title,
                'assignee_id': event.assignee_id,
                'assignee_username': event.assignee_username,
            }
        )
    
    @staticmethod
    def handle_ticket_updated(event: TicketUpdated) -> None:
        """Handle ticket update event."""
        from apps.core.services.activity_logger import log_activity, ActivityAction
        
        log_activity(
            actor=event.actor,
            action=ActivityAction.TICKET_UPDATED,
            target_type='ticket',
            target_id=event.ticket_id,
            metadata={
                'title': event.ticket_title,
                'changes': event.metadata.get('changes', {}),
            }
        )
    
    @staticmethod
    def handle_ticket_resolved(event: TicketResolved) -> None:
        """Handle ticket resolution event."""
        from apps.core.services.activity_logger import log_activity, ActivityAction
        
        log_activity(
            actor=event.actor,
            action=ActivityAction.TICKET_RESOLVED,
            target_type='ticket',
            target_id=event.ticket_id,
            metadata={
                'title': event.ticket_title,
                'resolution_summary': event.resolution_summary,
                'resolution_time_hours': event.resolution_time_hours,
            }
        )
    
    @staticmethod
    def handle_ticket_reopened(event: TicketReopened) -> None:
        """Handle ticket reopen event."""
        from apps.core.services.activity_logger import log_activity, ActivityAction
        from apps.tickets.models import TicketStatusHistory
        
        log_activity(
            actor=event.actor,
            action=ActivityAction.TICKET_REOPENED,
            target_type='ticket',
            target_id=event.ticket_id,
            metadata={
                'title': event.ticket_title,
                'reason': event.reason,
                'previous_status': event.previous_status,
            }
        )
    
    @staticmethod
    def handle_ticket_status_changed(event: TicketStatusChanged) -> None:
        """Handle ticket status change event."""
        from apps.tickets.models import TicketStatusHistory
        
        # Write StatusHistory (immutable record)
        TicketStatusHistory.objects.create(
            ticket_id=event.ticket_id,
            from_status=event.from_status,
            to_status=event.to_status,
            changed_by=event.actor,
        )
    
    @staticmethod
    def handle_ticket_unassigned(event: TicketUnassigned) -> None:
        """Handle ticket unassigned event."""
        from apps.core.services.activity_logger import log_activity, ActivityAction
        
        log_activity(
            actor=event.actor,
            action=ActivityAction.TICKET_UNASSIGNED,
            target_type='ticket',
            target_id=event.ticket_id,
            metadata={
                'title': event.ticket_title,
                'unassigned_user_id': event.unassigned_user_id,
                'unassigned_username': event.unassigned_username,
            }
        )


# =============================================================================
# Event Dispatcher Setup
# =============================================================================

def setup_ticket_event_handlers() -> None:
    """
    Register ticket event handlers with the global event dispatcher.
    
    Call this during application startup to register handlers.
    """
    dispatcher = EventDispatcher()
    
    # Register ticket event handlers
    dispatcher.register(TicketEventType.TICKET_ASSIGNED, TicketEventHandlers.handle_ticket_assigned)
    dispatcher.register(TicketEventType.TICKET_UNASSIGNED, TicketEventHandlers.handle_ticket_unassigned)
    dispatcher.register(TicketEventType.TICKET_UPDATED, TicketEventHandlers.handle_ticket_updated)
    dispatcher.register(TicketEventType.TICKET_RESOLVED, TicketEventHandlers.handle_ticket_resolved)
    dispatcher.register(TicketEventType.TICKET_REOPENED, TicketEventHandlers.handle_ticket_reopened)
    dispatcher.register(TicketEventType.TICKET_STATUS_CHANGED, TicketEventHandlers.handle_ticket_status_changed)


# =============================================================================
# Convenience Functions for Emitting Events
# =============================================================================

def emit_ticket_assigned(
    ticket_id: int,
    ticket_title: str,
    actor: Any,
    assignee_id: Optional[int],
    assignee_username: str,
    assigner_id: Optional[int] = None,
    assigner_username: str = ""
) -> None:
    """Emit a ticket assigned event."""
    event = TicketAssigned(
        ticket_id=ticket_id,
        ticket_title=ticket_title,
        actor=actor,
        assignee_id=assignee_id,
        assignee_username=assignee_username,
        assigner_id=assigner_id or (actor.id if actor else None),
        assigner_username=assigner_username or (actor.username if actor else ""),
    )
    EventDispatcher().dispatch(event)


def emit_ticket_updated(
    ticket_id: int,
    ticket_title: str,
    actor: Any,
    changes: Dict[str, tuple]
) -> None:
    """Emit a ticket updated event."""
    event = TicketUpdated(
        ticket_id=ticket_id,
        ticket_title=ticket_title,
        actor=actor,
        changes=changes,
    )
    EventDispatcher().dispatch(event)


def emit_ticket_resolved(
    ticket_id: int,
    ticket_title: str,
    actor: Any,
    resolution_summary: str = "",
    resolution_time_hours: Optional[float] = None
) -> None:
    """Emit a ticket resolved event."""
    event = TicketResolved(
        ticket_id=ticket_id,
        ticket_title=ticket_title,
        actor=actor,
        resolution_summary=resolution_summary,
        resolution_time_hours=resolution_time_hours,
    )
    EventDispatcher().dispatch(event)


def emit_ticket_reopened(
    ticket_id: int,
    ticket_title: str,
    actor: Any,
    reason: str,
    previous_status: str
) -> None:
    """Emit a ticket reopened event."""
    event = TicketReopened(
        ticket_id=ticket_id,
        ticket_title=ticket_title,
        actor=actor,
        reason=reason,
        previous_status=previous_status,
    )
    EventDispatcher().dispatch(event)


def emit_ticket_status_changed(
    ticket_id: int,
    ticket_title: str,
    actor: Any,
    from_status: str,
    to_status: str
) -> None:
    """Emit a ticket status changed event."""
    event = TicketStatusChanged(
        ticket_id=ticket_id,
        ticket_title=ticket_title,
        actor=actor,
        from_status=from_status,
        to_status=to_status,
    )
    EventDispatcher().dispatch(event)


def emit_ticket_unassigned(
    ticket_id: int,
    ticket_title: str,
    actor: Any,
    unassigned_user_id: Optional[int],
    unassigned_username: str
) -> None:
    """Emit a ticket unassigned event."""
    event = TicketUnassigned(
        ticket_id=ticket_id,
        ticket_title=ticket_title,
        actor=actor,
        unassigned_user_id=unassigned_user_id,
        unassigned_username=unassigned_username,
    )
    EventDispatcher().dispatch(event)
