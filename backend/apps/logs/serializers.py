"""
Log serializers for IT Management Platform.
Handles serialization and validation for log operations.
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta

from apps.logs.models import (
    LogCategory, ActivityLog, AuditLog, SystemLog, SecurityEvent,
    LogAlert, LogAlertTrigger, LogReport, LogRetention, LogStatistics
)
from apps.users.models import User

class LogCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for log categories.
    """
    class Meta:
        model = LogCategory
        fields = ['id', 'name', 'description', 'color', 'is_active', 'retention_days', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ActivityLogSerializer(serializers.ModelSerializer):
    """
    Serializer for activity logs.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'log_id', 'user', 'user_username', 'user_full_name',
            'action', 'level', 'category', 'category_name', 'title',
            'description', 'model_name', 'object_id', 'object_repr',
            'ip_address', 'user_agent', 'request_path', 'request_method',
            'response_status', 'session_key', 'session_data', 'extra_data',
            'tags', 'timestamp'
        ]
        read_only_fields = ['id', 'log_id', 'timestamp']

class ActivityLogListSerializer(serializers.ModelSerializer):
    """
    Serializer for activity log list view.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'log_id', 'user_username', 'action', 'level',
            'category_name', 'title', 'description', 'ip_address',
            'response_status', 'timestamp'
        ]
        read_only_fields = ['id', 'log_id', 'timestamp']

class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for audit logs.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'audit_id', 'user', 'user_username', 'action',
            'risk_level', 'model_name', 'object_id', 'object_repr',
            'field_name', 'old_value', 'new_value', 'changes_summary',
            'ip_address', 'user_agent', 'session_key', 'reason',
            'approval_status', 'approved_by', 'approved_by_username',
            'approved_at', 'extra_data', 'timestamp'
        ]
        read_only_fields = ['id', 'audit_id', 'timestamp']

