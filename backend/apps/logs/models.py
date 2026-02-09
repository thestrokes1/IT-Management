"""
Log models for IT Management Platform.
Comprehensive activity logging and audit trail system.
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
import json
import uuid
from datetime import datetime, timedelta

User = get_user_model()

class LogCategory(models.Model):
    """
    Categories for organizing different types of logs.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color code
    is_active = models.BooleanField(default=True)
    retention_days = models.PositiveIntegerField(default=90)  # How long to keep logs
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'log_categories'
        verbose_name = 'Log Category'
        verbose_name_plural = 'Log Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class ActivityLog(models.Model):
    """
    Activity log model for the IT Management Platform.

    Architectural rules:
    - `timestamp` is the canonical and ONLY time field for activity logging.
    - The `created_at` field must NEVER be added to this model.
    - All ordering, filtering, and display logic MUST use `timestamp`.
    - Actor information (actor_id, actor_name, actor_role) is captured at log creation time
      and stored as plain strings to avoid foreign key dereferencing in templates.
      This ensures logs remain readable even if the user is deleted.
    """
    # Log level choices
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    # Action type choices
    ACTION_CHOICES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('SEARCH', 'Search'),
        ('DOWNLOAD', 'Download'),
        ('UPLOAD', 'Upload'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
        ('API_CALL', 'API Call'),
        ('SYSTEM_ACTION', 'System Action'),
        ('SECURITY_EVENT', 'Security Event'),
        ('ERROR', 'Error'),
        ('OTHER', 'Other'),
    ]
    
    # Actor type choices - determines WHO performed the action
    ACTOR_TYPE_CHOICES = [
        ('user', 'User'),
        ('system', 'System'),
        ('automation', 'Automation'),
        ('api', 'API'),
    ]
    
    # Severity choices - used for filtering and display prioritization
    SEVERITY_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('SECURITY', 'Security'),
    ]
    
    # Intent choices - describes WHY the action was performed
    INTENT_CHOICES = [
        ('workflow', 'Workflow'),
        ('sla_risk', 'SLA Risk'),
        ('security', 'Security'),
        ('system', 'System'),
    ]
    
    # Log ID (unique identifier)
    log_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # ==========================================================================
    # Actor Information - IMMUTABLE, captured at log creation time
    # These fields are NOT foreign keys to avoid template FK dereferencing
    # ==========================================================================
    actor_type = models.CharField(
        max_length=20,
        choices=ACTOR_TYPE_CHOICES,
        default='user',
        help_text="Type of actor that performed the action"
    )
    actor_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Actor ID (user ID for users, null for system/automation)"
    )
    actor_name = models.CharField(
        max_length=255,
        help_text="Actor name resolved at log creation time (e.g., username)"
    )
    actor_role = models.CharField(
        max_length=50,
        default='VIEWER',
        help_text="Actor role resolved at log creation time, never dereferenced from FK"
    )
    
    # ==========================================================================
    # Event Information
    # ==========================================================================
    event_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Specific event type (e.g., TICKET_CREATED, ASSET_UPDATED)"
    )
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='INFO',
        help_text="Severity level for filtering and prioritization"
    )
    intent = models.CharField(
        max_length=20,
        choices=INTENT_CHOICES,
        default='workflow',
        help_text="Intent/purpose of the logged action"
    )
    
    # ==========================================================================
    # Entity Information - What was affected
    # ==========================================================================
    entity_type = models.CharField(
        max_length=100,
        blank=True,
        help_text="Type of affected entity (e.g., ticket, asset, project, user)"
    )
    entity_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="ID of the affected entity"
    )
    
    # ==========================================================================
    # Causal Log Chaining - Parent/Child relationship
    # Each log may reference a parent_log_id to form causal chains:
    # Asset failure → Ticket created → Technician assigned → SLA breach → Escalation
    # ==========================================================================
    parent_log_id = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Parent log ID for causal chaining. Creates: Asset failure → Ticket created → ..."
    )
    chain_depth = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Depth in the log chain (0 = root, 1 = child, 2 = grandchild, etc.)"
    )
    chain_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Type of causal relationship (e.g., CAUSED, ESCALATED, RESOLVED)"
    )
    
    # ==========================================================================
    # Legacy Foreign Key (deprecated but kept for backward compatibility)
    # DO NOT dereference this field in templates - use actor_* fields instead
    # ==========================================================================
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs'
    )
    
    # Action and categorization
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='INFO')
    category = models.ForeignKey(
        LogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs'
    )
    
    # Activity details
    title = models.CharField(max_length=200)
    description = models.TextField()
    model_name = models.CharField(max_length=100, blank=True)  # Django model name
    object_id = models.PositiveIntegerField(null=True, blank=True)  # ID of affected object
    object_repr = models.CharField(max_length=255, blank=True)  # String representation of object
    
    # Request information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    response_status = models.PositiveIntegerField(null=True, blank=True)
    
    # Session information
    session_key = models.CharField(max_length=40, blank=True)
    session_data = models.JSONField(default=dict, blank=True)
    
    # Additional context
    extra_data = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Timestamps
    timestamp = models.DateTimeField(
    auto_now_add=True,
    db_index=True,
    help_text=(
        "Primary timestamp for activity logging. "
        "Used for dashboard ordering, display, and all temporal queries."
    ),
)

    
    class Meta:
        db_table = 'activity_logs'
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['category', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        user_info = self.user.username if self.user else 'Anonymous'
        return f"{self.timestamp} - {user_info} - {self.title}"

class AuditLog(models.Model):
    """
    Audit log for sensitive operations and data changes.
    """
    # Audit action types
    AUDIT_ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('PERMISSION_CHANGE', 'Permission Change'),
        ('ROLE_CHANGE', 'Role Change'),
        ('SECURITY_EVENT', 'Security Event'),
        ('DATA_EXPORT', 'Data Export'),
        ('DATA_IMPORT', 'Data Import'),
        ('CONFIG_CHANGE', 'Configuration Change'),
        ('SYSTEM_ACCESS', 'System Access'),
    ]
    
    # Risk level choices
    RISK_LEVEL_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    # Audit ID (unique identifier)
    audit_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Basic information
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=AUDIT_ACTION_CHOICES)
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default='LOW')
    
    # Object information
    model_name = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField()
    object_repr = models.CharField(max_length=255)
    
    # Change tracking
    field_name = models.CharField(max_length=100, blank=True)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    changes_summary = models.TextField(blank=True)
    
    # Request information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    
    # Additional context
    reason = models.TextField(blank=True)  # Why the change was made
    approval_status = models.CharField(
        max_length=20, choices=[
            ('PENDING', 'Pending'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected'),
            ('NOT_REQUIRED', 'Not Required'),
        ],
        default='NOT_REQUIRED'
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_audit_logs'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    extra_data = models.JSONField(default=dict, blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(
    auto_now_add=True,
    db_index=True,
    help_text=(
        "Primary timestamp for activity logging. "
        "Used for dashboard ordering, display, and all temporal queries."
    ),
)

    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['risk_level', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['approval_status', 'timestamp']),
        ]
    
    def __str__(self):
        user_info = self.user.username if self.user else 'System'
        return f"{self.timestamp} - {user_info} - {self.action} {self.model_name}({self.object_id})"

