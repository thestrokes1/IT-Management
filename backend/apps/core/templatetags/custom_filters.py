"""
Core template tags and filters for the IT Management Platform.

This module provides custom template filters that can be used across all templates
in the project. The main filter is `get_item` which enables safe dictionary key access
in Django templates, avoiding TemplateSyntaxError when trying to access dictionary
values with variable keys.

Usage:
    {% load custom_filters %}
    {% with item=my_dict|get_item:key %}
        {{ item.some_attribute }}
    {% endwith %}
"""

from django import template

# Create a Library instance to register template tags and filters
register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Safely retrieve a value from a dictionary by key.
    
    This filter fixes the Django template limitation where you cannot use
    bracket notation (dict[key]) with variable keys. Instead, use:
        {{ dictionary|get_item:key }}
    
    Args:
        dictionary: The dictionary to retrieve the value from. Can be None.
        key: The key to look up. Can be an integer, string, or any hashable type.
    
    Returns:
        The value at the given key, or None if the key doesn't exist or
        the dictionary is None/empty.
    
    Usage Examples:
        {% with perms=permissions_by_ticket|get_item:ticket.id %}
            {% if perms.can_update %}...{% endif %}
        {% endwith %}
        
        {% with user_perms=permissions_map|get_item:user.id %}
            {{ user_perms.can_delete }}
        {% endwith %}
        
        {% with project_data=projects_dict|get_item:project.id %}
            {{ project_data.can_update }}
        {% endwith %}
    
    Note:
        This filter returns None (rendered as empty string in templates)
        if the key is not found, which makes it safe to use in conditional
        statements like {% if %}.
    """
    # Return None early if dictionary is None or not a dict
    if dictionary is None:
        return None
    
    if not isinstance(dictionary, dict):
        return None
    
    # Handle different key types
    # If key is a string that looks like a number, try to convert to int
    # This handles cases where template variables might be strings
    if isinstance(key, str):
        # Check if it's a numeric string
        if key.isdigit():
            key = int(key)
    elif isinstance(key, bool):
        # Convert boolean to string for dict key lookup
        key = str(key).lower()
    
    # Use dict.get() which returns None if key not found
    # This is safer than dictionary[key] which would raise KeyError
    return dictionary.get(key)

