"""
Permissions classes for Logs Management.
Role-based access control for logging and audit operations.

Uses User model properties for consistent permission checking:
- can_view_logs: SUPERADMIN, MANAGER
- can_view_audit_logs: SUPERADMIN, MANAGER
- can_manage_security: SUPERADMIN, IT_ADMIN
- is_admin: SUPERADMIN, IT_ADMIN
"""

from rest_framework import permissions


class CanViewLogs(permissions.BasePermission):
    """Check if user can view logs (SUPERADMIN, MANAGER)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_view_logs', False)
        )


class CanViewAuditLogs(permissions.BasePermission):
    """Check if user can view audit logs (SUPERADMIN, MANAGER)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_view_audit_logs', False)
        )


class CanViewSecurityEvents(permissions.BasePermission):
    """Check if user can view security events (SUPERADMIN, IT_ADMIN)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_manage_security', False)
        )


class CanManageLogAlerts(permissions.BasePermission):
    """Check if user can manage log alerts (SUPERADMIN, IT_ADMIN, MANAGER)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'is_admin', False)
                or getattr(request.user, 'can_view_logs', False)
            )
        )


class CanViewLogAlerts(permissions.BasePermission):
    """Check if user can view log alerts (SUPERADMIN, IT_ADMIN, MANAGER)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_view_logs', False)
        )


class CanManageLogReports(permissions.BasePermission):
    """Check if user can manage log reports (SUPERADMIN, IT_ADMIN, MANAGER)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'is_admin', False)
                or getattr(request.user, 'can_view_logs', False)
            )
        )


class CanViewLogReports(permissions.BasePermission):
    """Check if user can view log reports (SUPERADMIN, IT_ADMIN, MANAGER)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_view_logs', False)
        )


class CanGenerateLogReports(permissions.BasePermission):
    """Check if user can generate log reports (SUPERADMIN, IT_ADMIN, MANAGER)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_view_logs', False)
        )


class CanViewSystemLogs(permissions.BasePermission):
    """Check if user can view system logs (SUPERADMIN, IT_ADMIN)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'is_admin', False)
        )


class CanAcknowledgeSecurityEvents(permissions.BasePermission):
    """Check if user can acknowledge security events (SUPERADMIN, IT_ADMIN)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_manage_security', False)
        )


class CanResolveSecurityEvents(permissions.BasePermission):
    """Check if user can resolve security events (SUPERADMIN, IT_ADMIN)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_manage_security', False)
        )


class CanManageLogRetention(permissions.BasePermission):
    """Check if user can manage log retention (SUPERADMIN only)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_manage_settings', False)
        )


class CanViewLogStatistics(permissions.BasePermission):
    """Check if user can view log statistics (SUPERADMIN, IT_ADMIN, MANAGER)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_view_logs', False)
        )


class CanExportLogs(permissions.BasePermission):
    """Check if user can export logs (SUPERADMIN, IT_ADMIN, MANAGER)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_export_data', False)
        )


class CanCreateCustomLogs(permissions.BasePermission):
    """Check if user can create custom logs (SUPERADMIN, IT_ADMIN, MANAGER)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_view_logs', False)
        )


class CanViewOwnActivityLogs(permissions.BasePermission):
    """Users can view their own activity logs"""
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class CanViewSensitiveAuditLogs(permissions.BasePermission):
    """Check if user can view sensitive audit logs"""
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, 'is_admin', False):
            return True
        if obj.user == request.user:
            return True
        if (
            getattr(request.user, 'can_view_audit_logs', False)
            and obj.risk_level in ['LOW', 'MEDIUM']
        ):
            return True
        return False


class CanViewOwnSecurityEvents(permissions.BasePermission):
    """Users can view their own security events"""
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, 'is_admin', False):
            return True
        if obj.affected_user == request.user:
            return True
        if getattr(request.user, 'can_manage_security', False):
            return True
        return False


class CanManageLogCategories(permissions.BasePermission):
    """Check if user can manage log categories (SUPERADMIN, IT_ADMIN)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'is_admin', False)
        )


class CanViewLogInsights(permissions.BasePermission):
    """Check if user can view log insights (SUPERADMIN, IT_ADMIN, MANAGER)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_view_logs', False)
        )


class CanAccessLogDashboard(permissions.BasePermission):
    """Check if user can access log dashboard (SUPERADMIN, IT_ADMIN, MANAGER)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_view_logs', False)
        )


class CanTriggerLogAlerts(permissions.BasePermission):
    """Check if user can trigger log alerts - all authenticated users"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class CanViewLogFilters(permissions.BasePermission):
    """Check if user can view log filters (SUPERADMIN, IT_ADMIN, MANAGER)"""
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_view_logs', False)
        )
