"""
Template tags for menu permissions.
Provides template-level access control for menu items based on user roles.

All permission checks delegate to the User model's can_access_* properties
for consistency with the backend permission system.

Menu Access Matrix:
| Menu Item   | SUPERADMIN | IT_ADMIN | MANAGER | TECHNICIAN | VIEWER |
|-------------|------------|----------|---------|------------|--------|
| Dashboard   | ✅         | ✅       | ✅      | ✅         | ✅     |
| Assets      | ✅         | ✅       | ✅      | ✅         | ❌     |
| Projects    | ✅         | ❌       | ✅      | ❌         | ❌     |
| Tickets     | ✅         | ✅       | ✅      | ✅         | ✅     |
| Users       | ✅         | ✅       | ✅      | ❌         | ❌     |
| Logs        | ✅         | ✅       | ✅      | ✅         | ❌     |
| Reports     | ✅         | ❌       | ✅      | ❌         | ❌     |
"""

from django import template
from django.utils.safestring import mark_safe
from django.template import TemplateSyntaxError

register = template.Library()

# Menu access configuration based on role - kept for backward compatibility
# but can_access_menu() now delegates to user.can_access_* properties
MENU_ACCESS = {
    'dashboard': {
        'SUPERADMIN': True,
        'IT_ADMIN': True,
        'MANAGER': True,
        'TECHNICIAN': True,
        'VIEWER': True,
    },
    'assets': {
        'SUPERADMIN': True,
        'IT_ADMIN': True,
        'MANAGER': True,
        'TECHNICIAN': True,
        'VIEWER': False,
    },
    'projects': {
        'SUPERADMIN': True,
        'IT_ADMIN': False,
        'MANAGER': True,
        'TECHNICIAN': False,
        'VIEWER': False,
    },
    'tickets': {
        'SUPERADMIN': True,
        'IT_ADMIN': True,
        'MANAGER': True,
        'TECHNICIAN': True,
        'VIEWER': True,
    },
    'users': {
        'SUPERADMIN': True,
        'IT_ADMIN': True,
        'MANAGER': True,
        'TECHNICIAN': False,
        'VIEWER': False,
    },
    'logs': {
        'SUPERADMIN': True,
        'IT_ADMIN': True,
        'MANAGER': True,
        'TECHNICIAN': True,
        'VIEWER': False,
    },
    'reports': {
        'SUPERADMIN': True,
        'IT_ADMIN': False,
        'MANAGER': True,
        'TECHNICIAN': False,
        'VIEWER': False,
    },
}

# Map menu names to User model properties
MENU_PROPERTY_MAP = {
    'dashboard': 'can_access_dashboard',
    'assets': 'can_access_assets',
    'projects': 'can_access_projects',
    'tickets': 'can_access_tickets',
    'users': 'can_access_users',
    'logs': 'can_access_logs',
    'reports': 'can_access_reports',
}


@register.simple_tag
def can_access_menu(menu_name, user):
    """
    Check if a user can access a specific menu item.
    
    Usage: {% can_access_menu 'assets' user %}
    
    Returns: 'True' if user can access the menu, 'False' otherwise.
    """
    if not user.is_authenticated:
        return False
    
    # Superusers always have access
    if user.is_superuser:
        return True
    
    # Map menu name to user model property and delegate
    prop_name = MENU_PROPERTY_MAP.get(menu_name)
    if prop_name and hasattr(user, prop_name):
        return getattr(user, prop_name)
    
    # Fallback to MENU_ACCESS dict for backward compatibility
    user_role = getattr(user, 'role', 'VIEWER')
    if menu_name in MENU_ACCESS:
        return MENU_ACCESS[menu_name].get(user_role, False)
    
    return False


@register.simple_tag
def menu_access_class(menu_name, user):
    """
    Returns CSS class for menu item based on access.
    
    Usage: {% menu_access_class 'assets' user as menu_class %}
    
    Returns: 'hidden' if user cannot access the menu, '' otherwise.
    """
    if not can_access_menu(menu_name, user):
        return 'hidden'
    return ''


@register.simple_tag
def if_menu_access(menu_name, user):
    """
    Block tag to conditionally show menu items.
    
    Usage: 
        {% if_menu_access 'assets' user %}
            <a href="...">Assets</a>
        {% endif_menu_access %}
    """
    return can_access_menu(menu_name, user)


@register.filter
def has_role(user, roles):
    """
    Check if user has any of the specified roles.
    
    Usage: {% if user|has_role:"SUPERADMIN,IT_ADMIN" %}
    
    Returns: True if user has any of the roles.
    """
    if not user.is_authenticated:
        return False
    
    user_role = getattr(user, 'role', None)
    if not user_role:
        return False
    
    # Handle comma-separated roles or single role
    if isinstance(roles, str):
        role_list = [r.strip() for r in roles.split(',')]
    else:
        role_list = list(roles)
    
    return user_role in role_list


@register.simple_tag
def user_has_access(user, menu_item):
    """
    Alternative function to check menu access.
    
    Usage: {% user_has_access user 'assets' %}
    """
    return can_access_menu(menu_item, user)


@register.simple_tag
def get_accessible_menus(user):
    """
    Get list of menu items that the user can access.
    
    Usage: {% get_accessible_menus user as menus %}
    
    Returns: List of menu names user can access.
    """
    if not user.is_authenticated:
        return []
    
    # Superusers have access to all menus
    if user.is_superuser:
        return list(MENU_ACCESS.keys())
    
    accessible = []
    for menu_name in MENU_ACCESS.keys():
        if can_access_menu(menu_name, user):
            accessible.append(menu_name)
    
    return accessible


@register.simple_tag
def show_menu_item(menu_name, user):
    """
    Determine if a menu item should be shown.
    
    Usage: {% show_menu_item 'assets' user as show_assets %}
    
    Returns: True if menu item should be displayed.
    """
    return can_access_menu(menu_name, user)
