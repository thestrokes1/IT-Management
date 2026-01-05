"""
Frontend permissions module.
Placeholder for future permission implementations.
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
    Custom frontend permissions class.
    """
    
    @staticmethod
    def can_manage_users(user):
        """Check if user can manage other users."""
        if not user.is_authenticated:
            return False
        return user.role in ['ADMIN', 'SUPERADMIN'] or user.is_superuser
    
    @staticmethod
    def can_manage_tickets(user):
        """Check if user can manage tickets."""
        if not user.is_authenticated:
            return False
        return user.role in ['ADMIN', 'SUPERADMIN', 'TICKET_MANAGER'] or user.is_superuser
    
    @staticmethod
    def can_manage_projects(user):
        """Check if user can manage projects."""
        if not user.is_authenticated:
            return False
        return user.role in ['ADMIN', 'SUPERADMIN', 'PROJECT_MANAGER'] or user.is_superuser
    
    @staticmethod
    def can_manage_assets(user):
        """Check if user can manage assets."""
        if not user.is_authenticated:
            return False
        return user.role in ['ADMIN', 'SUPERADMIN', 'ASSET_MANAGER'] or user.is_superuser
    
    @staticmethod
    def can_view_reports(user):
        """Check if user can view reports."""
        if not user.is_authenticated:
            return False
        return user.role in ['ADMIN', 'SUPERADMIN', 'MANAGER', 'REPORTS_VIEWER'] or user.is_superuser
    
    @staticmethod
    def can_view_logs(user):
        """Check if user can view system logs."""
        if not user.is_authenticated:
            return False
        return user.role in ['ADMIN', 'SUPERADMIN'] or user.is_superuser
    
    @staticmethod
    def can_manage_settings(user):
        """Check if user can manage system settings."""
        if not user.is_authenticated:
            return False
        return user.role in ['ADMIN', 'SUPERADMIN'] or user.is_superuser

