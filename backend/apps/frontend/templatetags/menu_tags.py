"""
Custom template tags for menu access control.
Provides block tag {% if_menu_access %}...{% endif_menu_access %} for conditional menu rendering.

Menu Access Matrix:
| Menu Item   | SUPERADMIN | IT_ADMIN | MANAGER | TECHNICIAN | VIEWER |
|-------------|------------|----------|---------|------------|--------|
| Dashboard   | YES        | YES      | YES     | YES        | YES    |
| Assets      | YES        | YES      | YES     | YES        | NO     |
| Projects    | YES        | NO       | YES     | NO         | NO     |
| Tickets     | YES        | YES      | YES     | YES        | YES    |
| Users       | YES        | YES      | YES     | NO         | NO     |
| Logs        | YES        | YES      | YES     | YES        | NO     |
| Reports     | YES        | NO       | YES     | NO         | NO     |
"""

from django import template
from django.template import Library, Context, TemplateSyntaxError

register = template.Library()

# Menu access configuration based on role
MENU_ACCESS = {
    'dashboard': {'SUPERADMIN': True, 'IT_ADMIN': True, 'MANAGER': True, 'TECHNICIAN': True, 'VIEWER': True},
    'assets': {'SUPERADMIN': True, 'IT_ADMIN': True, 'MANAGER': True, 'TECHNICIAN': True, 'VIEWER': False},
    'projects': {'SUPERADMIN': True, 'IT_ADMIN': False, 'MANAGER': True, 'TECHNICIAN': False, 'VIEWER': False},
    'tickets': {'SUPERADMIN': True, 'IT_ADMIN': True, 'MANAGER': True, 'TECHNICIAN': True, 'VIEWER': True},
    'users': {'SUPERADMIN': True, 'IT_ADMIN': True, 'MANAGER': True, 'TECHNICIAN': False, 'VIEWER': False},
    'logs': {'SUPERADMIN': True, 'IT_ADMIN': True, 'MANAGER': True, 'TECHNICIAN': True, 'VIEWER': False},
    'reports': {'SUPERADMIN': True, 'IT_ADMIN': False, 'MANAGER': True, 'TECHNICIAN': False, 'VIEWER': False},
}

MENU_PROPERTY_MAP = {
    'dashboard': 'can_access_dashboard', 'assets': 'can_access_assets', 'projects': 'can_access_projects',
    'tickets': 'can_access_tickets', 'users': 'can_access_users', 'logs': 'can_access_logs', 'reports': 'can_access_reports',
}

class IfMenuAccessNode(template.Node):
    def __init__(self, menu_name_var, user_var, nodelist):
        self.menu_name_var = menu_name_var
        self.user_var = user_var
        self.nodelist = nodelist
    
    def render(self, context):
        try:
            if self.menu_name_var[0] in ('"', "'"):
                menu_name = self.menu_name_var[1:-1]
            else:
                menu_name = template.Variable(self.menu_name_var).resolve(context)
            user = template.Variable(self.user_var).resolve(context)
            if self._can_access_menu(menu_name, user):
                return self.nodelist.render(context)
            return ''
        except Exception:
            return ''
    
    def _can_access_menu(self, menu_name, user):
        if not user or not getattr(user, 'is_authenticated', False):
            return False
        if getattr(user, 'is_superuser', False):
            return True
        user_role = getattr(user, 'role', 'VIEWER')
        if menu_name in MENU_ACCESS:
            return MENU_ACCESS[menu_name].get(user_role, False)
        prop_name = MENU_PROPERTY_MAP.get(menu_name)
        if prop_name and hasattr(user, prop_name):
            return getattr(user, prop_name)
        return False

@register.tag
def if_menu_access(parser, token):
    bits = token.split_contents()
    if len(bits) < 3:
        raise TemplateSyntaxError(f"'{token.contents.split()[0]}' tag requires at least 2 arguments")
    menu_name_var = bits[1]
    user_var = bits[2]
    if 'as' in bits:
        raise TemplateSyntaxError(f"'{token.contents.split()[0]}' tag does not support 'as' clause")
    nodelist = parser.parse(('endif_menu_access',))
    parser.delete_first_token()
    return IfMenuAccessNode(menu_name_var, user_var, nodelist)

@register.simple_tag
def can_access_menu(menu_name, user):
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True
    user_role = getattr(user, 'role', 'VIEWER')
    if menu_name in MENU_ACCESS:
        return MENU_ACCESS[menu_name].get(user_role, False)
    prop_name = MENU_PROPERTY_MAP.get(menu_name)
    if prop_name and hasattr(user, prop_name):
        return getattr(user, prop_name)
    return False

@register.simple_tag
def get_accessible_menus(user):
    if not user or not getattr(user, 'is_authenticated', False):
        return []
    if getattr(user, 'is_superuser', False):
        return list(MENU_ACCESS.keys())
    accessible = []
    for menu_name in MENU_ACCESS.keys():
        if can_access_menu(menu_name, user):
            accessible.append(menu_name)
    return accessible

@register.filter
def has_role(user, roles):
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    user_role = getattr(user, 'role', None)
    if not user_role:
        return False
    if isinstance(roles, str):
        role_list = [r.strip() for r in roles.split(',')]
    else:
        role_list = list(roles)
    return user_role in role_list

@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return ''
    try:
        if isinstance(key, str) and key.isdigit():
            key = int(key)
        elif isinstance(key, bool):
            key = str(key).lower()
        value = dictionary.get(key)
        return value if value is not None else ''
    except (TypeError, AttributeError, KeyError):
        return ''

@register.filter
def get_dict_item(dictionary, key):
    return get_item(dictionary, key)
