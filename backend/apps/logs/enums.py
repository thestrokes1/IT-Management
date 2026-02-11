"""
Enumeration types for Activity Logging.

Provides enums for activity levels, security event types,
and other logging-related constants.
"""

from enum import Enum


# =============================================================================
# Event Category Enums - Canonical Classification
# =============================================================================

class EventCategory(Enum):
    """
    Canonical event categories for structured logging.
    
    Each log entry MUST belong to exactly one category.
    This provides a unified way to classify and filter events.
    """
    ACTIVITY = 'ACTIVITY'      # User actions and workflow events
    SECURITY = 'SECURITY'      # Security-related events and incidents
    SYSTEM = 'SYSTEM'          # System-level events and errors
    AUDIT = 'AUDIT'            # Audit trail for sensitive operations
    ERROR = 'ERROR'            # Error and exception events
    
    @classmethod
    def choices(cls):
        """Return choices for Django model field."""
        return [(e.value, e.name.replace('_', ' ')) for e in cls]
    
    @classmethod
    def from_action(cls, action: str) -> 'EventCategory':
        """Infer category from legacy action type."""
        action_category_map = {
            'LOGIN': cls.ACTIVITY,
            'LOGOUT': cls.ACTIVITY,
            'CREATE': cls.ACTIVITY,
            'READ': cls.ACTIVITY,
            'UPDATE': cls.ACTIVITY,
            'DELETE': cls.ACTIVITY,
            'SEARCH': cls.ACTIVITY,
            'DOWNLOAD': cls.ACTIVITY,
            'UPLOAD': cls.ACTIVITY,
            'EXPORT': cls.ACTIVITY,
            'IMPORT': cls.ACTIVITY,
            'API_CALL': cls.ACTIVITY,
            'SYSTEM_ACTION': cls.SYSTEM,
            'SECURITY_EVENT': cls.SECURITY,
            'ERROR': cls.ERROR,
            'OTHER': cls.ACTIVITY,
        }
        return action_category_map.get(action, cls.ACTIVITY)
    
    @classmethod
    def from_level(cls, level: str) -> 'EventCategory':
        """Infer category from legacy level."""
        level_category_map = {
            'DEBUG': cls.SYSTEM,
            'INFO': cls.ACTIVITY,
            'WARNING': cls.SYSTEM,
            'ERROR': cls.ERROR,
            'CRITICAL': cls.ERROR,
        }
        return level_category_map.get(level, cls.ACTIVITY)
    
    @property
    def color_class(self) -> str:
        """Get Tailwind color class for display."""
        colors = {
            self.ACTIVITY: 'bg-blue-100 text-blue-800',
            self.SECURITY: 'bg-red-100 text-red-800',
            self.SYSTEM: 'bg-gray-100 text-gray-800',
            self.AUDIT: 'bg-purple-100 text-purple-800',
            self.ERROR: 'bg-orange-100 text-orange-800',
        }
        return colors.get(self, 'bg-gray-100 text-gray-800')

class ActivityLevel(Enum):
    """Log level enumeration for activity logs."""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'
    
    @classmethod
    def choices(cls):
        """Return choices for Django model field."""
        return [(e.value, e.name.replace('_', ' ')) for e in cls]
    
    @property
    def is_error(self) -> bool:
        """Check if this is an error level."""
        return self in [self.ERROR, self.CRITICAL]
    
    @property
    def is_warning(self) -> bool:
        """Check if this is a warning level."""
        return self == self.WARNING
    
    @property
    def is_info(self) -> bool:
        """Check if this is an info level."""
        return self == self.INFO


class ActivityAction(Enum):
    """Activity action enumeration."""
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    CREATE = 'CREATE'
    READ = 'READ'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    SEARCH = 'SEARCH'
    DOWNLOAD = 'DOWNLOAD'
    UPLOAD = 'UPLOAD'
    EXPORT = 'EXPORT'
    IMPORT = 'IMPORT'
    API_CALL = 'API_CALL'
    SYSTEM_ACTION = 'SYSTEM_ACTION'
    SECURITY_EVENT = 'SECURITY_EVENT'
    ERROR = 'ERROR'
    OTHER = 'OTHER'
    
    @classmethod
    def choices(cls):
        """Return choices for Django model field."""
        return [(e.value, e.name.replace('_', ' ')) for e in cls]


# =============================================================================
# Target Type Enums
# =============================================================================

