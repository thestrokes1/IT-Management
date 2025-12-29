"""
Permissions classes for Logs Management.
Role-based access control for logging and audit operations.
"""

from rest_framework import permissions
from apps.logs.models import ActivityLog, AuditLog, SystemLog, SecurityEvent, LogAlert

class CanViewLogs(permissions.BasePermission):
    """
    Custom permission to only allow users who can view logs.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_view_logs

class CanViewAuditLogs(permissions.BasePermission):
    """
    Custom permission to only allow users who can view audit logs.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_view_audit_logs

class CanViewSecurityEvents(permissions.BasePermission):
    """
    Custom permission to only allow users who can view security events.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_view_security_events

class CanManageLogAlerts(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage log alerts.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.can_manage_logs
        )

class CanViewLogAlerts(permissions.BasePermission):
    """
    Custom permission to only allow users who can view log alerts.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_view_logs or request.user.can_manage_logs
        )

class CanManageLogReports(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage log reports.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.can_manage_logs
        )

class CanViewLogReports(permissions.BasePermission):
    """
    Custom permission to only allow users who can view log reports.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_view_logs or request.user.can_manage_logs
        )

class CanGenerateLogReports(permissions.BasePermission):
    """
    Custom permission to only allow users who can generate log reports.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_view_logs or request.user.can_manage_logs
        )

class CanViewSystemLogs(permissions.BasePermission):
    """
    Custom permission to only allow users who can view system logs.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.can_manage_logs
        )

class CanAcknowledgeSecurityEvents(permissions.BasePermission):
    """
    Custom permission to only allow users who can acknowledge security events.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.can_manage_security
        )

class CanResolveSecurityEvents(permissions.BasePermission):
    """
    Custom permission to only allow users who can resolve security events.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.can_manage_security
        )

class CanManageLogRetention(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage log retention policies.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin

class CanViewLogStatistics(permissions.BasePermission):
    """
    Custom permission to only allow users who can view log statistics.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_view_logs or request.user.can_manage_logs
        )

class CanExportLogs(permissions.BasePermission):
    """
    Custom permission to only allow users who can export logs.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_view_logs or request.user.can_manage_logs
        )

class CanCreateCustomLogs(permissions.BasePermission):
    """
    Custom permission to only allow users who can create custom log entries.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_view_logs or request.user.can_manage_logs
        )

class CanViewOwnActivityLogs(permissions.BasePermission):
    """
    Custom permission to allow users to view their own activity logs.
    """
    
    def has_object_permission(self, request, view, obj):
        # Users can view their own activity logs
        return obj.user == request.user

class CanViewSensitiveAuditLogs(permissions.BasePermission):
    """
    Custom permission to only allow users who can view sensitive audit logs.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can view all audit logs
        if request.user.is_admin:
            return True
        
        # Users can view their own audit logs
        if obj.user == request.user:
            return True
        
        # Users with audit log management rights can view sensitive logs
        if request.user.can_view_audit_logs and obj.risk_level in ['LOW', 'MEDIUM']:
            return True
        
        # Only admins can view high/critical risk audit logs
        return obj.risk_level in ['LOW', 'MEDIUM']

class CanViewOwnSecurityEvents(permissions.BasePermission):
    """
    Custom permission to allow users to view security events affecting them.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can view all security events
        if request.user.is_admin:
            return True
        
        # Users can view security events affecting them
        if obj.affected_user == request.user:
            return True
        
        # Security team can view all events
        if request.user.can_manage_security:
            return True
        
        return False

class CanManageLogCategories(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage log categories.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.can_manage_logs
        )

class CanViewLogInsights(permissions.BasePermission):
    """
    Custom permission to only allow users who can view log insights and analytics.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_view_logs or request.user.can_manage_logs
        )

class CanAccessLogDashboard(permissions.BasePermission):
    """
    Custom permission to only allow users who can access the log dashboard.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_view_logs or request.user.can_manage_logs or request.user.can_view_security_events
        )

class CanTriggerLogAlerts(permissions.BasePermission):
    """
    Custom permission for system processes to trigger log alerts.
    """
    
    def has_permission(self, request, view):
        # Allow system processes (no user) to trigger alerts
        return True

class CanViewLogFilters(permissions.BasePermission):
    """
    Custom permission to only allow users who can use advanced log filters.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_view_logs or request.user.can_manage_logs
        )
