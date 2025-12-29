"""
Security utilities for IT Management Platform.
Input validation, sanitization, and security helpers.
"""

import re
import hashlib
import secrets
import string
from django.core.validators import validate_email, RegexValidator
from django.core.exceptions import ValidationError
from django.utils.html import escape
from django.conf import settings
from django.core.cache import cache


def get_client_ip(request):
    """
    Get client IP address from request.
    Handles X-Forwarded-For header for proxied requests.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


class SecurityValidator:
    """
    Collection of security validation utilities.
    """
    
    # Dangerous patterns to check for
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # XSS attempts
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',  # Event handlers
        r'<!--.*?-->',  # HTML comments
        r'<\?php',  # PHP code injection
        r'<%\s*=',  # ASP code injection
        r'\$\{',  # Template injection
        r'\$\(',  # Function call injection
        r'eval\s*\(',  # Eval function calls
        r'exec\s*\(',  # Exec function calls
        r'system\s*\(',  # System calls
        r'shell_exec\s*\(',  # Shell exec calls
    ]
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(\b(OR|AND)\s+[\'"]?\d+[\'"]?\s*[=<>])',
        r'(\b(OR|AND)\s+[\'"]?[\w\s]+[\'"]?\s*[=<>])',
        r'(\b(OR|AND)\s+1=1\b)',
        r'(\b(OR|AND)\s+[\'"]\s*[\'"]\b)',
        r'(\b(UNION\s+SELECT)\b)',
        r'(\b(LOAD_FILE|INTO\s+OUTFILE)\b)',
    ]
    
    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\./',  # Directory traversal
        r'\.\.\\',  # Windows directory traversal
        r'/%2e%2e/',  # URL encoded traversal
        r'/%2e%2e%2f',  # URL encoded traversal
    ]
    
    # File upload patterns
    DANGEROUS_FILE_EXTENSIONS = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr',
        '.vbs', '.js', '.jar', '.sh', '.ps1', '.dll',
        '.php', '.asp', '.aspx', '.jsp', '.py', '.rb'
    ]
    
    @classmethod
    def sanitize_html(cls, html_content):
        """
        Sanitize HTML content to prevent XSS attacks.
        """
        if not html_content:
            return html_content
        
        # Remove dangerous patterns
        sanitized = html_content
        for pattern in cls.DANGEROUS_PATTERNS:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        
        # Use Django's built-in HTML escaping
        return escape(sanitized)
    
    @classmethod
    def validate_input(cls, content):
        """
        Validate input for dangerous content.
        """
        if not content:
            return True, "Valid input"
        
        content_str = str(content)
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, content_str, re.IGNORECASE | re.DOTALL):
                return False, f"Dangerous pattern detected: {pattern}"
        
        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, content_str, re.IGNORECASE):
                return False, f"Potential SQL injection detected: {pattern}"
        
        # Check for path traversal attempts
        for pattern in cls.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, content_str, re.IGNORECASE):
                return False, f"Path traversal attempt detected: {pattern}"
        
        return True, "Input is valid"
    
    @classmethod
    def validate_file_upload(cls, file_obj):
        """
        Validate uploaded files for security.
        """
        if not file_obj:
            return True, "No file provided"
        
        file_name = file_obj.name.lower()
        file_size = file_obj.size
        
        # Check file size (10MB limit)
        max_size = getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)
        if file_size > max_size:
            return False, f"File size exceeds maximum allowed size ({max_size} bytes)"
        
        # Check file extension
        for dangerous_ext in cls.DANGEROUS_FILE_EXTENSIONS:
            if file_name.endswith(dangerous_ext):
                return False, f"File type not allowed: {dangerous_ext}"
        
        # Check MIME type
        allowed_mime_types = getattr(settings, 'ALLOWED_MIME_TYPES', [
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain', 'text/csv',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        ])
        
        if file_obj.content_type not in allowed_mime_types:
            return False, f"MIME type not allowed: {file_obj.content_type}"
        
        return True, "File is valid"
    
    @classmethod
    def validate_email_address(cls, email):
        """
        Validate email address format.
        """
        try:
            validate_email(email)
            return True, "Valid email address"
        except ValidationError:
            return False, "Invalid email address format"
    
    @classmethod
    def validate_username(cls, username):
        """
        Validate username for security.
        """
        if not username:
            return False, "Username is required"
        
        if len(username) < 3:
            return False, "Username must be at least 3 characters long"
        
        if len(username) > 30:
            return False, "Username must not exceed 30 characters"
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            return False, "Username contains invalid characters"
        
        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, username, re.IGNORECASE):
                return False, "Username contains dangerous content"
        
        return True, "Valid username"
    
    @classmethod
    def validate_password_strength(cls, password):
        """
        Validate password strength.
        """
        if not password:
            return False, "Password is required"
        
        issues = []
        
        if len(password) < 8:
            issues.append("Password must be at least 8 characters long")
        
        if not re.search(r'[a-z]', password):
            issues.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'[A-Z]', password):
            issues.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'\d', password):
            issues.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            issues.append("Password must contain at least one special character")
        
        # Check for common patterns
        common_patterns = ['123456', 'password', 'qwerty', 'admin', 'test']
        for pattern in common_patterns:
            if pattern in password.lower():
                issues.append("Password contains common patterns")
        
        if issues:
            return False, "; ".join(issues)
        
        return True, "Strong password"
    
    @classmethod
    def generate_secure_token(cls, length=32):
        """
        Generate a secure random token.
        """
        return secrets.token_urlsafe(length)
    
    @classmethod
    def hash_data(cls, data, salt=None):
        """
        Hash data with optional salt using SHA-256.
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if isinstance(salt, str):
            salt = salt.encode('utf-8')
        
        hash_obj = hashlib.sha256(salt + data)
        return hash_obj.hexdigest(), salt.hex() if isinstance(salt, bytes) else salt
    
    @classmethod
    def mask_sensitive_data(cls, data, mask_char='*', show_chars=4):
        """
        Mask sensitive data like passwords or credit card numbers.
        """
        if not data:
            return data
        
        data_str = str(data)
        if len(data_str) <= show_chars:
            return mask_char * len(data_str)
        
        return data_str[:show_chars] + mask_char * (len(data_str) - show_chars)


