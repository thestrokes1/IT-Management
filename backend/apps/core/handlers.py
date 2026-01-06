# Event Handlers module.
# Contains handlers for domain events (e.g., AuditLogHandler).
# Handlers are registered with the EventDispatcher to respond to events.
# No logging or persistence logic in services - all delegated to handlers.

from typing import Any, Optional
from django.utils import timezone
from django.db import transaction

from apps.core.events import (
    DomainEvent,
    EventDispatcher,
    EventPublisher,
    EventType,
    ProjectCreated,
    ProjectUpdated,
    ProjectDeleted,
)
from apps.logs.models import AuditLog


class AuditLogHandler:
    """
    Handler that persists domain events as audit log entries.
    
    This handler is responsible for:
    - Receiving domain events
    - Persisting them as AuditLog records
    - Creating related Log entries for activity tracking
    
    Services do NOT contain any logging or persistence logic -
    they simply publish events. This handler subscribes to events
    and handles persistence.
    
    Usage:
        # Register the handler at app startup
        from apps.core.events import register_handler
        from apps.core.handlers import AuditLogHandler
        
        handler = AuditLogHandler()
        register_handler(EventType.PROJECT_CREATED, handler.handle_project_created)
        register_handler(EventType.PROJECT_UPDATED, handler.handle_project_updated)
        register_handler(EventType.PROJECT_DELETED, handler.handle_project_deleted)
    """
    
    # Mapping of event types to handler methods
    EVENT_HANDLERS = {
        EventType.PROJECT_CREATED: 'handle_project_created',
        EventType.PROJECT_UPDATED: 'handle_project_updated',
        EventType.PROJECT_DELETED: 'handle_project_deleted',
        EventType.ASSET_CREATED: 'handle_asset_created',
        EventType.ASSET_UPDATED: 'handle_asset_updated',
        EventType.ASSET_DELETED: 'handle_asset_deleted',
        EventType.TICKET_CREATED: 'handle_ticket_created',
        EventType.TICKET_UPDATED: 'handle_ticket_updated',
        EventType.TICKET_DELETED: 'handle_ticket_deleted',
        EventType.USER_CREATED: 'handle_user_created',
        EventType.USER_UPDATED: 'handle_user_updated',
        EventType.USER_DELETED: 'handle_user_deleted',
    }
    
    def handle(self, event: DomainEvent) -> None:
        """
        Route event to appropriate handler method.
        
        Args:
            event: DomainEvent to handle
        """
        handler_name = self.EVENT_HANDLERS.get(event.event_type)
        
        if handler_name and hasattr(self, handler_name):
            handler = getattr(self, handler_name)
            try:
                handler(event)
            except Exception:
                # Log but don't break event dispatching
                import traceback
                traceback.print_exc()
    
    def _create_audit_log(
        self,
        event: DomainEvent,
        action: str,
        description: str
    ) -> Optional[AuditLog]:
        """
        Create an AuditLog entry from a domain event.
        
        Args:
            event: The domain event
            action: Action type (e.g., "CREATE", "UPDATE", "DELETE")
            description: Human-readable description
            
        Returns:
            Created AuditLog instance or None on error
        """
        try:
            actor = event.actor
            actor_id = actor.id if actor and hasattr(actor, 'id') else None
            actor_username = actor.username if actor and hasattr(actor, 'username') else 'system'
            
            # Map event type to log type
            entity_type = event.entity_type.upper()
            
            return AuditLog.objects.create(
                action=action,
                entity_type=entity_type,
                entity_id=event.entity_id,
                user_id=actor_id,
                username=actor_username,
                details=event.metadata_json,
                timestamp=event.timestamp,
            )
        except Exception:
            import traceback
            traceback.print_exc()
            return None
    
    # -------------------------------------------------------------------------
    # Project Event Handlers
    # -------------------------------------------------------------------------
    
    def handle_project_created(self, event: ProjectCreated) -> None:
        """Handle ProjectCreated events."""
        description = f'Created project "{event.name}"'
        self._create_audit_log(event, 'CREATE', description)
    
    def handle_project_updated(self, event: ProjectUpdated) -> None:
        """Handle ProjectUpdated events."""
        changes_count = len(event.changes) if event.changes else 0
        description = f'Updated project "{event.name}" ({changes_count} changes)'
        self._create_audit_log(event, 'UPDATE', description)
    
    def handle_project_deleted(self, event: ProjectDeleted) -> None:
        """Handle ProjectDeleted events."""
        description = f'Deleted project "{event.name}"'
        if event.reason:
            description += f' - Reason: {event.reason}'
        self._create_audit_log(event, 'DELETE', description)
    
    # -------------------------------------------------------------------------
    # Asset Event Handlers
    # -------------------------------------------------------------------------
    
    def handle_asset_created(self, event: DomainEvent) -> None:
        """Handle AssetCreated events."""
        name = event.metadata.get('name', 'Unknown')
        description = f'Created asset "{name}"'
        self._create_audit_log(event, 'CREATE', description)
    
    def handle_asset_updated(self, event: DomainEvent) -> None:
        """Handle AssetUpdated events."""
        name = event.metadata.get('name', 'Unknown')
        description = f'Updated asset "{name}"'
        self._create_audit_log(event, 'UPDATE', description)
    
    def handle_asset_deleted(self, event: DomainEvent) -> None:
        """Handle AssetDeleted events."""
        name = event.metadata.get('name', 'Unknown')
        description = f'Deleted asset "{name}"'
        self._create_audit_log(event, 'DELETE', description)
    
    # -------------------------------------------------------------------------
    # Ticket Event Handlers
    # -------------------------------------------------------------------------
    
    def handle_ticket_created(self, event: DomainEvent) -> None:
        """Handle TicketCreated events."""
        title = event.metadata.get('title', 'Unknown')
        description = f'Created ticket "{title}"'
        self._create_audit_log(event, 'CREATE', description)
    
    def handle_ticket_updated(self, event: DomainEvent) -> None:
        """Handle TicketUpdated events."""
        title = event.metadata.get('title', 'Unknown')
        description = f'Updated ticket "{title}"'
        self._create_audit_log(event, 'UPDATE', description)
    
    def handle_ticket_deleted(self, event: DomainEvent) -> None:
        """Handle TicketDeleted events."""
        title = event.metadata.get('title', 'Unknown')
        description = f'Deleted ticket "{title}"'
        self._create_audit_log(event, 'DELETE', description)
    
    # -------------------------------------------------------------------------
    # User Event Handlers
    # -------------------------------------------------------------------------
    
    def handle_user_created(self, event: DomainEvent) -> None:
        """Handle UserCreated events."""
        username = event.metadata.get('username', 'Unknown')
        description = f'Created user "{username}"'
        self._create_audit_log(event, 'CREATE', description)
    
    def handle_user_updated(self, event: DomainEvent) -> None:
        """Handle UserUpdated events."""
        username = event.metadata.get('username', 'Unknown')
        description = f'Updated user "{username}"'
        self._create_audit_log(event, 'UPDATE', description)
    
    def handle_user_deleted(self, event: DomainEvent) -> None:
        """Handle UserDeleted events."""
        username = event.metadata.get('username', 'Unknown')
        description = f'Deleted user "{username}"'
        self._create_audit_log(event, 'DELETE', description)


