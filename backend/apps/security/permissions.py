"""
Security permissions for IT Management Platform.
Defines permission classes for security-related operations.
"""

from rest_framework import permissions
from django.contrib.auth.models import User, Group


class IsSecurityAdminOrReadOnly(permissions.BasePermission):
    """
    Permission that allows only security administrators to modify security data.
    Read access is allowed for authenticated users.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to perform the action."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read access for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write access only for security admins
        return self._is_security_admin(request.user)
    
    def _is_security_admin(self, user):
        """Check if user is a security administrator."""
        if user.is_superuser:
            return True
        
        # Check if user is in security admin group
        return user.groups.filter(name='Security_Admin').exists()


class IsSecurityAnalystOrReadOnly(permissions.BasePermission):
    """
    Permission that allows security analysts and admins to modify security data.
    Read access is allowed for authenticated users.
    """
    
    def has_permission(self, request, view):
        """Check if user has permission to perform the action."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Read access for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write access for security analysts and admins
        return self._is_security_analyst_or_admin(request.user)
    
    def _is_security_analyst_or_admin(self, user):
        """Check if user is a security analyst or administrator."""
        if user.is_superuser:
            return True
        
        # Check if user is in security admin or analyst group
        return user.groups.filter(name__in=['Security_Admin', 'Security_Analyst']).exists()


class CanViewSecurityData(permissions.BasePermission):
    """
    Permission that allows viewing security data based on user roles.
    """
    
    def has_permission(self, request, view):
        """Check if user can view security data."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return self._can_view_security_data(request.user)
    
    def _can_view_security_data(self, user):
        """Check if user can view security data."""
        if user.is_superuser:
            return True
        
        # Check if user is in security-related groups
        security_groups = [
            'Security_Admin', 'Security_Analyst', 'IT_Admin', 'Manager'
        ]
        return user.groups.filter(name__in=security_groups).exists()


class CanManageSecurityIncidents(permissions.BasePermission):
    """
    Permission that allows managing security incidents.
    """
    
    def has_permission(self, request, view):
        """Check if user can manage security incidents."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow incident creation for all authenticated users (security awareness)
        if request.method == 'POST':
            return True
        
        # Allow read access for authorized users
        if request.method in permissions.SAFE_METHODS:
            return self._can_view_security_data(request.user)
        
        # Modify access only for security staff
        return self._is_security_analyst_or_admin(request.user)
    
    def _can_view_security_data(self, user):
        """Check if user can view security data."""
        if user.is_superuser:
            return True
        
        # Check if user is in security-related groups
        security_groups = [
            'Security_Admin', 'Security_Analyst', 'IT_Admin', 'Manager'
        ]
        return user.groups.filter(name__in=security_groups).exists()
    
    def _is_security_analyst_or_admin(self, user):
        """Check if user is a security analyst or administrator."""
        if user.is_superuser:
            return True
        
        # Check if user is in security admin or analyst group
        return user.groups.filter(name__in=['Security_Admin', 'Security_Analyst']).exists()


class CanAccessSecurityLogs(permissions.BasePermission):
    """
    Permission that controls access to security logs and audit trails.
    """
    
    def has_permission(self, request, view):
        """Check if user can access security logs."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            # Read access for authorized users
            return self._can_view_security_data(request.user)
        
        # No write access to logs (they should be immutable)
        return False
    
    def _can_view_security_data(self, user):
        """Check if user can view security data."""
        if user.is_superuser:
            return True
        
        # Check if user is in security-related groups
        security_groups = [
            'Security_Admin', 'Security_Analyst', 'IT_Admin', 'Manager'
        ]
        return user.groups.filter(name__in=security_groups).exists()


class CanManageSecurityPolicies(permissions.BasePermission):
    """
    Permission that controls management of security policies.
    """
    
    def has_permission(self, request, view):
        """Check if user can manage security policies."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Only security administrators can modify policies
        return self._is_security_admin(request.user)
    
    def _is_security_admin(self, user):
        """Check if user is a security administrator."""
        if user.is_superuser:
            return True
        
        # Check if user is in security admin group
        return user.groups.filter(name='Security_Admin').exists()


