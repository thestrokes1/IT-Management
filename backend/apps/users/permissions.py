"""
Permissions classes for Users Management.

Role-based access control for user operations.
All permission checks are enforced server-side using domain authority services.

IMPORTANT: IT_ADMIN can only edit TECHNICIAN users.
Cannot edit MANAGER, IT_ADMIN, or SUPERADMIN users.
"""

from rest_framework import permissions
from apps.users.models import User


class CanViewUsers(permissions.BasePermission):
    """
    Check if user can view user list/profiles.
    
    Rules:
    - VIEWER: can only view own profile
    - All other roles: can view any user
    """
    
    def has_permission(self, request, view):
        from apps.users.domain.services.user_authority import can_view_list
        return (
            request.user 
            and request.user.is_authenticated 
            and can_view_list(request.user)
        )
    
    def has_object_permission(self, request, view, obj):
        from apps.users.domain.services.user_authority import can_view
        return can_view(request.user, obj)


class CanCreateUsers(permissions.BasePermission):
    """
    Check if user can create new users.
    
    Rules:
    - Any authenticated user can create users (self-registration)
    """
    
    def has_permission(self, request, view):
        from apps.users.domain.services.user_authority import can_create
        return (
            request.user 
            and request.user.is_authenticated 
            and can_create(request.user)
        )


class CanEditUser(permissions.BasePermission):
    """
    Check if user can edit another user's profile.
    
    Rules:
    - SUPERADMIN: can edit any user
    - MANAGER: can edit any user except SUPERADMIN
    - IT_ADMIN: can ONLY edit TECHNICIAN users
    - TECHNICIAN: can only edit own profile
    - VIEWER: cannot edit any profile
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.users.domain.services.user_authority import can_edit
        return can_edit(request.user, obj)


class CanChangeUserRole(permissions.BasePermission):
    """
    Check if user can change another user's role.
    
    Rules:
    - Cannot change own role
    - Cannot assign role >= own role (prevents privilege escalation)
    - SUPERADMIN: can assign any role
    - MANAGER: can assign IT_ADMIN, TECHNICIAN, VIEWER
    - IT_ADMIN: can assign TECHNICIAN, VIEWER only
    - TECHNICIAN, VIEWER: cannot change roles
    """
    
    def has_permission(self, request, view):
        from apps.users.domain.services.user_authority import can_change_role
        # For list views, we need to check per-target, so just allow
        # the permission check to proceed and let the view handle it
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('SUPERADMIN', 'MANAGER', 'IT_ADMIN')
        )
    
    def has_object_permission(self, request, view, obj):
        from apps.users.domain.services.user_authority import can_change_role
        return can_change_role(request.user, obj, obj.role)


class CanDeactivateUser(permissions.BasePermission):
    """
    Check if user can deactivate another user's account.
    
    Rules:
    - Cannot deactivate self
    - SUPERADMIN: can deactivate any user except self
    - MANAGER: can deactivate IT_ADMIN and below
    - IT_ADMIN: can deactivate TECHNICIAN, VIEWER only
    - TECHNICIAN, VIEWER: cannot deactivate users
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.users.domain.services.user_authority import can_deactivate
        return can_deactivate(request.user, obj)


class CanActivateUser(permissions.BasePermission):
    """
    Check if user can activate another user's account.
    
    Same rules as can_deactivate.
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.users.domain.services.user_authority import can_activate
        return can_activate(request.user, obj)


class CanDeleteUser(permissions.BasePermission):
    """
    Check if user can delete another user's account.
    
    Rules:
    - Cannot delete self
    - Only SUPERADMIN can delete other users
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.users.domain.services.user_authority import can_delete
        return can_delete(request.user, obj)


# =============================================================================
# Legacy permissions (for backward compatibility)
# =============================================================================

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit.
    Read access for all authenticated users.
    
    This is kept for backward compatibility - prefer using specific permissions.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return request.user and request.user.is_authenticated and request.user.is_admin
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_authenticated and request.user.is_admin


class IsManagerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow managers and above to edit.
    Read access for all authenticated users.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return request.user and request.user.is_authenticated and request.user.is_manager
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_authenticated and request.user.is_manager


class IsTechnicianOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow technicians and above to edit.
    Read access for all authenticated users.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return request.user and request.user.is_authenticated and request.user.is_technician
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user and request.user.is_authenticated and request.user.is_technician


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners or admins to edit.
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.users.domain.services.user_authority import can_edit
        
        # Admin can do anything
        if request.user.is_admin:
            return True
        
        # Check using domain authority
        return can_edit(request.user, obj)


class IsSelfOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow users to edit their own data or admins.
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.users.domain.services.user_authority import can_edit
        
        # Admin can do anything
        if request.user.is_admin:
            return True
        
        # Check using domain authority
        if isinstance(obj, User):
            return can_edit(request.user, obj)
        
        return False


class CanManageUsers(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage other users.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('SUPERADMIN', 'MANAGER', 'IT_ADMIN')
        )


class CanViewLogs(permissions.BasePermission):
    """
    Custom permission to only allow users who can view audit logs.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('MANAGER', 'IT_ADMIN', 'SUPERADMIN')
        )


class CanManageAssets(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage assets.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('TECHNICIAN', 'MANAGER', 'IT_ADMIN', 'SUPERADMIN')
        )


class CanManageProjects(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage projects.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('MANAGER', 'SUPERADMIN')
        )


class CanManageTickets(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage tickets.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role != 'VIEWER'
        )


class CanChangeUserRoleLegacy(permissions.BasePermission):
    """
    Allows changing another user's role.
    SUPERADMIN only.
    
    This is kept for backward compatibility.
    """
    
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'SUPERADMIN'
        )
    
    def has_object_permission(self, request, view, obj):
        from apps.users.domain.services.user_authority import can_change_role
        return can_change_role(request.user, obj, obj.role)