class SecuritySettings:
    """
    Configuration for security settings.
    """
    
    @staticmethod
    def get_rate_limit_config():
        """
        Get rate limiting configuration.
        """
        return {
            'enabled': getattr(settings, 'RATE_LIMIT_ENABLED', True),
            'requests_per_minute': getattr(settings, 'RATE_LIMIT_REQUESTS_PER_MINUTE', 60),
            'requests_per_hour': getattr(settings, 'RATE_LIMIT_REQUESTS_PER_HOUR', 1000),
            'requests_per_day': getattr(settings, 'RATE_LIMIT_REQUESTS_PER_DAY', 10000),
        }
    
    @staticmethod
    def get_cache_config():
        """
        Get cache configuration for security.
        """
        return {
            'default_timeout': getattr(settings, 'CACHE_DEFAULT_TIMEOUT', 300),
            'lockout_timeout': getattr(settings, 'LOCKOUT_TIMEOUT', 900),
            'session_timeout': getattr(settings, 'SESSION_TIMEOUT', 3600),
        }
    
    @staticmethod
    def get_validation_config():
        """
        Get input validation configuration.
        """
        return {
            'max_input_length': getattr(settings, 'MAX_INPUT_LENGTH', 10000),
            'allowed_file_types': getattr(settings, 'ALLOWED_FILE_TYPES', [
                'jpg', 'jpeg', 'png', 'gif', 'webp', 'pdf', 'txt', 'csv', 'docx', 'xlsx', 'pptx'
            ]),
            'max_file_size': getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024),
        }


class SecurityLogger:
    """
    Security event logging utility.
    """
    
    @staticmethod
    def log_security_event(event_type, details, user=None, ip_address=None):
        """
        Log security events for monitoring.
        """
        import logging
        logger = logging.getLogger('it_management_platform.security')
        
        log_data = {
            'event_type': event_type,
            'details': details,
            'user': str(user) if user else 'Anonymous',
            'ip_address': ip_address,
            'timestamp': secrets.token_hex(8)  # For anonymization
        }
        
        logger.warning(f"Security Event: {log_data}")
    
    @staticmethod
    def log_failed_login(username, ip_address, reason="Invalid credentials"):
        """
        Log failed login attempts.
        """
        SecurityLogger.log_security_event('FAILED_LOGIN', {
            'username': username,
            'reason': reason
        }, ip_address=ip_address)
    
    @staticmethod
    def log_successful_login(username, ip_address):
        """
        Log successful login attempts.
        """
        SecurityLogger.log_security_event('SUCCESSFUL_LOGIN', {
            'username': username
        }, user=username, ip_address=ip_address)
    
    @staticmethod
    def log_rate_limit_exceeded(ip_address, limit_type):
        """
        Log rate limit violations.
        """
        SecurityLogger.log_security_event('RATE_LIMIT_EXCEEDED', {
            'limit_type': limit_type
        }, ip_address=ip_address)
    
    @staticmethod
    def log_suspicious_activity(user, activity, ip_address):
        """
        Log suspicious activities.
        """
        SecurityLogger.log_security_event('SUSPICIOUS_ACTIVITY', {
            'activity': activity
        }, user=user, ip_address=ip_address)

