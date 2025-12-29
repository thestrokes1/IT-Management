"""
Security models for IT Management Platform.
Defines security events, audit logs, and security policies.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError


class SecurityEvent(models.Model):
    """
    Model for tracking security events and incidents.
    """
    EVENT_TYPES = [
        ('LOGIN_SUCCESS', 'Successful Login'),
        ('LOGIN_FAILURE', 'Failed Login'),
        ('LOGOUT', 'User Logout'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('PASSWORD_RESET', 'Password Reset'),
        ('ACCOUNT_LOCKED', 'Account Locked'),
        ('ACCOUNT_UNLOCKED', 'Account Unlocked'),
        ('RATE_LIMIT_EXCEEDED', 'Rate Limit Exceeded'),
        ('SUSPICIOUS_ACTIVITY', 'Suspicious Activity'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access'),
        ('SECURITY_VIOLATION', 'Security Violation'),
        ('DATA_BREACH_ATTEMPT', 'Data Breach Attempt'),
        ('XSS_ATTEMPT', 'XSS Attack Attempt'),
        ('SQL_INJECTION_ATTEMPT', 'SQL Injection Attempt'),
        ('CSRF_VIOLATION', 'CSRF Violation'),
        ('FILE_UPLOAD_BLOCKED', 'Blocked File Upload'),
        ('PERMISSION_DENIED', 'Permission Denied'),
        ('SESSION_EXPIRED', 'Session Expired'),
        ('TOKEN_EXPIRED', 'Token Expired'),
        ('SECURITY_CONFIG_CHANGE', 'Security Configuration Change'),
    ]

    SEVERITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('INVESTIGATING', 'Investigating'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_POSITIVE', 'False Positive'),
        ('ESCALATED', 'Escalated'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='LOW')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    
    # Event Details
    title = models.CharField(max_length=200)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referer = models.URLField(blank=True)
    
    # User Information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='security_security_events')
    username = models.CharField(max_length=150, blank=True)
    
    # Request Information
    request_method = models.CharField(max_length=10, blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_params = models.JSONField(default=dict, blank=True)
    
    # Response Information
    response_status = models.IntegerField(null=True, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    
    # Additional Context
    session_id = models.CharField(max_length=100, blank=True)
    additional_data = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Resolution Information
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_security_events')
    resolution_notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['status']),
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.title} ({self.severity})"

    def resolve(self, user, notes=""):
        """Mark the security event as resolved."""
        self.status = 'RESOLVED'
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.resolution_notes = notes
        self.save()


class AuditLog(models.Model):
    """
    Model for audit logging of all system activities.
    """
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('READ', 'Read'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
        ('DOWNLOAD', 'Download'),
        ('UPLOAD', 'Upload'),
        ('PRINT', 'Print'),
        ('SHARE', 'Share'),
        ('CHANGE_PASSWORD', 'Change Password'),
        ('RESET_PASSWORD', 'Reset Password'),
        ('PERMISSION_CHANGE', 'Permission Change'),
        ('CONFIGURATION_CHANGE', 'Configuration Change'),
    ]

    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    resource_type = models.CharField(max_length=50)  # e.g., 'user', 'asset', 'ticket'
    resource_id = models.CharField(max_length=50, blank=True)  # ID of the resource
    resource_name = models.CharField(max_length=200, blank=True)  # Name/description of resource
    
    # User Information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='security_audit_logs')
    username = models.CharField(max_length=150)
    
    # Request Information
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    # Change Details
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    changed_fields = models.JSONField(default=list, blank=True)
    
    # Additional Information
    description = models.TextField(blank=True)
    additional_data = models.JSONField(default=dict, blank=True)
    
    # Status
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action']),
            models.Index(fields=['resource_type']),
            models.Index(fields=['user']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f"{self.action} {self.resource_type} by {self.username} at {self.timestamp}"


class SecurityPolicy(models.Model):
    """
    Model for managing security policies and rules.
    """
    POLICY_TYPES = [
        ('PASSWORD_POLICY', 'Password Policy'),
        ('ACCOUNT_LOCKOUT', 'Account Lockout Policy'),
        ('SESSION_POLICY', 'Session Policy'),
        ('RATE_LIMITING', 'Rate Limiting Policy'),
        ('ACCESS_CONTROL', 'Access Control Policy'),
        ('DATA_RETENTION', 'Data Retention Policy'),
        ('ENCRYPTION', 'Encryption Policy'),
        ('BACKUP_POLICY', 'Backup Policy'),
        ('INCIDENT_RESPONSE', 'Incident Response Policy'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('DRAFT', 'Draft'),
    ]

    name = models.CharField(max_length=100, unique=True)
    policy_type = models.CharField(max_length=30, choices=POLICY_TYPES)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Policy Configuration
    config = models.JSONField(default=dict, help_text='Policy-specific configuration')
    rules = models.JSONField(default=list, help_text='List of policy rules')
    
    # Validity Period
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    version = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_security_policies')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='modified_security_policies')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['policy_type']),
            models.Index(fields=['status']),
            models.Index(fields=['valid_from']),
        ]

    def __str__(self):
        return f"{self.name} ({self.policy_type})"

    def is_valid(self):
        """Check if the policy is currently valid."""
        now = timezone.now()
        return (
            self.status == 'ACTIVE' and
            self.valid_from <= now and
            (self.valid_until is None or self.valid_until >= now)
        )


class SecurityThreshold(models.Model):
    """
    Model for configurable security thresholds and limits.
    """
    THRESHOLD_TYPES = [
        ('FAILED_LOGIN_ATTEMPTS', 'Failed Login Attempts'),
        ('RATE_LIMIT_REQUESTS', 'Rate Limit Requests'),
        ('CONCURRENT_SESSIONS', 'Concurrent Sessions'),
        ('PASSWORD_COMPLEXITY', 'Password Complexity Score'),
        ('SESSION_DURATION', 'Session Duration'),
        ('API_REQUEST_FREQUENCY', 'API Request Frequency'),
        ('DATA_EXPORT_SIZE', 'Data Export Size'),
        ('FILE_UPLOAD_SIZE', 'File Upload Size'),
        ('LOG_RETENTION_DAYS', 'Log Retention Days'),
    ]

    THRESHOLD_OPERATORS = [
        ('GREATER_THAN', '>'),
        ('GREATER_EQUAL', '>='),
        ('LESS_THAN', '<'),
        ('LESS_EQUAL', '<='),
        ('EQUAL', '='),
        ('NOT_EQUAL', '!='),
    ]

    name = models.CharField(max_length=100, unique=True)
    threshold_type = models.CharField(max_length=30, choices=THRESHOLD_TYPES)
    operator = models.CharField(max_length=15, choices=THRESHOLD_OPERATORS)
    value = models.FloatField()
    unit = models.CharField(max_length=20, blank=True, help_text='Unit of measurement (e.g., minutes, MB)')
    
    # Context and Scope
    scope = models.CharField(max_length=50, default='GLOBAL', help_text='Scope of threshold (GLOBAL, USER, IP, etc.)')
    context_data = models.JSONField(default=dict, blank=True, help_text='Additional context for threshold application')
    
    # Actions to take when threshold is exceeded
    alert_enabled = models.BooleanField(default=True)
    auto_block_enabled = models.BooleanField(default=False)
    notification_recipients = models.JSONField(default=list, blank=True)
    
    # Status and Metadata
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_security_thresholds')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['threshold_type']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name}: {self.operator} {self.value} {self.unit}"

    def check_threshold(self, current_value):
        """Check if current value exceeds the threshold."""
        if not self.is_active:
            return False
        
        if self.operator == 'GREATER_THAN':
            return current_value > self.value
        elif self.operator == 'GREATER_EQUAL':
            return current_value >= self.value
        elif self.operator == 'LESS_THAN':
            return current_value < self.value
        elif self.operator == 'LESS_EQUAL':
            return current_value <= self.value
        elif self.operator == 'EQUAL':
            return current_value == self.value
        elif self.operator == 'NOT_EQUAL':
            return current_value != self.value
        
        return False


class SecurityIncident(models.Model):
    """
    Model for tracking security incidents and their resolution.
    """
    INCIDENT_TYPES = [
        ('DATA_BREACH', 'Data Breach'),
        ('MALWARE_INFECTION', 'Malware Infection'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access'),
        ('DENIAL_OF_SERVICE', 'Denial of Service'),
        ('INSIDER_THREAT', 'Insider Threat'),
        ('PHISHING_ATTACK', 'Phishing Attack'),
        ('RANSOMWARE', 'Ransomware'),
        ('SYSTEM_COMPROMISE', 'System Compromise'),
        ('CONFIGURATION_ERROR', 'Configuration Error'),
        ('OTHER', 'Other'),
    ]

    INCIDENT_STATUS = [
        ('NEW', 'New'),
        ('INVESTIGATING', 'Investigating'),
        ('CONTAINED', 'Contained'),
        ('ERADICATED', 'Eradicated'),
        ('RECOVERING', 'Recovering'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]

    INCIDENT_SEVERITY = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    title = models.CharField(max_length=200)
    incident_type = models.CharField(max_length=30, choices=INCIDENT_TYPES)
    severity = models.CharField(max_length=10, choices=INCIDENT_SEVERITY)
    status = models.CharField(max_length=15, choices=INCIDENT_STATUS, default='NEW')
    
    # Description and Impact
    description = models.TextField()
    impact_assessment = models.TextField(blank=True)
    affected_systems = models.JSONField(default=list, blank=True)
    affected_users = models.JSONField(default=list, blank=True)
    
    # Discovery and Response
    discovered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='discovered_incidents')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assigned_incidents')
    
    # Timeline
    discovered_at = models.DateTimeField(default=timezone.now)
    reported_at = models.DateTimeField(default=timezone.now)
    contained_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Resolution Details
    resolution_summary = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    preventive_measures = models.TextField(blank=True)
    
    # Related Security Events
    related_events = models.ManyToManyField(SecurityEvent, blank=True, related_name='related_incidents')
    
    # Metadata
    case_number = models.CharField(max_length=50, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_incidents')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['incident_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['case_number']),
        ]

    def __str__(self):
        return f"{self.case_number}: {self.title}"

    def save(self, *args, **kwargs):
        """Generate case number if not provided."""
        if not self.case_number:
            # Generate case number format: SEC-YYYY-NNNN
            year = timezone.now().year
            count = SecurityIncident.objects.filter(
                created_at__year=year
            ).count() + 1
            self.case_number = f"SEC-{year}-{count:04d}"
        super().save(*args, **kwargs)

    @property
    def age_in_hours(self):
        """Get incident age in hours."""
        return int((timezone.now() - self.discovered_at).total_seconds() / 3600)


class SecurityDashboard(models.Model):
    """
    Model for storing security dashboard configurations and metrics.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Dashboard Configuration
    widgets = models.JSONField(default=list, help_text='Dashboard widget configurations')
    layout = models.JSONField(default=dict, help_text='Dashboard layout configuration')
    refresh_interval = models.PositiveIntegerField(default=300, help_text='Refresh interval in seconds')
    
    # Permissions
    is_public = models.BooleanField(default=False, help_text='Whether dashboard is publicly accessible')
    allowed_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='accessible_dashboards')
    allowed_roles = models.JSONField(default=list, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_security_dashboards')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

