"""
Security serializers for IT Management Platform.
Handles serialization and validation of security-related data.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import (
    SecurityEvent, AuditLog, SecurityPolicy, SecurityThreshold,
    SecurityIncident, SecurityDashboard
)


class SecurityEventSerializer(serializers.ModelSerializer):
    """
    Serializer for SecurityEvent model.
    """
    resolved_by_username = serializers.CharField(source='resolved_by.username', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    time_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityEvent
        fields = [
            'id', 'event_type', 'severity', 'status', 'title', 'description',
            'ip_address', 'user_agent', 'referer', 'user', 'user_username',
            'username', 'request_method', 'request_path', 'request_params',
            'response_status', 'response_data', 'session_id', 'additional_data',
            'created_at', 'updated_at', 'resolved_at', 'resolved_by',
            'resolved_by_username', 'resolution_notes', 'time_since_created'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'resolved_at', 'resolved_by',
            'time_since_created'
        ]
    
    def get_time_since_created(self, obj):
        """Calculate time since event creation."""
        delta = timezone.now() - obj.created_at
        if delta.days > 0:
            return f"{delta.days} day(s) ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour(s) ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute(s) ago"
        else:
            return "Just now"
    
    def validate_event_type(self, value):
        """Validate event type."""
        valid_types = dict(SecurityEvent.EVENT_TYPES).keys()
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid event type. Must be one of: {', '.join(valid_types)}")
        return value
    
    def validate_severity(self, value):
        """Validate severity level."""
        valid_severities = dict(SecurityEvent.SEVERITY_LEVELS).keys()
        if value not in valid_severities:
            raise serializers.ValidationError(f"Invalid severity. Must be one of: {', '.join(valid_severities)}")
        return value


class SecurityEventCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating SecurityEvent instances.
    """
    class Meta:
        model = SecurityEvent
        fields = [
            'event_type', 'severity', 'title', 'description', 'ip_address',
            'user_agent', 'referer', 'user', 'username', 'request_method',
            'request_path', 'request_params', 'response_status', 'response_data',
            'session_id', 'additional_data'
        ]
    
    def validate_ip_address(self, value):
        """Validate IP address format."""
        if value and not self.validate_ip_format(value):
            raise serializers.ValidationError("Invalid IP address format")
        return value
    
    def validate_ip_format(self, ip):
        """Validate IP address format using regex."""
        import re
        ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        ipv6_pattern = r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
        return re.match(ipv4_pattern, ip) or re.match(ipv6_pattern, ip)


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog model.
    """
    user_username = serializers.CharField(source='user.username', read_only=True, allow_null=True)
    time_since_audit = serializers.SerializerMethodField()
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'action', 'resource_type', 'resource_id', 'resource_name',
            'user', 'user_username', 'username', 'ip_address', 'user_agent',
            'session_id', 'old_values', 'new_values', 'changed_fields',
            'description', 'additional_data', 'success', 'error_message',
            'timestamp', 'time_since_audit'
        ]
        read_only_fields = [
            'id', 'timestamp', 'time_since_audit'
        ]
    
    def get_time_since_audit(self, obj):
        """Calculate time since audit log entry."""
        delta = timezone.now() - obj.timestamp
        if delta.days > 0:
            return f"{delta.days} day(s) ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours} hour(s) ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes} minute(s) ago"
        else:
            return "Just now"


class SecurityPolicySerializer(serializers.ModelSerializer):
    """
    Serializer for SecurityPolicy model.
    """
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    modified_by_username = serializers.CharField(source='modified_by.username', read_only=True)
    is_valid_now = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = SecurityPolicy
        fields = [
            'id', 'name', 'policy_type', 'description', 'status', 'config',
            'rules', 'valid_from', 'valid_until', 'version', 'created_by',
            'created_by_username', 'modified_by', 'modified_by_username',
            'created_at', 'updated_at', 'is_valid_now'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'is_valid_now'
        ]
    
    def validate_policy_type(self, value):
        """Validate policy type."""
        valid_types = dict(SecurityPolicy.POLICY_TYPES).keys()
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid policy type. Must be one of: {', '.join(valid_types)}")
        return value
    
    def validate_status(self, value):
        """Validate status."""
        valid_statuses = dict(SecurityPolicy.STATUS_CHOICES).keys()
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return value


class SecurityThresholdSerializer(serializers.ModelSerializer):
    """
    Serializer for SecurityThreshold model.
    """
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    threshold_display = serializers.CharField(read_only=True)
    
    class Meta:
        model = SecurityThreshold
        fields = [
            'id', 'name', 'threshold_type', 'operator', 'value', 'unit',
            'scope', 'context_data', 'alert_enabled', 'auto_block_enabled',
            'notification_recipients', 'is_active', 'created_by',
            'created_by_username', 'created_at', 'updated_at',
            'threshold_display'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'threshold_display'
        ]
    
    def validate_threshold_type(self, value):
        """Validate threshold type."""
        valid_types = dict(SecurityThreshold.THRESHOLD_TYPES).keys()
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid threshold type. Must be one of: {', '.join(valid_types)}")
        return value
    
    def validate_operator(self, value):
        """Validate operator."""
        valid_operators = dict(SecurityThreshold.THRESHOLD_OPERATORS).keys()
        if value not in valid_operators:
            raise serializers.ValidationError(f"Invalid operator. Must be one of: {', '.join(valid_operators)}")
        return value


class SecurityIncidentSerializer(serializers.ModelSerializer):
    """
    Serializer for SecurityIncident model.
    """
    discovered_by_username = serializers.CharField(source='discovered_by.username', read_only=True, allow_null=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True, allow_null=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    age_in_hours_display = serializers.CharField(read_only=True)
    time_to_resolution = serializers.SerializerMethodField()
    related_events_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityIncident
        fields = [
            'id', 'title', 'incident_type', 'severity', 'status', 'description',
            'impact_assessment', 'affected_systems', 'affected_users',
            'discovered_by', 'discovered_by_username', 'assigned_to',
            'assigned_to_username', 'discovered_at', 'reported_at',
            'contained_at', 'resolved_at', 'resolution_summary',
            'lessons_learned', 'preventive_measures', 'related_events',
            'case_number', 'created_by', 'created_by_username', 'created_at',
            'updated_at', 'age_in_hours', 'age_in_hours_display',
            'time_to_resolution', 'related_events_summary'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'case_number', 'age_in_hours',
            'age_in_hours_display', 'time_to_resolution', 'related_events_summary'
        ]
    
    def get_time_to_resolution(self, obj):
        """Calculate time to resolution for resolved incidents."""
        if obj.resolved_at:
            delta = obj.resolved_at - obj.discovered_at
            if delta.days > 0:
                return f"{delta.days} day(s), {delta.seconds // 3600} hour(s)"
            else:
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                return f"{hours}h {minutes}m"
        return None
    
    def get_related_events_summary(self, obj):
        """Get summary of related security events."""
        events = obj.related_events.all()
        if not events:
            return "No related events"
        
        event_types = [event.get_event_type_display() for event in events[:5]]
        if len(events) > 5:
            event_types.append(f"... and {len(events) - 5} more")
        
        return ", ".join(event_types)
    
    def validate_incident_type(self, value):
        """Validate incident type."""
        valid_types = dict(SecurityIncident.INCIDENT_TYPES).keys()
        if value not in valid_types:
            raise serializers.ValidationError(f"Invalid incident type. Must be one of: {', '.join(valid_types)}")
        return value
    
    def validate_severity(self, value):
        """Validate severity."""
        valid_severities = dict(SecurityIncident.INCIDENT_SEVERITY).keys()
        if value not in valid_severities:
            raise serializers.ValidationError(f"Invalid severity. Must be one of: {', '.join(valid_severities)}")
        return value


class SecurityDashboardSerializer(serializers.ModelSerializer):
    """
    Serializer for SecurityDashboard model.
    """
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    allowed_users_list = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityDashboard
        fields = [
            'id', 'name', 'description', 'widgets', 'layout', 'refresh_interval',
            'is_public', 'allowed_users', 'allowed_roles', 'created_by',
            'created_by_username', 'created_at', 'updated_at',
            'allowed_users_list'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'allowed_users_list'
        ]
    
    def get_allowed_users_list(self, obj):
        """Get list of allowed usernames."""
        return [user.username for user in obj.allowed_users.all()]


class SecurityDashboardCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating SecurityDashboard instances.
    """
    allowed_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        help_text="List of user IDs to grant access"
    )
    
    class Meta:
        model = SecurityDashboard
        fields = [
            'name', 'description', 'widgets', 'layout', 'refresh_interval',
            'is_public', 'allowed_user_ids'
        ]
    
    def create(self, validated_data):
        """Create dashboard with allowed users."""
        allowed_user_ids = validated_data.pop('allowed_user_ids', [])
        dashboard = SecurityDashboard.objects.create(**validated_data)
        
        if allowed_user_ids:
            dashboard.allowed_users.set(User.objects.filter(id__in=allowed_user_ids))
        
        return dashboard