class SystemLog(models.Model):
    """
    System-level events and errors.
    """
    # System log level choices
    SYSTEM_LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    # Component choices
    COMPONENT_CHOICES = [
        ('DATABASE', 'Database'),
        ('AUTHENTICATION', 'Authentication'),
        ('API', 'API'),
        ('EMAIL', 'Email'),
        ('FILE_SYSTEM', 'File System'),
        ('MEMORY', 'Memory'),
        ('CPU', 'CPU'),
        ('NETWORK', 'Network'),
        ('SECURITY', 'Security'),
        ('BACKUP', 'Backup'),
        ('MAINTENANCE', 'Maintenance'),
        ('INTEGRATION', 'Integration'),
        ('OTHER', 'Other'),
    ]
    
    # Log ID (unique identifier)
    log_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Basic information
    level = models.CharField(max_length=10, choices=SYSTEM_LEVEL_CHOICES, default='INFO')
    component = models.CharField(max_length=20, choices=COMPONENT_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Error details
    error_code = models.CharField(max_length=50, blank=True)
    error_type = models.CharField(max_length=100, blank=True)
    traceback = models.TextField(blank=True)
    
    # System information
    process_id = models.PositiveIntegerField(null=True, blank=True)
    thread_id = models.PositiveIntegerField(null=True, blank=True)
    server_name = models.CharField(max_length=100, blank=True)
    
    # Performance metrics
    execution_time = models.FloatField(null=True, blank=True)  # in seconds
    memory_usage = models.BigIntegerField(null=True, blank=True)  # in bytes
    
    # Additional context
    extra_data = models.JSONField(default=dict, blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(
    auto_now_add=True,
    db_index=True,
    help_text=(
        "Primary timestamp for activity logging. "
        "Used for dashboard ordering, display, and all temporal queries."
    ),
)

    
    class Meta:
        db_table = 'system_logs'
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['level', 'timestamp']),
            models.Index(fields=['component', 'timestamp']),
            models.Index(fields=['server_name', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.timestamp} - {self.level} - {self.component} - {self.title}"

class SecurityEvent(models.Model):
    """
    Security-related events and incidents.
    """
    # Event severity
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    # Event status
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('INVESTIGATING', 'Investigating'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_POSITIVE', 'False Positive'),
        ('CLOSED', 'Closed'),
    ]
    
    # Event type choices
    EVENT_TYPE_CHOICES = [
        ('FAILED_LOGIN', 'Failed Login Attempt'),
        ('BRUTE_FORCE', 'Brute Force Attack'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access'),
        ('PRIVILEGE_ESCALATION', 'Privilege Escalation'),
        ('DATA_BREACH', 'Data Breach'),
        ('MALWARE_DETECTION', 'Malware Detection'),
        ('SUSPICIOUS_ACTIVITY', 'Suspicious Activity'),
        ('POLICY_VIOLATION', 'Policy Violation'),
        ('UNAUTHORIZED_API_CALL', 'Unauthorized API Call'),
        ('SESSION_HIJACKING', 'Session Hijacking'),
        ('SQL_INJECTION', 'SQL Injection Attempt'),
        ('XSS_ATTEMPT', 'XSS Attempt'),
        ('CSRF_VIOLATION', 'CSRF Violation'),
        ('FILE_UPLOAD_ABUSE', 'File Upload Abuse'),
        ('OTHER', 'Other'),
    ]
    
    # Event ID (unique identifier)
    event_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Basic information
    event_type = models.CharField(max_length=30, choices=EVENT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    # Event details
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # User information
    affected_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='security_events'
    )
    source_ip = models.GenericIPAddressField(null=True, blank=True)
    target_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Request information
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    # Incident response
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_security_events'
    )
    resolution_notes = models.TextField(blank=True)
    false_positive_reason = models.TextField(blank=True)
    
    # Timestamps
    detected_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Additional context
    extra_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'security_events'
        verbose_name = 'Security Event'
        verbose_name_plural = 'Security Events'
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['detected_at']),
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['event_type', 'detected_at']),
            models.Index(fields=['affected_user', 'detected_at']),
            models.Index(fields=['source_ip', 'detected_at']),
        ]
    
    def __str__(self):
        return f"{self.detected_at} - {self.get_severity_display()} - {self.title}"