class TargetType(Enum):
    """Target type enumeration for activities."""
    TICKET = 'TICKET'
    ASSET = 'ASSET'
    PROJECT = 'PROJECT'
    USER = 'USER'
    COMMENT = 'COMMENT'
    ATTACHMENT = 'ATTACHMENT'
    REPORT = 'REPORT'
    SYSTEM = 'SYSTEM'
    
    @classmethod
    def choices(cls):
        """Return choices for Django model field."""
        return [(e.value, e.name.replace('_', ' ')) for e in cls]


# =============================================================================
# Security Event Enums
# =============================================================================

class SecuritySeverity(Enum):
    """Security event severity enumeration."""
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'
    
    @classmethod
    def choices(cls):
        """Return choices for Django model field."""
        return [(e.value, e.name.replace('_', ' ')) for e in cls]
    
    @property
    def is_critical(self) -> bool:
        """Check if this is critical severity."""
        return self == self.CRITICAL
    
    @property
    def is_high(self) -> bool:
        """Check if this is high severity."""
        return self == self.HIGH
    
    @property
    def priority(self) -> int:
        """Get priority value (higher = more urgent)."""
        priority_map = {
            self.LOW: 1,
            self.MEDIUM: 2,
            self.HIGH: 3,
            self.CRITICAL: 4,
        }
        return priority_map.get(self, 0)


class SecurityStatus(Enum):
    """Security event status enumeration."""
    OPEN = 'OPEN'
    INVESTIGATING = 'INVESTIGATING'
    RESOLVED = 'RESOLVED'
    FALSE_POSITIVE = 'FALSE_POSITIVE'
    CLOSED = 'CLOSED'
    
    @classmethod
    def choices(cls):
        """Return choices for Django model field."""
        return [(e.value, e.name.replace('_', ' ')) for e in cls]
    
    @property
    def is_active(self) -> bool:
        """Check if this is an active status."""
        return self in [self.OPEN, self.INVESTIGATING]
    
    @property
    def is_resolved(self) -> bool:
        """Check if this is a resolved status."""
        return self in [self.RESOLVED, self.FALSE_POSITIVE, self.CLOSED]


class SecurityEventType(Enum):
    """Security event type enumeration."""
    FAILED_LOGIN = 'FAILED_LOGIN'
    BRUTE_FORCE = 'BRUTE_FORCE'
    UNAUTHORIZED_ACCESS = 'UNAUTHORIZED_ACCESS'
    PRIVILEGE_ESCALATION = 'PRIVILEGE_ESCALATION'
    DATA_BREACH = 'DATA_BREACH'
    MALWARE_DETECTION = 'MALWARE_DETECTION'
    SUSPICIOUS_ACTIVITY = 'SUSPICIOUS_ACTIVITY'
    POLICY_VIOLATION = 'POLICY_VIOLATION'
    UNAUTHORIZED_API_CALL = 'UNAUTHORIZED_API_CALL'
    SESSION_HIJACKING = 'SESSION_HIJACKING'
    SQL_INJECTION = 'SQL_INJECTION'
    XSS_ATTEMPT = 'XSS_ATTEMPT'
    CSRF_VIOLATION = 'CSRF_VIOLATION'
    FILE_UPLOAD_ABUSE = 'FILE_UPLOAD_ABUSE'
    OTHER = 'OTHER'
    
    @classmethod
    def choices(cls):
        """Return choices for Django model field."""
        return [(e.value, e.name.replace('_', ' ')) for e in cls]
    
    @classmethod
    def get_label(cls, event_type: str) -> str:
        """Get human-readable label for event type."""
        labels = {
            'FAILED_LOGIN': 'Failed Login Attempt',
            'BRUTE_FORCE': 'Brute Force Attack',
            'UNAUTHORIZED_ACCESS': 'Unauthorized Access',
            'PRIVILEGE_ESCALATION': 'Privilege Escalation',
            'DATA_BREACH': 'Data Breach',
            'MALWARE_DETECTION': 'Malware Detection',
            'SUSPICIOUS_ACTIVITY': 'Suspicious Activity',
            'POLICY_VIOLATION': 'Policy Violation',
            'UNAUTHORIZED_API_CALL': 'Unauthorized API Call',
            'SESSION_HIJACKING': 'Session Hijacking',
            'SQL_INJECTION': 'SQL Injection Attempt',
            'XSS_ATTEMPT': 'XSS Attempt',
            'CSRF_VIOLATION': 'CSRF Violation',
            'FILE_UPLOAD_ABUSE': 'File Upload Abuse',
            'OTHER': 'Other',
        }
        return labels.get(event_type, event_type.replace('_', ' '))
    
    @property
    def is_attack(self) -> bool:
        """Check if this is an attack type event."""
        return self in [
            self.BRUTE_FORCE, self.SQL_INJECTION, self.XSS_ATTEMPT,
            self.CSRF_VIOLATION, self.FILE_UPLOAD_ABUSE
        ]
    
    @property
    def is_access_violation(self) -> bool:
        """Check if this is an access violation event."""
        return self in [
            self.UNAUTHORIZED_ACCESS, self.PRIVILEGE_ESCALATION,
            self.SESSION_HIJACKING
        ]


