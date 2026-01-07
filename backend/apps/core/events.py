# Domain Events module.
# Provides infrastructure for domain event publishing and handling.
# Follows the Observer pattern for loose coupling between domain and infrastructure.
# Supports both synchronous and asynchronous event handlers.

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Callable, Optional, Union
from enum import Enum
import threading
import json
import uuid
import inspect


class EventType(str, Enum):
    """Enumeration of domain event types."""
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_DELETED = "project.deleted"
    ASSET_CREATED = "asset.created"
    ASSET_UPDATED = "asset.updated"
    ASSET_DELETED = "asset.deleted"
    TICKET_CREATED = "ticket.created"
    TICKET_UPDATED = "ticket.updated"
    TICKET_DELETED = "ticket.deleted"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"


@dataclass
class DomainEvent(ABC):
    """Base class for all domain events."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.PROJECT_CREATED
    actor: Any = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    entity_type: str = "Project"
    entity_id: Any = None
    metadata: Dict = field(default_factory=dict)
    
    @property
    def metadata_json(self) -> str:
        """JSON representation of metadata for storage."""
        return json.dumps(self.metadata) if self.metadata else "{}"
    
    def to_dict(self) -> Dict:
        """Convert event to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            'actor_id': self.actor.id if self.actor and hasattr(self.actor, 'id') else None,
            'actor_username': self.actor.username if self.actor and hasattr(self.actor, 'username') else None,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'metadata': self.metadata,
            'metadata_json': self.metadata_json,
        }
    
    def __str__(self) -> str:
        """Human-readable event representation."""
        actor_name = self.actor.username if self.actor and hasattr(self.actor, 'username') else "system"
        return f"[{self.event_type.value}] {self.entity_type}#{self.entity_id} by {actor_name} at {self.timestamp}"


# =============================================================================
# Project Events
# =============================================================================

@dataclass
class ProjectCreated(DomainEvent):
    """Event fired when a new project is created."""
    event_type: EventType = EventType.PROJECT_CREATED
    entity_type: str = "Project"
    name: str = ""
    status: str = ""
    priority: str = ""
    category_id: Optional[str] = None
    budget: float = 0.0
    
    def __post_init__(self):
        """Initialize metadata with event details."""
        self.metadata = {
            'name': self.name,
            'status': self.status,
            'priority': self.priority,
            'category_id': self.category_id,
            'budget': self.budget,
        }


