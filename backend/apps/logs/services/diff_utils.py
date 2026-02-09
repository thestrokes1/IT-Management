"""
Diff utilities for activity logging.

Provides diff generation and rendering for entity updates.
Stores before/after values and renders readable diffs.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class FieldDiff:
    """Represents a single field change."""
    field_name: str
    old_value: Any
    new_value: Any
    
    @property
    def has_changed(self) -> bool:
        """Check if the field actually changed."""
        return self.old_value != self.new_value
    
    @property
    def old_display(self) -> str:
        """Get human-readable old value."""
        return self._format_value(self.old_value)
    
    @property
    def new_display(self) -> str:
        """Get human-readable new value."""
        return self._format_value(self.new_value)
    
    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if value is None:
            return "Empty"
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, dict):
            return str(value)
        return str(value)


@dataclass
class EntityDiff:
    """
    Represents changes to an entity.
    
    Use generate_diff() to create from old/new instances.
    Use from_dict() to restore from stored extra_data.
    """
    entity_type: str  # 'ticket', 'asset', 'project', 'user'
    entity_id: Optional[int]
    field_diffs: List[FieldDiff] = field(default_factory=list)
    
    @property
    def has_changes(self) -> bool:
        """Check if there are any actual changes."""
        return any(diff.has_changed for diff in self.field_diffs)
    
    @property
    def changed_fields(self) -> List[str]:
        """Get list of changed field names."""
        return [diff.field_name for diff in self.field_diffs if diff.has_changed]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage in extra_data."""
        return {
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'changes': [
                {
                    'field': diff.field_name,
                    'old': diff.old_value,
                    'new': diff.new_value,
                }
                for diff in self.field_diffs
            ],
            'changed_fields': self.changed_fields,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntityDiff':
        """Deserialize from stored extra_data."""
        field_diffs = [
            FieldDiff(
                field_name=change['field'],
                old_value=change.get('old'),
                new_value=change.get('new'),
            )
            for change in data.get('changes', [])
        ]
        return cls(
            entity_type=data.get('entity_type', ''),
            entity_id=data.get('entity_id'),
            field_diffs=field_diffs,
        )


def generate_diff(
    old_instance: Any,
    new_instance: Any,
    field_mapping: Optional[Dict[str, str]] = None,
    ignore_fields: Optional[List[str]] = None,
) -> EntityDiff:
    """
    Generate a diff between two model instances.
    
    Args:
        old_instance: The original model instance (or dict)
        new_instance: The updated model instance (or dict)
        field_mapping: Map of model field names to display labels
                      e.g., {'status': 'Status', 'priority': 'Priority'}
        ignore_fields: List of field names to skip (e.g., ['updated_at'])
    
    Returns:
        EntityDiff with all field changes
        
    Example:
        >>> old = Ticket(title="Bug", priority="LOW", status="NEW")
        >>> new = Ticket(title="Bug", priority="HIGH", status="IN_PROGRESS")
        >>> diff = generate_diff(old, new, ignore_fields=['updated_at'])
        >>> diff.changed_fields
        ['priority', 'status']
    """
    # Convert to dicts if instances
    old_dict = _get_dict(old_instance)
    new_dict = _get_dict(new_instance)
    
    # Default mappings
    field_mapping = field_mapping or {}
    ignore_fields = ignore_fields or ['updated_at', 'created_at', 'modified_at']
    
    # Get all field names
    all_fields = set(old_dict.keys()) | set(new_dict.keys())
    
    field_diffs = []
    for field_name in all_fields:
        if field_name in ignore_fields:
            continue
            
        old_val = old_dict.get(field_name)
        new_val = new_dict.get(field_name)
        
        # Skip if both are None/null
        if old_val is None and new_val is None:
            continue
        
        # Create diff
        diff = FieldDiff(
            field_name=field_mapping.get(field_name, field_name.title()),
            old_value=old_val,
            new_value=new_val,
        )
        
        if diff.has_changed:
            field_diffs.append(diff)
    
    # Determine entity type and ID
    entity_type = getattr(old_instance, '_meta', None) or getattr(new_instance, '_meta', None)
    if entity_type:
        entity_type = entity_type.model_name
    else:
        # Try to infer from class name
        class_name = type(old_instance).__name__
        if 'Ticket' in class_name:
            entity_type = 'ticket'
        elif 'Asset' in class_name:
            entity_type = 'asset'
        elif 'Project' in class_name:
            entity_type = 'project'
        elif 'User' in class_name:
            entity_type = 'user'
        else:
            entity_type = class_name.lower()
    
    entity_id = new_dict.get('id') or old_dict.get('id')
    
    return EntityDiff(
        entity_type=entity_type or 'unknown',
        entity_id=entity_id,
        field_diffs=field_diffs,
    )


def _get_dict(instance: Any) -> Dict[str, Any]:
    """Convert model instance to dict."""
    if instance is None:
        return {}
    
    if isinstance(instance, dict):
        return instance
    
    # Django model instance
    if hasattr(instance, '_meta'):
        return {
            field.name: getattr(instance, field.name)
            for field in instance._meta.fields
            if hasattr(instance, field.name)
        }
    
    # Fallback to __dict__
    return instance.__dict__


# Pre-defined field mappings for common models
TICKET_FIELD_MAPPING = {
    'title': 'Title',
    'description': 'Description',
    'status': 'Status',
    'priority': 'Priority',
    'category': 'Category',
    'assigned_to': 'Assigned To',
    'due_date': 'Due Date',
}

ASSET_FIELD_MAPPING = {
    'name': 'Name',
    'description': 'Description',
    'status': 'Status',
    'category': 'Category',
    'assigned_to': 'Assigned To',
    'location': 'Location',
    'serial_number': 'Serial Number',
}

PROJECT_FIELD_MAPPING = {
    'name': 'Name',
    'description': 'Description',
    'status': 'Status',
    'start_date': 'Start Date',
    'end_date': 'End Date',
    'budget': 'Budget',
}

USER_FIELD_MAPPING = {
    'username': 'Username',
    'email': 'Email',
    'first_name': 'First Name',
    'last_name': 'Last Name',
    'role': 'Role',
    'is_active': 'Active',
}


def log_entity_update(
    user: Any,
    action: str,
    old_instance: Any,
    new_instance: Any,
    entity_type: str,
    field_mapping: Optional[Dict[str, str]] = None,
    request: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Convenience function to generate diff and prepare log data.
    
    Args:
        user: The user performing the update
        action: The action type (e.g., 'TICKET_UPDATED')
        old_instance: Original instance
        new_instance: Updated instance
        entity_type: Type of entity ('ticket', 'asset', etc.)
        field_mapping: Custom field name mappings
        request: Optional request for IP address
    
    Returns:
        Dict with 'description' and 'extra_data' for logging
        
    Example:
        >>> result = log_entity_update(
        ...     user=request.user,
        ...     action='TICKET_UPDATED',
        ...     old_instance=ticket_before,
        ...     new_instance=ticket_after,
        ...     entity_type='ticket',
        ...     field_mapping=TICKET_FIELD_MAPPING,
        ... )
        >>> # Use result['description'] and result['extra_data'] in log
    """
    diff = generate_diff(
        old_instance,
        new_instance,
        field_mapping=field_mapping,
    )
    
    # Build description
    if diff.has_changes:
        changes_str = ', '.join(diff.changed_fields)
        description = f"Updated {entity_type}: {changes_str}"
    else:
        description = f"Updated {entity_type} (no changes detected)"
    
    # Build extra_data
    extra_data = {
        'diff': diff.to_dict(),
        'actor_name': getattr(user, 'username', 'System'),
        'actor_role': getattr(user, 'role', 'VIEWER') if user else 'VIEWER',
    }
    
    if request:
        extra_data['ip_address'] = get_client_ip(request)
    
    return {
        'description': description,
        'extra_data': extra_data,
        'diff': diff,
    }


def get_client_ip(request: Any) -> str:
    """Extract client IP from request."""
    if not request:
        return ''
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')