class LogAlert(models.Model):
    """
    Alert rules and configurations for log monitoring.
    """
    # Alert severity
    SEVERITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    # Alert status
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('TRIGGERED', 'Triggered'),
        ('ACKNOWLEDGED', 'Acknowledged'),
        ('RESOLVED', 'Resolved'),
    ]
    
    # Alert ID (unique identifier)
    alert_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Basic information
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Alert conditions
    log_type = models.CharField(
        max_length=20, choices=[
            ('ACTIVITY', 'Activity Log'),
            ('AUDIT', 'Audit Log'),
            ('SYSTEM', 'System Log'),
            ('SECURITY', 'Security Event'),
        ]
    )
    conditions = models.JSONField(default=dict, blank=True)  # JSON conditions for triggering
    threshold_count = models.PositiveIntegerField(default=1)  # Number of occurrences to trigger
    time_window_minutes = models.PositiveIntegerField(default=60)  # Time window for threshold
    
    # Notification settings
    notify_email = models.BooleanField(default=True)
    notify_sms = models.BooleanField(default=False)
    notify_webhook = models.BooleanField(default=False)
    email_recipients = models.JSONField(default=list, blank=True)
    webhook_url = models.URLField(blank=True)
    
    # Alert management
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_log_alerts'
    )
    last_triggered = models.DateTimeField(null=True, blank=True)
    trigger_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'log_alerts'
        verbose_name = 'Log Alert'
        verbose_name_plural = 'Log Alerts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'severity']),
            models.Index(fields=['log_type', 'status']),
        ]
    
    def __str__(self):
        return self.name

class LogAlertTrigger(models.Model):
    """
    Record of triggered log alerts.
    """
    # Trigger ID (unique identifier)
    trigger_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Associated alert
    alert = models.ForeignKey(LogAlert, on_delete=models.CASCADE, related_name='triggers')
    
    # Trigger details
    triggered_at = models.DateTimeField(auto_now_add=True)
    matching_logs_count = models.PositiveIntegerField()
    matching_logs_sample = models.JSONField(default=list, blank=True)  # Sample of matching logs
    
    # Notification status
    email_sent = models.BooleanField(default=False)
    sms_sent = models.BooleanField(default=False)
    webhook_sent = models.BooleanField(default=False)
    
    # Resolution
    acknowledged_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alert_triggers'
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'log_alert_triggers'
        verbose_name = 'Log Alert Trigger'
        verbose_name_plural = 'Log Alert Triggers'
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['triggered_at']),
            models.Index(fields=['alert', 'triggered_at']),
        ]
    
    def __str__(self):
        return f"{self.triggered_at} - {self.alert.name}"

