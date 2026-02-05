"""
Custom template tags and filters for the IT Management Platform frontend.

This module provides custom template filters for mathematical operations,
dictionary access, and other utilities used across frontend templates.

Usage:
    {% load custom_filters %}
    
    {# Mathematical operations #}
    {{ value|divide:total }}
    {{ percent|multiply:100 }}
    
    {# Dictionary access #}
    {{ my_dict|get_item:key }}
"""

from django import template

register = template.Library()


@register.filter
def divide(value, arg):
    """
    Divide value by arg.
    
    Safely divides two values and returns the result.
    Returns 0 if division by zero or if values cannot be converted to float.
    
    Usage:
        {{ total|divide:count }}
        {{ data.count|divide:total }}
    """
    try:
        value = float(value)
        arg = float(arg)
        if arg == 0:
            return 0
        return value / arg
    except (ValueError, TypeError):
        return 0


@register.filter
def mul(value, arg):
    """
    Multiply value by arg.
    
    Multiplies two values and returns the result.
    Returns 0 if values cannot be converted to float.
    
    Usage:
        {{ percent|mul:100 }}
        {{ count|mul:2 }}
    """
    try:
        value = float(value)
        arg = float(arg)
        return value * arg
    except (ValueError, TypeError):
        return 0


@register.filter
def multiply(value, arg):
    """
    Multiply value by arg.
    
    Alias for 'mul' filter with explicit naming.
    Multiplies two values and returns the result.
    Returns 0 if values cannot be converted to float.
    
    Usage:
        {{ percent|multiply:100 }}
        {{ count|multiply:2 }}
    """
    try:
        value = float(value)
        arg = float(arg)
        return value * arg
    except (ValueError, TypeError):
        return 0


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
    """
    if dictionary is None:
        return None
    
    if not isinstance(dictionary, dict):
        return None
    
    # Handle different key types
    if isinstance(key, str):
        if key.isdigit():
            key = int(key)
    elif isinstance(key, bool):
        key = str(key).lower()
    
    return dictionary.get(key)

