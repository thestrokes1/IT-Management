"""
Frontend permissions module.
Role-based access control for frontend views and actions.
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
    Uses the approved menu access matrix:
    
    | Menu Item   | SUPERADMIN | IT_ADMIN | MANAGER | TECHNICIAN | VIEWER |
    |-------------|------------|----------|---------|------------|--------|
    | Dashboard   | ✅         | ✅       | ✅      | ✅         | ✅     |
    | Assets      | ✅         | ✅       | ✅      | ❌         | ❌     |
    | Projects    | ✅         | ❌       | ✅      | ❌         | ❌     |
    | Tickets     | ✅         | ✅       | ✅      | ✅         | ✅     |
    | Users       | ✅         | ✅       | ✅      | ❌         | ❌     |
    | Logs        | ✅         | ❌       | ✅      | ❌         | ❌     |
    | Reports     | ✅         | ❌       | ✅      | ❌         | ❌     |
    """
    
    # Role-based menu access configuration
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
            'TECHNICIAN': False,
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
            'IT_ADMIN': False,
            'MANAGER': True,
            'TECHNICIAN': False,
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
        """Check if user can manage other users (SUPERADMIN, IT_ADMIN, MANAGER)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
    
    @staticmethod
    def can_manage_tickets(user):
        """Check if user can manage tickets (All roles can access)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER']
    
    @staticmethod
    def can_manage_projects(user):
        """Check if user can manage projects (SUPERADMIN, MANAGER only)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'MANAGER']
    
    @staticmethod
    def can_manage_assets(user):
        """Check if user can manage assets (SUPERADMIN, IT_ADMIN, MANAGER)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
    
    @staticmethod
    def can_view_reports(user):
        """Check if user can view reports (SUPERADMIN, MANAGER only)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'MANAGER']
    
    @staticmethod
    def can_view_logs(user):
        """Check if user can view system logs (SUPERADMIN, MANAGER only)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'MANAGER']
    
    @staticmethod
    def can_manage_settings(user):
        """Check if user can manage system settings (SUPERADMIN, IT_ADMIN only)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'IT_ADMIN']
    
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
        return user.role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER']
    
    @staticmethod
    def can_access_assets(user):
        """Check if user can access Assets menu (SUPERADMIN, IT_ADMIN, MANAGER)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
    
    @staticmethod
    def can_access_projects(user):
        """Check if user can access Projects menu (SUPERADMIN, MANAGER only)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'MANAGER']
    
    @staticmethod
    def can_access_tickets(user):
        """Check if user can access Tickets menu - All roles can access."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER']
    
    @staticmethod
    def can_access_users(user):
        """Check if user can access Users menu (SUPERADMIN, IT_ADMIN, MANAGER)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
    
    @staticmethod
    def can_access_logs(user):
        """Check if user can access Logs menu (SUPERADMIN, MANAGER only)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'MANAGER']
    
    @staticmethod
    def can_access_reports(user):
        """Check if user can access Reports menu (SUPERADMIN, MANAGER only)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'MANAGER']
    
    @staticmethod
    def is_admin(user):
        """Check if user has admin privileges (SUPERADMIN, IT_ADMIN)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'IT_ADMIN']
    
    @staticmethod
    def is_manager(user):
        """Check if user has manager privileges (SUPERADMIN, IT_ADMIN, MANAGER)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
    
    @staticmethod
    def is_technician(user):
        """Check if user has technician privileges (TECHNICIAN and above)."""
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN']
    
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
        
        creation_rules = {
            'user': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER'],
            'asset': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER'],
            'project': ['SUPERADMIN', 'MANAGER'],
            'ticket': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER'],
            'report': ['SUPERADMIN', 'MANAGER'],
        }
        
        allowed_roles = creation_rules.get(resource_type, [])
        return user.role in allowed_roles
    
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
        
        edit_rules = {
            'user': ['SUPERADMIN', 'IT_ADMIN'],
            'asset': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER'],
            'project': ['SUPERADMIN', 'MANAGER'],
            'ticket': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN'],
            'report': ['SUPERADMIN', 'MANAGER'],
        }
        
        allowed_roles = edit_rules.get(resource_type, [])
        return user.role in allowed_roles
    
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
        
        delete_rules = {
            'user': ['SUPERADMIN', 'IT_ADMIN'],
            'asset': ['SUPERADMIN', 'IT_ADMIN'],
            'project': ['SUPERADMIN', 'MANAGER'],
            'ticket': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER'],
            'report': ['SUPERADMIN', 'MANAGER'],
        }
        
        allowed_roles = delete_rules.get(resource_type, [])
        return user.role in allowed_roles