class SecurityStatisticsSerializer(serializers.Serializer):
    """
    Serializer for security statistics and metrics.
    """
    total_events = serializers.IntegerField()
    events_today = serializers.IntegerField()
    events_this_week = serializers.IntegerField()
    events_this_month = serializers.IntegerField()
    high_severity_events = serializers.IntegerField()
    critical_events = serializers.IntegerField()
    open_incidents = serializers.IntegerField()
    resolved_incidents = serializers.IntegerField()
    active_threats = serializers.IntegerField()
    blocked_ips = serializers.IntegerField()
    failed_logins_today = serializers.IntegerField()
    successful_logins_today = serializers.IntegerField()
    
    # Top lists
    top_attack_types = serializers.ListField(
        child=serializers.DictField()
    )
    top_source_ips = serializers.ListField(
        child=serializers.DictField()
    )
    most_affected_users = serializers.ListField(
        child=serializers.DictField()
    )


class SecurityAlertSerializer(serializers.Serializer):
    """
    Serializer for security alerts and notifications.
    """
    alert_type = serializers.CharField()
    severity = serializers.CharField()
    title = serializers.CharField()
    message = serializers.CharField()
    source_ip = serializers.CharField(required=False, allow_null=True)
    user = serializers.CharField(required=False, allow_null=True)
    timestamp = serializers.DateTimeField()
    metadata = serializers.DictField(required=False)


