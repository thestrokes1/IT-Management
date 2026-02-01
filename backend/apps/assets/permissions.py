"""
Permissions classes for Assets Management.

Role-based access control for asset operations.
All permission checks are enforced server-side using domain authority services.

IMPORTANT: All permission checks MUST use the domain authority services
to ensure consistent enforcement across all entry points (API, views, etc.).
"""

from rest_framework import permissions
from apps.assets.models import Asset


class CanViewAssets(permissions.BasePermission):
    """
    Check if user can view assets.
    
    Rules:
    - VIEWER: NOT allowed
    - All other roles: allowed
    """
    
    def has_permission(self, request, view):
        from apps.assets.domain.services.asset_authority import can_view_list
        return (
            request.user 
            and request.user.is_authenticated 
            and can_view_list(request.user)
        )
    
    def has_object_permission(self, request, view, obj):
        from apps.assets.domain.services.asset_authority import can_view
        return can_view(request.user, obj)


class CanCreateAssets(permissions.BasePermission):
    """
    Check if user can create assets.
    
    Rules:
    - VIEWER: NOT allowed
    - TECHNICIAN and above: allowed
    """
    
    def has_permission(self, request, view):
        from apps.assets.domain.services.asset_authority import can_create
        return (
            request.user 
            and request.user.is_authenticated 
            and can_create(request.user)
        )


class CanEditAsset(permissions.BasePermission):
    """
    Check if user can edit an asset.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: only if assigned_to == user
    - VIEWER: NOT allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.assets.domain.services.asset_authority import can_edit
        return can_edit(request.user, obj)


class CanDeleteAsset(permissions.BasePermission):
    """
    Check if user can delete an asset.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: only if assigned_to == user
    - VIEWER: NOT allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.assets.domain.services.asset_authority import can_delete
        return can_delete(request.user, obj)


class CanAssignAsset(permissions.BasePermission):
    """
    Check if user can assign an asset to a user.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: NEVER allowed
    - VIEWER: NOT allowed
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            'SUPERADMIN', 'MANAGER', 'IT_ADMIN'
        )
    
    def has_object_permission(self, request, view, obj):
        from apps.assets.domain.services.asset_authority import can_assign
        return can_assign(request.user, obj, None)


class CanUnassignAsset(permissions.BasePermission):
    """
    Check if user can unassign an asset.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: NEVER allowed
    - VIEWER: NOT allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.assets.domain.services.asset_authority import can_unassign
        return can_unassign(request.user, obj)


class CanSelfAssignAsset(permissions.BasePermission):
    """
    Check if user can self-assign an asset.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: only if unassigned
    - VIEWER: NOT allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.assets.domain.services.asset_authority import can_self_assign
        return can_self_assign(request.user, obj)


class CanViewAssetLogs(permissions.BasePermission):
    """
    Check if user can view asset logs/history.
    
    Rules:
    - IT_ADMIN and above: always allowed
    - TECHNICIAN, VIEWER: NOT allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.assets.domain.services.asset_authority import can_view_logs
        return can_view_logs(request.user, obj)


class CanAddAssetMaintenance(permissions.BasePermission):
    """
    Check if user can add maintenance records.
    
    Rules:
    - VIEWER: NOT allowed
    - TECHNICIAN: only if assigned_to == user
    - IT_ADMIN and above: allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.assets.domain.services.asset_authority import can_add_maintenance
        return can_add_maintenance(request.user, obj)


class CanViewAssetMaintenance(permissions.BasePermission):
    """
    Check if user can view maintenance records.
    
    Rules:
    - VIEWER: NOT allowed
    - TECHNICIAN: only if assigned_to == user
    - IT_ADMIN and above: allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.assets.domain.services.asset_authority import can_view_maintenance
        return can_view_maintenance(request.user, obj)


# =============================================================================
# Legacy permissions (for backward compatibility)
# =============================================================================

class CanManageAssets(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage assets.
    """
    
    def has_permission(self, request, view):
        from apps.assets.domain.services.asset_authority import can_create
        return (
            request.user 
            and request.user.is_authenticated 
            and can_create(request.user)
        )


class IsAssetOwnerOrReadOnly(permissions.BasePermission):
    """
    Asset object-level permission: allows asset owner or users with management permission.
    
    Read permissions: All users who can access assets
    Write permissions: Asset managers or assigned users
    
    This is kept for backward compatibility - prefer using CanEditAsset.
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.assets.domain.services.asset_authority import can_edit, can_view
        
        # Read permissions
        if request.method in permissions.SAFE_METHODS:
            return can_view(request.user, obj)
        
        # Write permissions
        return can_edit(request.user, obj)


class CanViewAssetDetails(permissions.BasePermission):
    """
    Check if user can view asset details.
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.assets.domain.services.asset_authority import can_view
        return can_view(request.user, obj)


class CanAssignAssets(permissions.BasePermission):
    """
    Check if user can assign assets.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in (
            'SUPERADMIN', 'MANAGER', 'IT_ADMIN'
        )


class CanViewMaintenanceRecords(permissions.BasePermission):
    """
    Check if user can view maintenance records.
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.assets.domain.services.asset_authority import can_view_maintenance
        return can_view_maintenance(request.user, obj.asset)


class CanManageMaintenance(permissions.BasePermission):
    """
    Check if user can manage maintenance records.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('IT_ADMIN', 'MANAGER', 'SUPERADMIN')
        )


class CanViewAssetAuditLogs(permissions.BasePermission):
    """
    Check if user can view asset audit logs.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('IT_ADMIN', 'MANAGER', 'SUPERADMIN')
        )


class CanGenerateAssetReports(permissions.BasePermission):
    """
    Check if user can generate asset reports.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('MANAGER', 'SUPERADMIN')
        )


class CanManageAssetCategories(permissions.BasePermission):
    """
    Check if user can manage asset categories.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('IT_ADMIN', 'MANAGER', 'SUPERADMIN')
        )


class CanApproveAssetRetirement(permissions.BasePermission):
    """
    Check if user can approve asset retirement.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('IT_ADMIN', 'MANAGER', 'SUPERADMIN')
        )


class CanExportAssets(permissions.BasePermission):
    """
    Check if user can export asset data.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('MANAGER', 'SUPERADMIN')
        )


class CanImportAssets(permissions.BasePermission):
    """
    Check if user can import asset data.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('MANAGER', 'SUPERADMIN')
        )


class CanReassignAsset(permissions.BasePermission):
    """
    Check if user can reassign an asset to another user.
    
    Rules:
    - MANAGER / IT_ADMIN / SUPERADMIN: can always reassign
    - TECHNICIAN: CANNOT reassign assets (even their own)
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.assets.domain.services.asset_authority import can_reassign
        return can_reassign(request.user, obj)


class IsAssignedAssetUser(permissions.BasePermission):
    """
    Check if user is the assigned asset user.
    
    Rules:
    - User must be the assigned user
    - ADMIN roles always have access
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.assets.domain.services.asset_authority import can_edit
        return can_edit(request.user, obj)

