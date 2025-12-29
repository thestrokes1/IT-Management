"""
Django admin configuration for logs app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    LogCategory, ActivityLog, AuditLog, SystemLog, SecurityEvent,
    LogAlert, LogAlertTrigger, LogReport, LogRetention, LogStatistics
)

@admin.register(LogCategory)
class LogCategoryAdmin(admin.ModelAdmin):
    """Admin interface for LogCategory model."""
    list_display = ['name', 'color_display', 'is_active', 'retention_days', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def color_display(self, obj):
        return format_html(
            '<span style="color: {};">●</span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'color')
        }),
        ('Settings', {
            'fields': ('is_active', 'retention_days')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Admin interface for ActivityLog model."""
    list_display = ['user', 'action', 'level', 'title', 'timestamp']
    list_filter = ['action', 'level', 'category', 'timestamp']
    search_fields = ['title', 'description', 'user__username', 'model_name']
    readonly_fields = ['log_id', 'timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('log_id', 'user', 'action', 'level', 'category')
        }),
        ('Activity Details', {
            'fields': ('title', 'description', 'model_name', 'object_id', 'object_repr')
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent', 'request_path', 'request_method', 'response_status')
        }),
        ('Session Information', {
            'fields': ('session_key', 'session_data'),
            'classes': ('collapse',)
        }),
        ('Additional Context', {
            'fields': ('extra_data', 'tags')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model."""
    list_display = ['user', 'action', 'risk_level', 'model_name', 'object_id', 'timestamp']
    list_filter = ['action', 'risk_level', 'approval_status', 'timestamp']
    search_fields = ['user__username', 'model_name', 'object_repr', 'changes_summary']
    readonly_fields = ['audit_id', 'timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('audit_id', 'user', 'action', 'risk_level')
        }),
        ('Object Information', {
            'fields': ('model_name', 'object_id', 'object_repr')
        }),
        ('Change Tracking', {
            'fields': ('field_name', 'old_value', 'new_value', 'changes_summary')
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent', 'session_key')
        }),
        ('Approval Workflow', {
            'fields': ('reason', 'approval_status', 'approved_by', 'approved_at')
        }),
        ('Additional Context', {
            'fields': ('extra_data',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )

@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    """Admin interface for SystemLog model."""
    list_display = ['level', 'component', 'title', 'error_code', 'timestamp']
    list_filter = ['level', 'component', 'server_name', 'timestamp']
    search_fields = ['title', 'message', 'error_code', 'error_type']
    readonly_fields = ['log_id', 'timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('log_id', 'level', 'component', 'title', 'message')
        }),
        ('Error Details', {
            'fields': ('error_code', 'error_type', 'traceback'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('process_id', 'thread_id', 'server_name')
        }),
        ('Performance Metrics', {
            'fields': ('execution_time', 'memory_usage'),
            'classes': ('collapse',)
        }),
        ('Additional Context', {
            'fields': ('extra_data',)
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )

@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """Admin interface for SecurityEvent model."""
    list_display = ['event_type', 'severity', 'status', 'title', 'affected_user', 'detected_at']
    list_filter = ['event_type', 'severity', 'status', 'detected_at']
    search_fields = ['title', 'description', 'affected_user__username']
    readonly_fields = ['event_id', 'detected_at']
    date_hierarchy = 'detected_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('event_id', 'event_type', 'severity', 'status')
        }),
        ('Event Details', {
            'fields': ('title', 'description')
        }),
        ('User Information', {
            'fields': ('affected_user', 'source_ip', 'target_ip')
        }),
        ('Request Information', {
            'fields': ('user_agent', 'request_path', 'request_method')
        }),
        ('Incident Response', {
            'fields': ('assigned_to', 'resolution_notes', 'false_positive_reason')
        }),
        ('Additional Context', {
            'fields': ('extra_data',)
        }),
        ('Timestamps', {
            'fields': ('detected_at', 'resolved_at')
        }),
    )

@admin.register(LogAlert)
class LogAlertAdmin(admin.ModelAdmin):
    """Admin interface for LogAlert model."""
    list_display = ['name', 'severity', 'status', 'log_type', 'created_by', 'last_triggered']
    list_filter = ['severity', 'status', 'log_type', 'notify_email', 'notify_sms']
    search_fields = ['name', 'description']
    readonly_fields = ['alert_id', 'created_at', 'updated_at', 'last_triggered', 'trigger_count']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('alert_id', 'name', 'description', 'severity', 'status')
        }),
        ('Alert Conditions', {
            'fields': ('log_type', 'conditions', 'threshold_count', 'time_window_minutes')
        }),
        ('Notification Settings', {
            'fields': ('notify_email', 'notify_sms', 'notify_webhook', 'email_recipients', 'webhook_url')
        }),
        ('Alert Management', {
            'fields': ('created_by', 'last_triggered', 'trigger_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(LogAlertTrigger)
class LogAlertTriggerAdmin(admin.ModelAdmin):
    """Admin interface for LogAlertTrigger model."""
    list_display = ['alert', 'triggered_at', 'matching_logs_count', 'acknowledged_by']
    list_filter = ['triggered_at', 'email_sent', 'sms_sent', 'webhook_sent']
    search_fields = ['alert__name', 'resolution_notes']
    readonly_fields = ['trigger_id', 'triggered_at']
    date_hierarchy = 'triggered_at'
    
    fieldsets = (
        ('Trigger Information', {
            'fields': ('trigger_id', 'alert', 'triggered_at', 'matching_logs_count')
        }),
        ('Sample Data', {
            'fields': ('matching_logs_sample',),
            'classes': ('collapse',)
        }),
        ('Notification Status', {
            'fields': ('email_sent', 'sms_sent', 'webhook_sent')
        }),
        ('Resolution', {
            'fields': ('acknowledged_by', 'acknowledged_at', 'resolution_notes')
        }),
    )

@admin.register(LogReport)
class LogReportAdmin(admin.ModelAdmin):
    """Admin interface for LogReport model."""
    list_display = ['name', 'report_type', 'format', 'created_by', 'is_scheduled', 'usage_count']
    list_filter = ['report_type', 'format', 'is_scheduled', 'schedule_frequency']
    search_fields = ['name', 'description']
    readonly_fields = ['report_id', 'created_at', 'updated_at', 'usage_count', 'generated_reports']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('report_id', 'name', 'description', 'report_type', 'format')
        }),
        ('Configuration', {
            'fields': ('parameters', 'filters', 'date_range_days')
        }),
        ('Scheduling', {
            'fields': ('is_scheduled', 'schedule_frequency', 'schedule_time')
        }),
        ('Report Metadata', {
            'fields': ('created_by', 'is_public', 'usage_count')
        }),
        ('Generated Reports', {
            'fields': ('generated_reports',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(LogRetention)
class LogRetentionAdmin(admin.ModelAdmin):
    """Admin interface for LogRetention model."""
    list_display = ['name', 'log_type', 'retention_days', 'is_active', 'last_run']
    list_filter = ['log_type', 'is_active', 'compress_archives', 'encrypt_archives']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'last_run']
    
    fieldsets = (
        ('Policy Information', {
            'fields': ('name', 'description')
        }),
        ('Retention Settings', {
            'fields': ('log_type', 'retention_days', 'archive_after_days', 'delete_after_archive_days')
        }),
        ('Policy Status', {
            'fields': ('is_active', 'last_run')
        }),
        ('Additional Settings', {
            'fields': ('compress_archives', 'encrypt_archives')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(LogStatistics)
class LogStatisticsAdmin(admin.ModelAdmin):
    """Admin interface for LogStatistics model."""
    list_display = ['date', 'total_activity_logs', 'total_audit_logs', 'total_system_logs', 'total_security_events']
    list_filter = ['date']
    readonly_fields = ['calculated_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Statistics Date', {
            'fields': ('date',)
        }),
        ('Activity Log Statistics', {
            'fields': ('total_activity_logs', 'activity_logs_by_level', 'activity_logs_by_action', 'unique_users_active')
        }),
        ('Audit Log Statistics', {
            'fields': ('total_audit_logs', 'audit_logs_by_action', 'audit_logs_by_risk')
        }),
        ('System Log Statistics', {
            'fields': ('total_system_logs', 'system_logs_by_level', 'system_logs_by_component')
        }),
        ('Security Event Statistics', {
            'fields': ('total_security_events', 'security_events_by_severity', 'security_events_by_type')
        }),
        ('Performance Metrics', {
            'fields': ('average_log_size', 'total_log_size')
        }),
        ('Calculation Info', {
            'fields': ('calculated_at',)
        }),
    )