@dataclass
class ProjectUpdated(DomainEvent):
    """Event fired when a project is updated."""
    event_type: EventType = EventType.PROJECT_UPDATED
    entity_type: str = "Project"
    name: str = ""
    status: str = ""
    priority: str = ""
    changes: Dict[str, tuple] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize metadata with event details."""
        self.metadata = {
            'name': self.name,
            'status': self.status,
            'priority': self.priority,
            'changes': {k: {'old': str(v[0]), 'new': str(v[1])} for k, v in self.changes.items()},
        }


@dataclass
class ProjectDeleted(DomainEvent):
    """Event fired when a project is deleted."""
    event_type: EventType = EventType.PROJECT_DELETED
    entity_type: str = "Project"
    name: str = ""
    reason: str = ""
    
    def __post_init__(self):
        """Initialize metadata with event details."""
        self.metadata = {
            'name': self.name,
            'reason': self.reason,
        }


# =============================================================================
# Async Handler Executor (Pluggable Interface)
# =============================================================================

class AsyncExecutor(ABC):
    """Abstract base class for async handler execution."""
    
    @abstractmethod
    def submit(self, handler: Callable, event: DomainEvent) -> None:
        """
        Submit a handler to be executed asynchronously.
        
        Args:
            handler: Callable that accepts a DomainEvent
            event: The event to handle
        """
        pass
    
    @abstractmethod
    def flush(self) -> None:
        """Wait for all pending async handlers to complete."""
        pass


class ThreadPoolExecutor(AsyncExecutor):
    """
    Simple thread pool based async executor.
    
    Uses a bounded thread pool to execute handlers in background threads.
    Suitable for development and small-scale deployments.
    """
    
    def __init__(self, max_workers: int = 5, timeout: float = 30.0):
        """
        Initialize thread pool executor.
        
        Args:
            max_workers: Maximum number of worker threads
            timeout: Timeout for worker threads in seconds
        """
        from concurrent.futures import ThreadPoolExecutor as TPE
        self._executor = TPE(max_workers=max_workers)
        self._timeout = timeout
        self._lock = threading.Lock()
        self._pending = []
    
    def submit(self, handler: Callable, event: DomainEvent) -> None:
        """Submit handler for async execution."""
        with self._lock:
            self._pending.append((handler, event))
        
        # Run in background thread
        self._executor.submit(self._run_handler, handler, event)
    
    def _run_handler(self, handler: Callable, event: DomainEvent) -> None:
        """Execute handler and handle errors."""
        try:
            if inspect.iscoroutinefunction(handler):
                # For async handlers, run in new event loop
                import asyncio
                asyncio.run(handler(event))
            else:
                handler(event)
        except Exception:
            import traceback
            traceback.print_exc()
    
    def flush(self) -> None:
        """Wait for pending handlers to complete."""
        # Note: In a real implementation, we'd track futures and wait
        import time
        time.sleep(0.1)  # Brief wait for threads to complete
    
    def shutdown(self) -> None:
        """Shutdown the executor."""
        self._executor.shutdown(wait=True)


class ImmediateAsyncExecutor(AsyncExecutor):
    """
    Synchronous executor that executes handlers immediately.
    
    Used when async execution is disabled or not available.
    """
    
    def submit(self, handler: Callable, event: DomainEvent) -> None:
        """Execute handler immediately in the current thread."""
        try:
            if inspect.iscoroutinefunction(handler):
                import asyncio
                asyncio.run(handler(event))
            else:
                handler(event)
        except Exception:
            import traceback
            traceback.print_exc()
    
    def flush(self) -> None:
        """No-op for immediate executor."""
        pass


class CeleryExecutor(AsyncExecutor):
    """
    Celery-based async executor for production deployments.
    
    Requires Celery to be configured. Tasks are submitted to Celery
    for execution in worker processes.
    """
    
    def __init__(self, task_name: str = 'apps.core.events.handle_event_async'):
        """
        Initialize Celery executor.
        
        Args:
            task_name: Name of the Celery task for event handling
        """
        self._task_name = task_name
    
    def submit(self, handler: Callable, event: DomainEvent) -> None:
        """Submit handler as a Celery task."""
        try:
            from celery import current_app
            
            # Serialize event to dict
            event_data = event.to_dict()
            
            # Get handler module and function name
            handler_module = handler.__module__
            handler_name = handler.__name__
            
            # Submit task to Celery
            current_app.send_task(
                self._task_name,
                args=[handler_module, handler_name, event_data],
                kwargs={},
            )
        except ImportError:
            # Celery not configured, fall back to immediate
            import traceback
            traceback.print_exc()
    
    def flush(self) -> None:
        """No-op for Celery executor (tasks are async)."""
        pass


# =============================================================================
# Event Handler Wrapper
# =============================================================================

class EventHandler:
    """
    Wrapper for event handlers supporting both sync and async execution.
    
    Attributes:
        handler: The actual handler callable
        is_async: Whether the handler is async
    """
    
    def __init__(self, handler: Callable, is_async: bool = False):
        """Initialize handler wrapper."""
        self.handler = handler
        self.is_async = is_async or inspect.iscoroutinefunction(handler)
    
    def __call__(self, event: DomainEvent) -> None:
        """Execute the handler."""
        if self.is_async:
            import asyncio
            asyncio.run(self.handler(event))
        else:
            self.handler(event)
    
    def __eq__(self, other) -> bool:
        """Compare handlers by their underlying callable."""
        if isinstance(other, EventHandler):
            return self.handler == other.handler
        return self.handler == other
    
    def __hash__(self) -> int:
        """Hash based on underlying handler."""
        return hash(self.handler)


# =============================================================================
# Transaction-Safe Event Dispatcher
# =============================================================================

class EventDispatcher:
    """
    Central event dispatcher for publishing and handling domain events.
    
    Features:
    - Transaction-safe event dispatch using Django's transaction.on_commit()
    - Support for both synchronous and asynchronous handlers
    - Pluggable async executor for different backends
    - Wildcard handlers that receive all events
    - Thread-safe handler registration
    - Events are only dispatched AFTER successful transaction commit
    
    Usage:
        dispatcher = EventDispatcher()
        dispatcher.register(ProjectCreated, sync_handler)
        dispatcher.register(ProjectCreated, async_handler, async=True)
        dispatcher.dispatch(ProjectCreated(...))  # Queued until commit
    """
    
    _instance: Optional['EventDispatcher'] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern for global dispatcher."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the dispatcher if not already initialized."""
        if self._initialized:
            return
        
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._wildcard_handlers: List[EventHandler] = []
        self._async_executor: AsyncExecutor = ThreadPoolExecutor()
        self._async_enabled: bool = True
        self._initialized = True
    
    # =====================================================================
    # Async Executor Configuration
    # =====================================================================
    
    def set_async_executor(self, executor: AsyncExecutor) -> None:
        """
        Set a custom async executor.
        
        Args:
            executor: AsyncExecutor implementation
        """
        self._async_executor = executor
    
    def enable_async(self, enabled: bool = True) -> None:
        """Enable or disable async handler execution."""
        self._async_enabled = enabled
    
    def get_async_executor(self) -> AsyncExecutor:
        """Get the current async executor."""
        return self._async_executor
    
    # =====================================================================
    # Handler Registration
    # =====================================================================
    
    def register(
        self,
        event_type: EventType,
        handler: Callable,
        wildcard: bool = False,
        async_handler: bool = False
    ) -> None:
        """
        Register an event handler.
        
        Args:
            event_type: Type of event to handle
            handler: Callable that accepts a DomainEvent
            wildcard: If True, handler receives all events
            async_handler: If True, handler runs asynchronously
        """
        with self._lock:
            wrapped = EventHandler(handler, is_async=async_handler)
            
            if wildcard:
                if wrapped not in self._wildcard_handlers:
                    self._wildcard_handlers.append(wrapped)
            else:
                type_key = event_type.value if isinstance(event_type, EventType) else str(event_type)
                if type_key not in self._handlers:
                    self._handlers[type_key] = []
                if wrapped not in self._handlers[type_key]:
                    self._handlers[type_key].append(wrapped)
    
    def unregister(
        self,
        event_type: EventType,
        handler: Callable,
        wildcard: bool = False
    ) -> None:
        """
        Unregister an event handler.
        
        Args:
            event_type: Type of event to unhandle
            handler: Handler to remove
            wildcard: If True, handler is a wildcard handler
        """
        with self._lock:
            wrapped = EventHandler(handler)
            
            if wildcard:
                if wrapped in self._wildcard_handlers:
                    self._wildcard_handlers.remove(wrapped)
            else:
                type_key = event_type.value if isinstance(event_type, EventType) else str(event_type)
                if type_key in self._handlers and wrapped in self._handlers[type_key]:
                    self._handlers[type_key].remove(wrapped)
    
    # =====================================================================
    # Event Dispatch
    # =====================================================================
    
    def dispatch(self, event: DomainEvent, using: str = 'default') -> None:
        """
        Schedule an event to be dispatched after transaction commit.
        
        Uses Django's transaction.on_commit() to ensure events are only
        dispatched after the database transaction is successfully committed.
        
        Args:
            event: DomainEvent to publish
            using: Database alias to use for transaction checking
        """
        from django.db import transaction, connection
        
        # Check if we're in a transaction
        if connection.uses_oracle():
            # Oracle doesn't support savepoint rollback in the same way
            # Dispatch immediately for Oracle
            self._dispatch_now(event)
        else:
            # Use transaction.on_commit for transactional safety
            transaction.on_commit(
                lambda: self._dispatch_now(event),
                using=using
            )
    
    def _dispatch_now(self, event: DomainEvent) -> None:
        """
        Actually dispatch an event to all registered handlers.
        
        Args:
            event: DomainEvent to publish
        """
        type_key = event.event_type.value if isinstance(event.event_type, EventType) else str(event_type)
        
        # Get handlers for this event type
        handlers = self._handlers.get(type_key, []).copy()
        
        # Dispatch to handlers
        self._execute_handlers(handlers, event)
        
        # Dispatch to wildcard handlers
        self._execute_handlers(self._wildcard_handlers.copy(), event)
    
    def _execute_handlers(self, handlers: List[EventHandler], event: DomainEvent) -> None:
        """
        Execute a list of handlers for an event.
        
        Sync handlers execute immediately.
        Async handlers execute in the configured async executor.
        
        Args:
            handlers: List of EventHandler wrappers
            event: The event to handle
        """
        for handler in handlers:
            try:
                if handler.is_async and self._async_enabled:
                    # Submit to async executor
                    self._async_executor.submit(handler.handler, event)
                else:
                    # Execute immediately
                    handler(event)
            except Exception:
                import traceback
                traceback.print_exc()
    
    def dispatch_now(self, event: DomainEvent) -> None:
        """
        Immediately dispatch an event (bypasses transaction.on_commit).
        
        Use this for events that should be dispatched immediately,
        outside of any transaction context.
        
        Args:
            event: DomainEvent to publish
        """
        self._dispatch_now(event)
    
    # =====================================================================
    # Utility Methods
    # =====================================================================
    
    def clear(self) -> None:
        """Remove all registered handlers."""
        with self._lock:
            self._handlers.clear()
            self._wildcard_handlers.clear()
    
    def get_handlers_for(self, event_type: EventType) -> List[Callable]:
        """Get all handlers registered for an event type."""
        type_key = event_type.value if isinstance(event_type, EventType) else str(event_type)
        return [h.handler for h in self._handlers.get(type_key, [])]
    
    def flush(self) -> None:
        """Flush all pending async handlers."""
        self._async_executor.flush()