class LogReport(models.Model):
    """
    Predefined and custom log reports.
    """
    # Report type choices
    REPORT_TYPE_CHOICES = [
        ('USER_ACTIVITY', 'User Activity Report'),
        ('SECURITY_EVENTS', 'Security Events Report'),
        ('SYSTEM_PERFORMANCE', 'System Performance Report'),
        ('AUDIT_TRAIL', 'Audit Trail Report'),
        ('ERROR_SUMMARY', 'Error Summary Report'),
        ('LOGIN_ANALYSIS', 'Login Analysis Report'),
        ('CUSTOM', 'Custom Report'),
    ]
    
    # Report format choices
    FORMAT_CHOICES = [
        ('HTML', 'HTML'),
        ('PDF', 'PDF'),
        ('CSV', 'CSV'),
        ('JSON', 'JSON'),
        ('EXCEL', 'Excel'),
    ]
    
    # Report ID (unique identifier)
    report_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Basic information
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='HTML')
    
    # Report configuration
    parameters = models.JSONField(default=dict, blank=True)  # Report parameters
    filters = models.JSONField(default=dict, blank=True)  # Log filters
    date_range_days = models.PositiveIntegerField(default=30)  # Default date range
    
    # Scheduling
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(
        max_length=20, choices=[
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
            ('MONTHLY', 'Monthly'),
            ('QUARTERLY', 'Quarterly'),
        ],
        blank=True
    )
    schedule_time = models.TimeField(null=True, blank=True)
    
    # Report metadata
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_log_reports'
    )
    is_public = models.BooleanField(default=False)
    usage_count = models.PositiveIntegerField(default=0)
    
    # Generated reports
    generated_reports = models.JSONField(default=list, blank=True)  # List of generated report files
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'log_reports'
        verbose_name = 'Log Report'
        verbose_name_plural = 'Log Reports'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['report_type', 'is_public']),
            models.Index(fields=['created_by', 'created_at']),
        ]
    
    def __str__(self):
        return self.name

class LogRetention(models.Model):
    """
    Log retention policies and cleanup rules.
    """
    # Retention policy name
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Retention settings
    log_type = models.CharField(
        max_length=20, choices=[
            ('ACTIVITY', 'Activity Logs'),
            ('AUDIT', 'Audit Logs'),
            ('SYSTEM', 'System Logs'),
            ('SECURITY', 'Security Events'),
            ('ALL', 'All Logs'),
        ]
    )
    retention_days = models.PositiveIntegerField()
    archive_after_days = models.PositiveIntegerField(default=0)  # Move to archive after X days
    delete_after_archive_days = models.PositiveIntegerField(default=0)  # Delete from archive after X days
    
    # Policy status
    is_active = models.BooleanField(default=True)
    last_run = models.DateTimeField(null=True, blank=True)
    
    # Additional settings
    compress_archives = models.BooleanField(default=True)
    encrypt_archives = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'log_retention'
        verbose_name = 'Log Retention Policy'
        verbose_name_plural = 'Log Retention Policies'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.retention_days} days)"

class LogStatistics(models.Model):
    """
    Pre-calculated log statistics for performance.
    """
    # Date for statistics
    date = models.DateField(unique=True)
    
    # Activity log statistics
    total_activity_logs = models.PositiveIntegerField(default=0)
    activity_logs_by_level = models.JSONField(default=dict)
    activity_logs_by_action = models.JSONField(default=dict)
    unique_users_active = models.PositiveIntegerField(default=0)
    
    # Audit log statistics
    total_audit_logs = models.PositiveIntegerField(default=0)
    audit_logs_by_action = models.JSONField(default=dict)
    audit_logs_by_risk = models.JSONField(default=dict)
    
    # System log statistics
    total_system_logs = models.PositiveIntegerField(default=0)
    system_logs_by_level = models.JSONField(default=dict)
    system_logs_by_component = models.JSONField(default=dict)
    
    # Security event statistics
    total_security_events = models.PositiveIntegerField(default=0)
    security_events_by_severity = models.JSONField(default=dict)
    security_events_by_type = models.JSONField(default=dict)
    
    # Performance metrics
    average_log_size = models.FloatField(default=0)  # Average log entry size in bytes
    total_log_size = models.BigIntegerField(default=0)  # Total log size in bytes
    
    # Calculated at
    calculated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'log_statistics'
        verbose_name = 'Log Statistics'
        verbose_name_plural = 'Log Statistics'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"Statistics for {self.date}"
