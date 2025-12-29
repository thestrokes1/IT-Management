"""
Permissions classes for Assets Management.
Role-based access control for asset operations.
"""

from rest_framework import permissions
from apps.assets.models import Asset

class CanManageAssets(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage assets.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_manage_assets

class IsAssetOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow asset owners or those with asset management rights.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for all authenticated users who can view assets
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated and request.user.can_manage_assets
        
        # Write permissions for asset managers or asset owners
        if request.user.is_admin:
            return True
        
        # Check if user can manage assets
        if request.user.can_manage_assets:
            return True
        
        # Asset owners can update their assigned assets
        if hasattr(obj, 'assigned_to') and obj.assigned_to == request.user:
            return True
        
        return False

class CanViewAssetDetails(permissions.BasePermission):
    """
    Custom permission to check if user can view asset details.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can view all
        if request.user.is_admin:
            return True
        
        # Asset managers can view all
        if request.user.can_manage_assets:
            return True
        
        # Users can view assets assigned to them
        if hasattr(obj, 'assigned_to') and obj.assigned_to == request.user:
            return True
        
        # Users can view assets they created
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        return False

class CanAssignAssets(permissions.BasePermission):
    """
    Custom permission to only allow users who can assign assets.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_manager

class CanViewMaintenanceRecords(permissions.BasePermission):
    """
    Custom permission to check if user can view maintenance records.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can view all
        if request.user.is_admin:
            return True
        
        # Asset managers can view all
        if request.user.can_manage_assets:
            return True
        
        # Users can view maintenance for their assigned assets
        if hasattr(obj, 'asset') and hasattr(obj.asset, 'assigned_to'):
            if obj.asset.assigned_to == request.user:
                return True
        
        return False

class CanManageMaintenance(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage maintenance records.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_technician

class CanViewAuditLogs(permissions.BasePermission):
    """
    Custom permission to only allow users who can view asset audit logs.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_view_logs

class CanGenerateReports(permissions.BasePermission):
    """
    Custom permission to only allow users who can generate asset reports.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_manager

class CanManageCategories(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage asset categories.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin

class CanApproveRetirement(permissions.BasePermission):
    """
    Custom permission to only allow users who can approve asset retirement.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin
