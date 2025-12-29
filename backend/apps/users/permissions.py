"""
Permissions classes for IT Management Platform.
Role-based access control implementation.
"""

from rest_framework import permissions
from apps.users.models import User

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit.
    Read access for all authenticated users.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
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

class IsTechnicianOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow technicians and above to edit.
    Read access for all authenticated users.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        return request.user and request.user.is_authenticated and request.user.is_technician

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners or admins to edit.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user.is_admin:
            return True
        
        # Users can only edit their own profile
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object has created_by field
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False

class IsSelfOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow users to edit their own data or admins.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user.is_admin:
            return True
        
        # Users can only access their own data
        if isinstance(obj, User):
            return obj == request.user
        
        return False

class CanManageUsers(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage other users.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_manage_users

class CanViewLogs(permissions.BasePermission):
    """
    Custom permission to only allow users who can view audit logs.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_view_logs

class CanManageAssets(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage assets.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_manage_assets

class CanManageProjects(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage projects.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_manage_projects

class CanManageTickets(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage tickets.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_manage_tickets