# =============================================================================
# System Log Enums
# =============================================================================

class SystemLogLevel(Enum):
    """System log level enumeration."""
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'
    
    @classmethod
    def choices(cls):
        """Return choices for Django model field."""
        return [(e.value, e.name.replace('_', ' ')) for e in cls]


class SystemComponent(Enum):
    """System component enumeration."""
    DATABASE = 'DATABASE'
    AUTHENTICATION = 'AUTHENTICATION'
    API = 'API'
    EMAIL = 'EMAIL'
    FILE_SYSTEM = 'FILE_SYSTEM'
    MEMORY = 'MEMORY'
    CPU = 'CPU'
    NETWORK = 'NETWORK'
    SECURITY = 'SECURITY'
    BACKUP = 'BACKUP'
    MAINTENANCE = 'MAINTENANCE'
    INTEGRATION = 'INTEGRATION'
    OTHER = 'OTHER'
    
    @classmethod
    def choices(cls):
        """Return choices for Django model field."""
        return [(e.value, e.name.replace('_', ' ')) for e in cls]


# =============================================================================
# Audit Log Enums
# =============================================================================

class AuditAction(Enum):
    """Audit action enumeration."""
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    PASSWORD_CHANGE = 'PASSWORD_CHANGE'
    PERMISSION_CHANGE = 'PERMISSION_CHANGE'
    ROLE_CHANGE = 'ROLE_CHANGE'
    SECURITY_EVENT = 'SECURITY_EVENT'
    DATA_EXPORT = 'DATA_EXPORT'
    DATA_IMPORT = 'DATA_IMPORT'
    CONFIG_CHANGE = 'CONFIG_CHANGE'
    SYSTEM_ACCESS = 'SYSTEM_ACCESS'
    
    @classmethod
    def choices(cls):
        """Return choices for Django model field."""
        return [(e.value, e.name.replace('_', ' ')) for e in cls]


class AuditRiskLevel(Enum):
    """Audit risk level enumeration."""
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'
    
    @classmethod
    def choices(cls):
        """Return choices for Django model field."""
        return [(e.value, e.name.replace('_', ' ')) for e in cls]
    
    @property
    def is_high(self) -> bool:
        """Check if this is high or critical risk."""
        return self in [self.HIGH, self.CRITICAL]


# =============================================================================
# Helper Functions
# =============================================================================

def get_level_color(level: str) -> str:
    """Get color class for log level."""
    colors = {
        'DEBUG': 'text-gray-500',
        'INFO': 'text-blue-500',
        'WARNING': 'text-yellow-500',
        'ERROR': 'text-red-500',
        'CRITICAL': 'text-red-700',
    }
    return colors.get(level, 'text-gray-500')


def get_severity_color(severity: str) -> str:
    """Get color class for severity level."""
    colors = {
        'LOW': 'bg-blue-100 text-blue-800',
        'MEDIUM': 'bg-yellow-100 text-yellow-800',
        'HIGH': 'bg-orange-100 text-orange-800',
        'CRITICAL': 'bg-red-100 text-red-800',
    }
    return colors.get(severity, 'bg-gray-100 text-gray-800')


def get_status_color(status: str) -> str:
    """Get color class for status."""
    colors = {
        'OPEN': 'bg-red-100 text-red-800',
        'INVESTIGATING': 'bg-yellow-100 text-yellow-800',
        'RESOLVED': 'bg-green-100 text-green-800',
        'FALSE_POSITIVE': 'bg-gray-100 text-gray-800',
        'CLOSED': 'bg-gray-100 text-gray-600',
    }
    return colors.get(status, 'bg-gray-100 text-gray-800')