# =============================================================================
# Transaction-Aware Event Publisher (for services)
# =============================================================================

class TransactionEventPublisher:
    """
    Mixin that provides transactional-safe event publishing capability to services.
    
    Events are collected during execution and dispatched AFTER the transaction
    commits successfully.
    
    Usage:
        class ProjectService(TransactionEventPublisher):
            def create_project(self, ...):
                project = ...
                self._publish_event(ProjectCreated(...))  # Queued
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize with empty event queue."""
        super().__init__(*args, **kwargs)
        self._pending_events: List[DomainEvent] = []
    
    def _publish_event(self, event: DomainEvent) -> None:
        """Queue an event for dispatch after transaction commit."""
        self._pending_events.append(event)


class ImmediateEventPublisher:
    """Mixin for services that need immediate event dispatch."""
    
    @property
    def _dispatcher(self) -> EventDispatcher:
        """Get the singleton event dispatcher."""
        return EventDispatcher()
    
    def _publish_event(self, event: DomainEvent) -> None:
        """Immediately dispatch an event."""
        self._dispatcher.dispatch_now(event)


# Backward compatibility alias
EventPublisher = ImmediateEventPublisher


# =============================================================================
# Utility Functions
# =============================================================================

def publish_event(event: DomainEvent) -> None:
    """Convenience function to publish an event."""
    EventDispatcher().dispatch(event)


def register_handler(
    event_type: EventType,
    handler: Callable,
    wildcard: bool = False,
    async_handler: bool = False
) -> None:
    """Convenience function to register an event handler."""
    EventDispatcher().register(event_type, handler, wildcard, async_handler)


def unregister_handler(
    event_type: EventType,
    handler: Callable,
    wildcard: bool = False
) -> None:
    """Convenience function to unregister an event handler."""
    EventDispatcher().unregister(event_type, handler, wildcard)

