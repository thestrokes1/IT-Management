"""
Utility functions for change detection in use cases.

Provides functions to detect and track field-level changes for activity logging.
"""

from typing import Any, Dict, List, Optional


def get_changed_fields(original_instance: Any, updated_data: Dict) -> List[Dict[str, Any]]:
    """
    Detect changes between original instance and updated data.
    
    Compares the original model instance with the incoming update data
    and returns only the fields that have actually changed.
    
    Args:
        original_instance: The original model instance before update
        updated_data: Dictionary of field names and new values
        
    Returns:
        List of dictionaries, each containing:
        - 'field': The field name that changed
        - 'old': The original value
        - 'new': The new value
        
    Example:
        >>> original = Asset(name='Old Name', status='ACTIVE')
        >>> updated = {'name': 'New Name', 'status': 'ACTIVE'}
        >>> changes = get_changed_fields(original, updated)
        >>> # Returns [{'field': 'name', 'old': 'Old Name', 'new': 'New Name'}]
        >>> # status is not included because it didn't change
    """
    changes = []
    
    for field, new_value in updated_data.items():
        # Skip if field doesn't exist on the instance
        if not hasattr(original_instance, field):
            continue
            
        old_value = getattr(original_instance, field, None)
        
        # Compare old and new values
        # Handle None vs empty string comparison
        old_val = old_value if old_value is not None else ''
        new_val = new_value if new_value is not None else ''
        
        if str(old_val) != str(new_val):
            changes.append({
                'field': field,
                'old': old_value,
                'new': new_value,
            })
    
    return changes


def format_field_value(value: Any) -> str:
    """
    Format a field value for display in activity logs.
    
    Handles common Django model field types and converts them
    to human-readable strings.
    
    Args:
        value: The field value to format
        
    Returns:
        Human-readable string representation
    """
    if value is None:
        return '-'
    
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    
    if hasattr(value, '__str__'):
        return str(value)
    
    return str(value)


def get_display_field_name(field: str) -> str:
    """
    Convert a model field name to a human-readable display name.
    
    Args:
        field: The technical field name
        
    Returns:
        Human-readable field name
        
    Example:
        >>> get_display_field_name('purchase_cost')
        'Purchase Cost'
        >>> get_display_field_name('contact_phone')
        'Contact Phone'
    """
    # Common field name mappings
    field_mappings = {
        'name': 'Name',
        'description': 'Description',
        'status': 'Status',
        'priority': 'Priority',
        'location': 'Location',
        'serial_number': 'Serial Number',
        'model': 'Model',
        'manufacturer': 'Manufacturer',
        'purchase_cost': 'Purchase Cost',
        'purchase_date': 'Purchase Date',
        'warranty_expiry': 'Warranty Expiry',
        'end_of_life': 'End of Life',
        'contact_type': 'Contact Type',
        'contact_email': 'Contact Email',
        'contact_phone': 'Contact Phone',
        'assigned_to': 'Assigned To',
        'category': 'Category',
        'asset_type': 'Asset Type',
        'title': 'Title',
        'category_id': 'Category',
        'ticket_type_id': 'Ticket Type',
        'assigned_to_id': 'Assigned To',
        'assignment_status': 'Assignment Status',
        'resolution_summary': 'Resolution Summary',
        'impact': 'Impact',
        'urgency': 'Urgency',
    }
    
    return field_mappings.get(field, field.replace('_', ' ').title())