class SecurityHealthCheckSerializer(serializers.Serializer):
    """
    Serializer for security system health check.
    """
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    services = serializers.DictField()
    last_updated = serializers.DateTimeField()
    uptime = serializers.CharField()
    version = serializers.CharField()


class BulkSecurityEventActionSerializer(serializers.Serializer):
    """
    Serializer for bulk actions on security events.
    """
    event_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    action = serializers.ChoiceField(choices=[
        ('RESOLVE', 'Resolve'),
        ('ESCALATE', 'Escalate'),
        ('MARK_FALSE_POSITIVE', 'Mark as False Positive'),
        ('ASSIGN', 'Assign'),
        ('DELETE', 'Delete'),
    ])
    notes = serializers.CharField(required=False, allow_blank=True)
    assignee_id = serializers.IntegerField(required=False, allow_null=True)


class SecurityConfigurationSerializer(serializers.Serializer):
    """
    Serializer for security configuration settings.
    """
    # Rate Limiting
    rate_limiting_enabled = serializers.BooleanField()
    requests_per_minute = serializers.IntegerField(min_value=1)
    requests_per_hour = serializers.IntegerField(min_value=1)
    requests_per_day = serializers.IntegerField(min_value=1)
    
    # Session Management
    session_timeout_minutes = serializers.IntegerField(min_value=1)
    max_concurrent_sessions = serializers.IntegerField(min_value=1)
    
    # Password Policy
    password_min_length = serializers.IntegerField(min_value=6)
    password_require_uppercase = serializers.BooleanField()
    password_require_lowercase = serializers.BooleanField()
    password_require_numbers = serializers.BooleanField()
    password_require_symbols = serializers.BooleanField()
    
    # Account Lockout
    max_failed_attempts = serializers.IntegerField(min_value=1)
    lockout_duration_minutes = serializers.IntegerField(min_value=1)
    
    # Logging
    log_retention_days = serializers.IntegerField(min_value=1)
    audit_log_enabled = serializers.BooleanField()
    security_event_logging_enabled = serializers.BooleanField()

