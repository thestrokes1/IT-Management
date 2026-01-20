"""
Custom template tags for menu access control.
Provides block tag {% if_menu_access %}...{% endif_menu_access %} for conditional menu rendering.

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
from django.template import Library, Context, TemplateSyntaxError

register = template.Library()

# Menu access configuration based on role
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


class IfMenuAccessNode(template.Node):
    """
    Node for {% if_menu_access %} block tag.
    Renders the block content if user has access to the menu item.
    """
    
    def __init__(self, menu_name_var, user_var, nodelist):
        self.menu_name_var = menu_name_var
        self.user_var = user_var
        self.nodelist = nodelist
    
    def render(self, context):
        try:
            # Resolve menu_name (can be a variable or string literal)
            if self.menu_name_var[0] in ('"', "'"):
                # It's a quoted string literal
                menu_name = self.menu_name_var[1:-1]
            else:
                # It's a variable
                menu_name = template.Variable(self.menu_name_var).resolve(context)
            
            # Resolve user variable
            user = template.Variable(self.user_var).resolve(context)
            
            # Check access
            if self._can_access_menu(menu_name, user):
                return self.nodelist.render(context)
            else:
                return ''
        except Exception:
            # On any error, render nothing (fail silently)
            return ''
    
    def _can_access_menu(self, menu_name, user):
        """Check if user can access the menu item."""
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        
        # Superusers always have access
        if getattr(user, 'is_superuser', False):
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


@register.tag
def if_menu_access(parser, token):
    """
    Block tag to conditionally show menu items based on user permissions.
    
    Usage:
        {% if_menu_access 'assets' user %}
            <a href="{% url 'frontend:assets' %}">Assets</a>
        {% endif_menu_access %}
    
    Or with a variable:
        {% if_menu_access menu_name request.user %}
            ...
        {% endif_menu_access %}
    """
    # Parse the tag arguments
    bits = token.split_contents()
    
    if len(bits) < 3:
        raise TemplateSyntaxError(
            f"'{token.contents.split()[0]}' tag requires at least 2 arguments"
        )
    
    # Extract menu_name and user
    menu_name_var = bits[1]
    user_var = bits[2]
    
    # Check for 'as' clause (not used in this implementation but for future extensibility)
    if 'as' in bits:
        raise TemplateSyntaxError(
            f"'{token.contents.split()[0]}' tag does not support 'as' clause"
        )
    
    # Parse until {% endif_menu_access %}
    nodelist = parser.parse(('endif_menu_access',))
    parser.delete_first_token()
    
    return IfMenuAccessNode(menu_name_var, user_var, nodelist)


@register.simple_tag
def can_access_menu(menu_name, user):
    """
    Check if a user can access a specific menu item.
    
    Usage: {% can_access_menu 'assets' user %}
    
    Returns: True if user can access the menu, False otherwise.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    
    # Superusers always have access
    if getattr(user, 'is_superuser', False):
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
def get_accessible_menus(user):
    """
    Get list of menu items that the user can access.
    
    Usage: {% get_accessible_menus user as menus %}
    
    Returns: List of menu names user can access.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return []
    
    # Superusers have access to all menus
    if getattr(user, 'is_superuser', False):
        return list(MENU_ACCESS.keys())
    
    accessible = []
    for menu_name in MENU_ACCESS.keys():
        if can_access_menu(menu_name, user):
            accessible.append(menu_name)
    
    return accessible


@register.filter
def has_role(user, roles):
    """
    Check if user has any of the specified roles.
    
    Usage: {% if user|has_role:"SUPERADMIN,IT_ADMIN" %}
    
    Returns: True if user has any of the roles.
    """
    if not user or not getattr(user, 'is_authenticated', False):
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


@register.filter
def get_item(dictionary, key):
    """
    Safely retrieve a value from a dictionary by key.
    
    Usage:
        {% if permissions_by_ticket|get_item:ticket.id.can_update %}
        {{ permissions_map|get_item:project.id|get_item:"can_update" }}
        {% with item=permissions_map|get_item:user.id %}{{ item.can_delete }}{% endwith %}
    
    This filter is needed because Django templates don't support
    direct dictionary key access with dot notation like {{ dict.key.value }}.
    
    Returns: The value at the key, or an empty string if not found.
    """
    if dictionary is None:
        return ''
    
    try:
        # Handle different key types
        if isinstance(key, str):
            # For string keys, try to convert to int if it looks like a number
            # This handles cases where key might be "123" vs 123
            if key.isdigit():
                key = int(key)
        elif isinstance(key, bool):
            # Convert boolean to string for dict key lookup
            key = str(key).lower()
        
        # Get the value from dictionary
        value = dictionary.get(key)
        return value if value is not None else ''
    except (TypeError, AttributeError, KeyError):
        # On any error, return empty string
        return ''


@register.filter
def get_dict_item(dictionary, key):
    """
    Alternative name for get_item filter for clarity.
    
    Usage: {% permissions_map|get_dict_item:user.id %}
    """
    return get_item(dictionary, key)