class CanViewOwnSecurityData(permissions.BasePermission):
    """
    Permission that allows users to view their own security-related data.
    """
    
    def has_permission(self, request, view):
        """Check if user can view their own security data."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Users can view their own security events and audit logs
        return True
    
    def has_object_permission(self, request, view, obj):
        """Check if user can view specific object."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers can view everything
        if request.user.is_superuser:
            return True
        
        # Users can view their own security events
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Users can view their own audit logs
        if hasattr(obj, 'username'):
            return obj.username == request.user.username
        
        return False


class CanAccessSecurityDashboard(permissions.BasePermission):
    """
    Permission that controls access to security dashboards.
    """
    
    def has_permission(self, request, view):
        """Check if user can access security dashboards."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has access to security data
        return self._can_view_security_data(request.user)
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access specific dashboard."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Check if dashboard is public
        if obj.is_public:
            return True
        
        # Check if user is allowed to access this dashboard
        return obj.allowed_users.filter(id=request.user.id).exists()
    
    def _can_view_security_data(self, user):
        """Check if user can view security data."""
        if user.is_superuser:
            return True
        
        # Check if user is in security-related groups
        security_groups = [
            'Security_Admin', 'Security_Analyst', 'IT_Admin', 'Manager'
        ]
        return user.groups.filter(name__in=security_groups).exists()


class CanPerformSecurityActions(permissions.BasePermission):
    """
    Permission that controls performing security actions like resolving events.
    """
    
    def has_permission(self, request, view):
        """Check if user can perform security actions."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Security analysts and admins can perform actions
        return self._is_security_analyst_or_admin(request.user)
    
    def _is_security_analyst_or_admin(self, user):
        """Check if user is a security analyst or administrator."""
        if user.is_superuser:
            return True
        
        # Check if user is in security admin or analyst group
        return user.groups.filter(name__in=['Security_Admin', 'Security_Analyst']).exists()


class CanViewSecurityStatistics(permissions.BasePermission):
    """
    Permission that controls access to security statistics and metrics.
    """
    
    def has_permission(self, request, view):
        """Check if user can view security statistics."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow access to security statistics for authorized users
        return self._can_view_security_data(request.user)
    
    def _can_view_security_data(self, user):
        """Check if user can view security data."""
        if user.is_superuser:
            return True
        
        # Check if user is in security-related groups
        security_groups = [
            'Security_Admin', 'Security_Analyst', 'IT_Admin', 'Manager'
        ]
        return user.groups.filter(name__in=security_groups).exists()


class CanManageSecurityThresholds(permissions.BasePermission):
    """
    Permission that controls management of security thresholds.
    """
    
    def has_permission(self, request, view):
        """Check if user can manage security thresholds."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Only security administrators can modify thresholds
        return self._is_security_admin(request.user)
    
    def _is_security_admin(self, user):
        """Check if user is a security administrator."""
        if user.is_superuser:
            return True
        
        # Check if user is in security admin group
        return user.groups.filter(name='Security_Admin').exists()


class IsOwnerOrSecurityStaff(permissions.BasePermission):
    """
    Permission that allows users to access their own data or security staff to access all data.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can access the object."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers can access everything
        if request.user.is_superuser:
            return True
        
        # Security staff can access everything
        if self._is_security_staff(request.user):
            return True
        
        # Users can access their own data
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        if hasattr(obj, 'username'):
            return obj.username == request.user.username
        
        return False
    
    def _is_security_staff(self, user):
        """Check if user is security staff."""
        security_groups = ['Security_Admin', 'Security_Analyst']
        return user.groups.filter(name__in=security_groups).exists()


class SecurityObjectLevelPermissions(permissions.BasePermission):
    """
    Object-level permissions for security data.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check object-level permissions."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Read permissions for security data
        if request.method in permissions.SAFE_METHODS:
            return self._can_view_security_data(request.user)
        
        # Write permissions for security staff only
        return self._is_security_staff(request.user)
    
    def _can_view_security_data(self, user):
        """Check if user can view security data."""
        # Check if user is in security-related groups
        security_groups = [
            'Security_Admin', 'Security_Analyst', 'IT_Admin', 'Manager'
        ]
        return user.groups.filter(name__in=security_groups).exists()
    
    def _is_security_staff(self, user):
        """Check if user is security staff."""
        security_groups = ['Security_Admin', 'Security_Analyst']
        return user.groups.filter(name__in=security_groups).exists()

