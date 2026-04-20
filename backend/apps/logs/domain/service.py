"""
Activity Log Domain Service.

Framework-agnostic domain service for activity logging.
Follows Clean Architecture - no Django ORM dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from apps.logs.domain.entity import (
    ActivityLogEntity,
    ActionType,
    EntityType,
    EntityCreated,
    EntityUpdated,
    EntityDeleted,
    EntityStatusChanged,
    EntityAssigned,
)


# =============================================================================
# Domain Service Interface
# =============================================================================

class IActivityLogRepository:
    """Interface for activity log repository."""
    
    def save(self, activity_log: ActivityLogEntity) -> ActivityLogEntity:
        """Save an activity log entry."""
        raise NotImplementedError
    
    def get_by_id(self, log_id: UUID) -> Optional[ActivityLogEntity]:
        """Get activity log by ID."""
        raise NotImplementedError
    
    def get_by_entity(
        self,
        entity_type: str,
        entity_id: Any,
        limit: int = 100,
    ) -> List[ActivityLogEntity]:
        """Get logs for a specific entity."""
        raise NotImplementedError
    
    def get_by_user(
        self,
        user_id: str,
        limit: int = 100,
    ) -> List[ActivityLogEntity]:
        """Get logs performed by a specific user."""
        raise NotImplementedError
    
    def get_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        entity_type: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ActivityLogEntity]:
        """Get logs within a date range with filters."""
        raise NotImplementedError


# =============================================================================
# Activity Log Service (Domain Service)
# =============================================================================

class ActivityLogService:
    """
    Domain service for recording activity logs.
    
    This service is framework-agnostic and can be used with any ORM or storage.
    It handles:
    - Creating activity log entries from domain events
    - Computing field diffs for updates
    - Building human-readable descriptions
    
    Usage:
        service = ActivityLogService(repository=my_repository)
        
        # Record an entity creation
        service.record_activity(
            entity_type=EntityType.TICKET,
            entity_id=ticket.id,
            action_type=ActionType.CREATED,
            performed_by=user.id,
            performed_by_username=user.username,
            description=f"Created ticket: {ticket.title}"
        )
        
        # Record an entity update with diff
        service.record_activity(
            entity_type=EntityType.TICKET,
            entity_id=ticket.id,
            action_type=ActionType.UPDATED,
            performed_by=user.id,
            performed_by_username=user.username,
            changes={
                'status': {'from': 'Open', 'to': 'Closed'},
                'priority': {'from': 'Low', 'to': 'High'},
            },
            description="Updated ticket: status, priority"
        )
    """
    
    def __init__(self, repository: Optional[IActivityLogRepository] = None):
        """
        Initialize the service with an optional repository.
        
        Args:
            repository: Implementation of IActivityLogRepository
        """
        self._repository = repository
    
    @property
    def repository(self) -> IActivityLogRepository:
        """Get the repository, raising error if not set."""
        if self._repository is None:
            raise RuntimeError(
                "Repository not set. Provide a repository implementation."
            )
        return self._repository
    
    def set_repository(self, repository: IActivityLogRepository) -> None:
        """Set the repository implementation."""
        self._repository = repository
    
    # =========================================================================
    # Recording Methods
    # =========================================================================
    
    def record_activity(
        self,
        entity_type: str,
        entity_id: Any,
        action_type: str,
        performed_by: Optional[str] = None,
        performed_by_username: str = "",
        performed_by_role: str = "",
        changes: Optional[Dict[str, Any]] = None,
        description: str = "",
        timestamp: Optional[datetime] = None,
    ) -> ActivityLogEntity:
        """
        Record an activity log entry.
        
        Args:
            entity_type: Type of entity (Asset, Ticket, Project, User)
            entity_id: ID of the affected entity
            action_type: Type of action (CREATED, UPDATED, etc.)
            performed_by: User ID who performed the action
            performed_by_username: Username for display
            performed_by_role: User role for display
            changes: Dictionary of field changes {field: {'from': old, 'to': new}}
            description: Human-readable description
            timestamp: When the action occurred (default: now)
        
        Returns:
            The created ActivityLogEntity
        """
        # Validate entity type
        if entity_type not in EntityType.choices():
            raise ValueError(f"Invalid entity_type: {entity_type}")
        
        # Generate description if not provided
        if not description:
            description = self._build_description(
                entity_type=entity_type,
                action_type=action_type,
                changes=changes or {},
            )
        
        # Create the domain entity
        activity_log = ActivityLogEntity(
            entity_type=entity_type,
            entity_id=entity_id,
            action_type=action_type,
            performed_by=performed_by,
            performed_by_username=performed_by_username,
            performed_by_role=performed_by_role,
            changes=changes or {},
            description=description,
            timestamp=timestamp or datetime.utcnow(),
        )
        
        # Save via repository if available
        if self._repository:
            return self._repository.save(activity_log)
        
        return activity_log
    
    def record_from_event(self, event: Any) -> ActivityLogEntity:
        """
        Record an activity log from a domain event.
        
        Args:
            event: Domain event (EntityCreated, EntityUpdated, etc.)
        
        Returns:
            The created ActivityLogEntity
        """
        # Get actor information
        performed_by = None
        performed_by_username = "System"
        performed_by_role = ""
        
        if event.performed_by:
            if hasattr(event.performed_by, 'id'):
                performed_by = str(event.performed_by.id)
            else:
                performed_by = str(event.performed_by)
        
        if hasattr(event.performed_by, 'username'):
            performed_by_username = event.performed_by.username
        elif hasattr(event, 'actor_username'):
            performed_by_username = event.actor_username
        
        if hasattr(event.performed_by, 'role'):
            performed_by_role = event.performed_by.role
        
        # Map event type to action type
        action_type = self._map_event_to_action(event)
        
        # Build changes dictionary
        changes = {}
        if isinstance(event, EntityUpdated):
            changes = self._build_changes_from_event(event)
        elif isinstance(event, EntityStatusChanged):
            changes = {
                'status': {'from': event.from_status, 'to': event.to_status}
            }
        elif isinstance(event, EntityAssigned):
            changes = {
                'assigned_to': {
                    'from': event.previous_assignee_username or 'None',
                    'to': event.assigned_to_username
                }
            }
        
        # Get description
        description = event.description or self._build_description(
            entity_type=event.entity_type,
            action_type=action_type,
            changes=changes,
        )
        
        return self.record_activity(
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            action_type=action_type,
            performed_by=performed_by,
            performed_by_username=performed_by_username,
            performed_by_role=performed_by_role,
            changes=changes,
            description=description,
            timestamp=event.timestamp if hasattr(event, 'timestamp') else None,
        )
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _map_event_to_action(self, event: Any) -> str:
        """Map domain event to action type."""
        event_type = getattr(event, 'event_type', '') or getattr(event, 'event_type', '')
        
        # Handle string event types
        if isinstance(event_type, str):
            if 'created' in event_type.lower():
                return ActionType.CREATED
            elif 'deleted' in event_type.lower():
                return ActionType.DELETED
            elif 'status_changed' in event_type.lower():
                return ActionType.STATUS_CHANGED
            elif 'assigned' in event_type.lower():
                return ActionType.ASSIGNED
            elif 'unassigned' in event_type.lower():
                return ActionType.UNASSIGNED
            elif 'resolved' in event_type.lower():
                return ActionType.RESOLVED
            elif 'reopened' in event_type.lower():
                return ActionType.REOPENED
            elif 'updated' in event_type.lower():
                return ActionType.UPDATED
        
        # Handle event classes
        if isinstance(event, EntityCreated):
            return ActionType.CREATED
        elif isinstance(event, EntityUpdated):
            return ActionType.UPDATED
        elif isinstance(event, EntityDeleted):
            return ActionType.DELETED
        elif isinstance(event, EntityStatusChanged):
            return ActionType.STATUS_CHANGED
        elif isinstance(event, EntityAssigned):
            return ActionType.ASSIGNED
        
        return ActionType.UPDATED
    
    def _build_changes_from_event(self, event: EntityUpdated) -> Dict[str, Any]:
        """Build changes dictionary from update event."""
        changes = {}
        
        if event.changes:
            for field, (old, new) in event.changes.items():
                changes[field] = {'from': str(old), 'to': str(new)}
        
        return changes
    
    def _build_description(
        self,
        entity_type: str,
        action_type: str,
        changes: Dict[str, Any],
    ) -> str:
        """Build human-readable description."""
        action_verbs = {
            ActionType.CREATED: "created",
            ActionType.UPDATED: "updated",
            ActionType.DELETED: "deleted",
            ActionType.STATUS_CHANGED: "changed status of",
            ActionType.ASSIGNED: "assigned",
            ActionType.UNASSIGNED: "unassigned",
            ActionType.RESOLVED: "resolved",
            ActionType.REOPENED: "reopened",
        }
        
        verb = action_verbs.get(action_type, action_type.lower())
        
        if changes and action_type == ActionType.UPDATED:
            changed_fields = list(changes.keys())
            if changed_fields:
                fields_str = ", ".join(changed_fields[:3])
                if len(changed_fields) > 3:
                    fields_str += f" and {len(changed_fields) - 3} more"
                return f"{verb} {entity_type}: {fields_str}"
        
        return f"{verb} {entity_type}"
    
    # =========================================================================
    # Query Methods (requires repository)
    # =========================================================================
    
    def get_entity_history(
        self,
        entity_type: str,
        entity_id: Any,
        limit: int = 100,
    ) -> List[ActivityLogEntity]:
        """Get activity history for an entity."""
        if not self._repository:
            raise RuntimeError("Repository not configured")
        return self._repository.get_by_entity(entity_type, entity_id, limit)
    
    def get_user_activity(
        self,
        user_id: str,
        limit: int = 100,
    ) -> List[ActivityLogEntity]:
        """Get activity performed by a user."""
        if not self._repository:
            raise RuntimeError("Repository not configured")
        return self._repository.get_by_user(user_id, limit)
    
    def get_timeline(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        entity_type: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[ActivityLogEntity]:
        """Get activity timeline with filters."""
        if not self._repository:
            raise RuntimeError("Repository not configured")
        
        # Default date range to last 30 days if not specified
        if not start_date:
            start_date = datetime.utcnow()
        if not end_date:
            end_date = datetime.utcnow()
        
        return self._repository.get_by_date_range(
            start_date=start_date,
            end_date=end_date,
            entity_type=entity_type,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )


# =============================================================================
# Singleton Instance
# =============================================================================

# Global service instance (will be configured with repository)
_activity_log_service: Optional[ActivityLogService] = None


def get_activity_log_service() -> ActivityLogService:
    """Get the global activity log service instance."""
    global _activity_log_service
    if _activity_log_service is None:
        _activity_log_service = ActivityLogService()
    return _activity_log_service


def set_activity_log_service(service: ActivityLogService) -> None:
    """Set the global activity log service instance."""
    global _activity_log_service
    _activity_log_service = service