class AuditLogListSerializer(serializers.ModelSerializer):
    """
    Serializer for audit log list view.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'audit_id', 'user_username', 'action', 'risk_level',
            'model_name', 'object_repr', 'changes_summary', 'timestamp'
        ]
        read_only_fields = ['id', 'audit_id', 'timestamp']

class SystemLogSerializer(serializers.ModelSerializer):
    """
    Serializer for system logs.
    """
    class Meta:
        model = SystemLog
        fields = [
            'id', 'log_id', 'level', 'component', 'title', 'message',
            'error_code', 'error_type', 'traceback', 'process_id',
            'thread_id', 'server_name', 'execution_time', 'memory_usage',
            'extra_data', 'timestamp'
        ]
        read_only_fields = ['id', 'log_id', 'timestamp']

class SystemLogListSerializer(serializers.ModelSerializer):
    """
    Serializer for system log list view.
    """
    class Meta:
        model = SystemLog
        fields = [
            'id', 'log_id', 'level', 'component', 'title', 'message',
            'error_code', 'server_name', 'execution_time', 'timestamp'
        ]
        read_only_fields = ['id', 'log_id', 'timestamp']

class SecurityEventSerializer(serializers.ModelSerializer):
    """
    Serializer for security events.
    """
    affected_user_username = serializers.CharField(source='affected_user.username', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    
    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'event_id', 'event_type', 'severity', 'status',
            'title', 'description', 'affected_user', 'affected_user_username',
            'source_ip', 'target_ip', 'user_agent', 'request_path',
            'request_method', 'assigned_to', 'assigned_to_username',
            'resolution_notes', 'false_positive_reason', 'detected_at',
            'resolved_at', 'extra_data'
        ]
        read_only_fields = ['id', 'event_id', 'detected_at']

class SecurityEventListSerializer(serializers.ModelSerializer):
    """
    Serializer for security event list view.
    """
    affected_user_username = serializers.CharField(source='affected_user.username', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    
    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'event_id', 'event_type', 'severity', 'status',
            'title', 'affected_user_username', 'source_ip', 'assigned_to_username',
            'detected_at', 'resolved_at'
        ]
        read_only_fields = ['id', 'event_id', 'detected_at']

class LogAlertSerializer(serializers.ModelSerializer):
    """
    Serializer for log alerts.
    """
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = LogAlert
        fields = [
            'id', 'alert_id', 'name', 'description', 'severity', 'status',
            'log_type', 'conditions', 'threshold_count', 'time_window_minutes',
            'notify_email', 'notify_sms', 'notify_webhook', 'email_recipients',
            'webhook_url', 'created_by', 'created_by_username', 'last_triggered',
            'trigger_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'alert_id', 'created_by', 'created_by_username', 'last_triggered', 'trigger_count', 'created_at', 'updated_at']

class LogAlertTriggerSerializer(serializers.ModelSerializer):
    """
    Serializer for log alert triggers.
    """
    alert_name = serializers.CharField(source='alert.name', read_only=True)
    acknowledged_by_username = serializers.CharField(source='acknowledged_by.username', read_only=True)
    
    class Meta:
        model = LogAlertTrigger
        fields = [
            'id', 'trigger_id', 'alert', 'alert_name', 'triggered_at',
            'matching_logs_count', 'matching_logs_sample', 'email_sent',
            'sms_sent', 'webhook_sent', 'acknowledged_by', 'acknowledged_by_username',
            'acknowledged_at', 'resolution_notes'
        ]
        read_only_fields = ['id', 'trigger_id', 'triggered_at']

class LogReportSerializer(serializers.ModelSerializer):
    """
    Serializer for log reports.
    """
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = LogReport
        fields = [
            'id', 'report_id', 'name', 'description', 'report_type',
            'format', 'parameters', 'filters', 'date_range_days',
            'is_scheduled', 'schedule_frequency', 'schedule_time',
            'created_by', 'created_by_username', 'is_public', 'usage_count',
            'generated_reports', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'report_id', 'created_by', 'created_by_username', 'usage_count', 'generated_reports', 'created_at', 'updated_at']

class LogRetentionSerializer(serializers.ModelSerializer):
    """
    Serializer for log retention policies.
    """
    class Meta:
        model = LogRetention
        fields = [
            'id', 'name', 'description', 'log_type', 'retention_days',
            'archive_after_days', 'delete_after_archive_days', 'is_active',
            'last_run', 'compress_archives', 'encrypt_archives',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_run', 'created_at', 'updated_at']

class LogStatisticsSerializer(serializers.ModelSerializer):
    """
    Serializer for log statistics.
    """
    class Meta:
        model = LogStatistics
        fields = [
            'id', 'date', 'total_activity_logs', 'activity_logs_by_level',
            'activity_logs_by_action', 'unique_users_active', 'total_audit_logs',
            'audit_logs_by_action', 'audit_logs_by_risk', 'total_system_logs',
            'system_logs_by_level', 'system_logs_by_component',
            'total_security_events', 'security_events_by_severity',
            'security_events_by_type', 'average_log_size', 'total_log_size',
            'calculated_at'
        ]
        read_only_fields = ['id', 'calculated_at']

class LogSearchSerializer(serializers.Serializer):
    """
    Serializer for log search functionality.
    """
    search = serializers.CharField(required=False)
    level = serializers.ChoiceField(choices=ActivityLog.LEVEL_CHOICES, required=False)
    action = serializers.ChoiceField(choices=ActivityLog.ACTION_CHOICES, required=False)
    category = serializers.IntegerField(required=False)
    user = serializers.IntegerField(required=False)
    ip_address = serializers.CharField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    model_name = serializers.CharField(required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)

class AuditLogSearchSerializer(serializers.Serializer):
    """
    Serializer for audit log search functionality.
    """
    search = serializers.CharField(required=False)
    action = serializers.ChoiceField(choices=AuditLog.AUDIT_ACTION_CHOICES, required=False)
    risk_level = serializers.ChoiceField(choices=AuditLog.RISK_LEVEL_CHOICES, required=False)
    model_name = serializers.CharField(required=False)
    user = serializers.IntegerField(required=False)
    approval_status = serializers.ChoiceField(
        choices=AuditLog._meta.get_field('approval_status').choices, required=False
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

class SecurityEventSearchSerializer(serializers.Serializer):
    """
    Serializer for security event search functionality.
    """
    search = serializers.CharField(required=False)
    event_type = serializers.ChoiceField(choices=SecurityEvent.EVENT_TYPE_CHOICES, required=False)
    severity = serializers.ChoiceField(choices=SecurityEvent.SEVERITY_CHOICES, required=False)
    status = serializers.ChoiceField(choices=SecurityEvent.STATUS_CHOICES, required=False)
    affected_user = serializers.IntegerField(required=False)
    assigned_to = serializers.IntegerField(required=False)
    source_ip = serializers.CharField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

class SystemLogSearchSerializer(serializers.Serializer):
    """
    Serializer for system log search functionality.
    """
    search = serializers.CharField(required=False)
    level = serializers.ChoiceField(choices=SystemLog.SYSTEM_LEVEL_CHOICES, required=False)
    component = serializers.ChoiceField(choices=SystemLog.COMPONENT_CHOICES, required=False)
    server_name = serializers.CharField(required=False)
    error_code = serializers.CharField(required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)

class LogStatisticsSerializer(serializers.Serializer):
    """
    Serializer for log statistics data.
    """
    total_activity_logs = serializers.IntegerField()
    activity_logs_by_level = serializers.DictField()
    activity_logs_by_action = serializers.DictField()
    unique_users_active = serializers.IntegerField()
    total_audit_logs = serializers.IntegerField()
    audit_logs_by_action = serializers.DictField()
    audit_logs_by_risk = serializers.DictField()
    total_system_logs = serializers.IntegerField()
    system_logs_by_level = serializers.DictField()
    system_logs_by_component = serializers.DictField()
    total_security_events = serializers.IntegerField()
    security_events_by_severity = serializers.DictField()
    security_events_by_type = serializers.DictField()
    recent_security_events = SecurityEventListSerializer(many=True)
    top_users_by_activity = serializers.ListField()
    error_trends = serializers.ListField()
    system_performance = serializers.DictField()

class LogExportSerializer(serializers.Serializer):
    """
    Serializer for log export functionality.
    """
    log_type = serializers.ChoiceField(
        choices=[
            ('ACTIVITY', 'Activity Logs'),
            ('AUDIT', 'Audit Logs'),
            ('SYSTEM', 'System Logs'),
            ('SECURITY', 'Security Events'),
        ]
    )
    format = serializers.ChoiceField(
        choices=[
            ('CSV', 'CSV'),
            ('JSON', 'JSON'),
            ('EXCEL', 'Excel'),
        ]
    )
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    filters = serializers.DictField(required=False)

class LogAlertCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating log alerts.
    """
    class Meta:
        model = LogAlert
        fields = [
            'name', 'description', 'severity', 'log_type', 'conditions',
            'threshold_count', 'time_window_minutes', 'notify_email',
            'notify_sms', 'notify_webhook', 'email_recipients', 'webhook_url'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class LogReportCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating log reports.
    """
    class Meta:
        model = LogReport
        fields = [
            'name', 'description', 'report_type', 'format', 'parameters',
            'filters', 'date_range_days', 'is_scheduled', 'schedule_frequency',
            'schedule_time', 'is_public'
        ]
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

class SecurityEventUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating security events.
    """
    class Meta:
        model = SecurityEvent
        fields = [
            'status', 'assigned_to', 'resolution_notes', 'false_positive_reason'
        ]
    
    def update(self, instance, validated_data):
        # If status is being changed to resolved, set resolved_at
        if 'status' in validated_data and validated_data['status'] == 'RESOLVED':
            instance.resolved_at = timezone.now()
        
        return super().update(instance, validated_data)

class AuditLogApprovalSerializer(serializers.ModelSerializer):
    """
    Serializer for approving/rejecting audit logs.
    """
    class Meta:
        model = AuditLog
        fields = ['approval_status', 'reason']
    
    def update(self, instance, validated_data):
        instance.approved_by = self.context['request'].user
        instance.approved_at = timezone.now()
        return super().update(instance, validated_data)
