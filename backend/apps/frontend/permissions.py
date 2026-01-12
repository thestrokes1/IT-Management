"""
Frontend permissions module.
Role-based access control for frontend views and actions.

All permission checks delegate to the User model's can_* properties,
which use the role_level hierarchy for consistency.

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

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


def get_user_permissions(user):
    """
    Get all permissions for a user including group permissions.
    """
    if not user.is_authenticated:
        return set()
    
    permissions = set()
    
    # Get user's direct permissions
    for perm in user.user_permissions.all():
        permissions.add(f"{perm.content_type.app_label}.{perm.codename}")
    
    # Get user's group permissions
    for group in user.groups.all():
        for perm in group.permissions.all():
            permissions.add(f"{perm.content_type.app_label}.{perm.codename}")
    
    return permissions


def has_permission(user, permission):
    """
    Check if user has a specific permission.
    """
    if not user.is_authenticated:
        return False
    
    # Superusers have all permissions
    if user.is_superuser:
        return True
    
    # Check direct permissions
    if user.user_permissions.filter(codename=permission).exists():
        return True
    
    # Check group permissions
    for group in user.groups.all():
        if group.permissions.filter(codename=permission).exists():
            return True
    
    return False


class FrontendPermissions:
    """
    Custom frontend permissions class with role-based access control.
    
    All methods delegate to the User model's properties for consistency.
    """
    
    # Role-based menu access configuration - kept for backward compatibility
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
    
    @staticmethod
    def can_manage_users(user):
        """Check if user can manage other users (IT_ADMIN or SUPERADMIN)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.can_manage_users
    
    @staticmethod
    def can_manage_tickets(user):
        """Check if user can manage tickets (All roles can access)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.can_manage_tickets
    
    @staticmethod
    def can_manage_projects(user):
        """Check if user can manage projects (MANAGER only - IT_ADMIN excluded)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.can_manage_projects
    
    @staticmethod
    def can_manage_assets(user):
        """Check if user can manage assets (MANAGER or above)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.can_manage_assets
    
    @staticmethod
    def can_view_reports(user):
        """Check if user can view reports (MANAGER only - IT_ADMIN excluded)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.can_view_reports
    
    @staticmethod
    def can_view_logs(user):
        """Check if user can view system logs (MANAGER or IT_ADMIN or SUPERADMIN)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.can_view_logs
    
    @staticmethod
    def can_manage_settings(user):
        """Check if user can manage system settings (IT_ADMIN or SUPERADMIN only)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.can_manage_settings
    
    @staticmethod
    def can_access_menu(user, menu_name):
        """
        Check if user can access a specific menu based on the menu access matrix.
        
        Args:
            user: The user object
            menu_name: The menu name (dashboard, assets, projects, tickets, users, logs, reports)
            
        Returns:
            bool: True if user can access the menu, False otherwise
        """
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # Map menu names to user model properties
        menu_property_map = {
            'dashboard': 'can_access_dashboard',
            'assets': 'can_access_assets',
            'projects': 'can_access_projects',
            'tickets': 'can_access_tickets',
            'users': 'can_access_users',
            'logs': 'can_access_logs',
            'reports': 'can_access_reports',
        }
        
        prop_name = menu_property_map.get(menu_name)
        if prop_name and hasattr(user, prop_name):
            return getattr(user, prop_name)
        
        # Fallback to MENU_ACCESS dict for backward compatibility
        user_role = getattr(user, 'role', 'VIEWER')
        if menu_name in FrontendPermissions.MENU_ACCESS:
            return FrontendPermissions.MENU_ACCESS[menu_name].get(user_role, False)
        
        return False
    
    @staticmethod
    def can_access_dashboard(user):
        """Check if user can access dashboard - All roles can access."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.can_access_dashboard
    
    @staticmethod
    def can_access_assets(user):
        """Check if user can access Assets menu (MANAGER or above)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.can_access_assets
    
    @staticmethod
    def can_access_projects(user):
        """Check if user can access Projects menu (MANAGER only - IT_ADMIN excluded)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.can_access_projects
    
    @staticmethod
    def can_access_tickets(user):
        """Check if user can access Tickets menu - All roles can access."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.can_access_tickets
    
    @staticmethod
    def can_access_users(user):
        """Check if user can access Users menu (MANAGER or above)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.can_access_users
    
    @staticmethod
    def can_access_logs(user):
        """Check if user can access Logs menu (MANAGER or IT_ADMIN or SUPERADMIN)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.can_access_logs
    
    @staticmethod
    def can_access_reports(user):
        """Check if user can access Reports menu (MANAGER only - IT_ADMIN excluded)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.can_access_reports
    
    @staticmethod
    def is_admin(user):
        """Check if user has admin privileges (IT_ADMIN or SUPERADMIN)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.is_admin
    
    @staticmethod
    def is_manager(user):
        """Check if user has manager privileges (MANAGER or above)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.is_manager
    
    @staticmethod
    def is_technician(user):
        """Check if user has technician privileges (TECHNICIAN and above)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.is_technician
    
    @staticmethod
    def can_create(user, resource_type):
        """
        Check if user can create a specific resource type.
        
        Args:
            user: The user object
            resource_type: Type of resource (user, asset, project, ticket, report)
            
        Returns:
            bool: True if user can create the resource, False otherwise
        """
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # Delegate to user model properties
        creation_rules = {
            'user': 'can_manage_users',
            'asset': 'can_manage_assets',
            'project': 'can_manage_projects',
            'ticket': 'can_manage_tickets',
            'report': 'can_create_reports',
        }
        
        prop_name = creation_rules.get(resource_type)
        if prop_name and hasattr(user, prop_name):
            return getattr(user, prop_name)
        
        return False
    
    @staticmethod
    def can_edit(user, resource_type, owner=None):
        """
        Check if user can edit a specific resource.
        
        Args:
            user: The user object
            resource_type: Type of resource
            owner: The user who owns the resource (optional)
            
        Returns:
            bool: True if user can edit the resource, False otherwise
        """
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # Users can always edit their own resources
        if owner and user == owner:
            return True
        
        # Delegate to user model properties
        edit_rules = {
            'user': 'can_manage_users',
            'asset': 'can_manage_assets',
            'project': 'can_manage_projects',
            'ticket': 'can_manage_tickets',
            'report': 'can_manage_projects',
        }
        
        prop_name = edit_rules.get(resource_type)
        if prop_name and hasattr(user, prop_name):
            return getattr(user, prop_name)
        
        return False
    
    @staticmethod
    def can_delete(user, resource_type):
        """
        Check if user can delete a specific resource.
        
        Args:
            user: The user object
            resource_type: Type of resource
            
        Returns:
            bool: True if user can delete the resource, False otherwise
        """
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        # Map resource types to user model properties
        delete_rules = {
            'user': 'can_manage_users',
            'asset': 'can_manage_assets',
            'project': 'can_manage_projects',
            'ticket': 'can_manage_tickets',
            'report': 'can_manage_projects',
        }
        
        prop_name = delete_rules.get(resource_type)
        if prop_name and hasattr(user, prop_name):
            return getattr(user, prop_name)
        
        return False

