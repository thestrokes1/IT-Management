"""
Permissions classes for Logs Management.
Role-based access control for logging and audit operations.
"""

from rest_framework import permissions


class CanViewLogs(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_view_logs', False)
        )


class CanViewAuditLogs(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_view_audit_logs', False)
        )


class CanViewSecurityEvents(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'can_view_security_events', False)
        )


class CanManageLogAlerts(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'is_admin', False)
                or getattr(request.user, 'can_manage_logs', False)
            )
        )


class CanViewLogAlerts(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'can_view_logs', False)
                or getattr(request.user, 'can_manage_logs', False)
            )
        )


class CanManageLogReports(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'is_admin', False)
                or getattr(request.user, 'can_manage_logs', False)
            )
        )


class CanViewLogReports(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'can_view_logs', False)
                or getattr(request.user, 'can_manage_logs', False)
            )
        )


class CanGenerateLogReports(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'can_view_logs', False)
                or getattr(request.user, 'can_manage_logs', False)
            )
        )


class CanViewSystemLogs(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'is_admin', False)
                or getattr(request.user, 'can_manage_logs', False)
            )
        )


class CanAcknowledgeSecurityEvents(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'is_admin', False)
                or getattr(request.user, 'can_manage_security', False)
            )
        )


class CanResolveSecurityEvents(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'is_admin', False)
                or getattr(request.user, 'can_manage_security', False)
            )
        )


class CanManageLogRetention(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'is_admin', False)
        )


class CanViewLogStatistics(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'can_view_logs', False)
                or getattr(request.user, 'can_manage_logs', False)
            )
        )


class CanExportLogs(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'can_view_logs', False)
                or getattr(request.user, 'can_manage_logs', False)
            )
        )


class CanCreateCustomLogs(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'can_view_logs', False)
                or getattr(request.user, 'can_manage_logs', False)
            )
        )


class CanViewOwnActivityLogs(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class CanViewSensitiveAuditLogs(permissions.BasePermission):
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
    def has_object_permission(self, request, view, obj):
        if getattr(request.user, 'is_admin', False):
            return True

        if obj.affected_user == request.user:
            return True

        if getattr(request.user, 'can_manage_security', False):
            return True

        return False


class CanManageLogCategories(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'is_admin', False)
                or getattr(request.user, 'can_manage_logs', False)
            )
        )


class CanViewLogInsights(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'can_view_logs', False)
                or getattr(request.user, 'can_manage_logs', False)
            )
        )


class CanAccessLogDashboard(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'can_view_logs', False)
                or getattr(request.user, 'can_manage_logs', False)
                or getattr(request.user, 'can_view_security_events', False)
            )
        )


class CanTriggerLogAlerts(permissions.BasePermission):
    def has_permission(self, request, view):
        return True


class CanViewLogFilters(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and (
                getattr(request.user, 'can_view_logs', False)
                or getattr(request.user, 'can_manage_logs', False)
            )
        )