# =============================================================================
# Event Handler Registration
# =============================================================================

def register_audit_handlers() -> None:
    """
    Register all audit log handlers with the EventDispatcher.
    
    Call this function at app startup (e.g., in AppConfig.ready()).
    
    Usage:
        # In apps.py
        def ready(self):
            from apps.core.handlers import register_audit_handlers
            register_audit_handlers()
    """
    handler = AuditLogHandler()
    dispatcher = EventDispatcher()
    
    for event_type, handler_name in AuditLogHandler.EVENT_HANDLERS.items():
        dispatcher.register(event_type, handler.handle)


# =============================================================================
# Integration with Django Apps
# =============================================================================

def setup_event_handlers() -> None:
    """
    Setup function to be called from Django's AppConfig.ready().
    
    Example usage in apps.py:
    
        from apps.core.handlers import setup_event_handlers
        
        class ProjectsConfig(AppConfig):
            name = 'apps.projects'
            
            def ready(self):
                setup_event_handlers()
    """
    from django.apps import apps
    
    # Import handlers to ensure they're loaded
    from apps.core.handlers import AuditLogHandler
    
    # Register wildcard handler for all events
    dispatcher = EventDispatcher()
    dispatcher.register(EventType.PROJECT_CREATED, lambda e: None, wildcard=False)  # Placeholder
    
    # Actually register the audit handler
    register_audit_handlers()

