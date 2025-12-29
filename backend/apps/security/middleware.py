"""
Security middleware for IT Management Platform.
Provides rate limiting, input validation, and security hardening.
"""

import time
import json
from collections import defaultdict
from django.core.cache import cache
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth.models import AnonymousUser


class RateLimitingMiddleware:
    """
    Middleware for rate limiting API requests.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Rate limiting configuration
        self.requests_per_minute = getattr(settings, 'RATE_LIMIT_REQUESTS_PER_MINUTE', 60)
        self.requests_per_hour = getattr(settings, 'RATE_LIMIT_REQUESTS_PER_HOUR', 1000)
        self.cache_timeout = 3600  # 1 hour
        self.allowed_paths = [
            '/admin/login/',
            '/frontend/login/',
            '/api/auth/',
        ]
    
    def __call__(self, request):
        # Check rate limits before processing the request
        response = self.process_request(request)
        if response is not None:
            return response
        
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        """
        Check rate limits before processing the request.
        """
        # Skip rate limiting for certain paths
        if any(path in request.path for path in self.allowed_paths):
            return None
        
        # Skip rate limiting for static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None
        
        # Get client IP
        client_ip = self.get_client_ip(request)
        
        # Check minute limit
        if self.is_rate_limited(client_ip, 'minute', self.requests_per_minute, 60):
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.',
                'retry_after': 60
            }, status=429)
        
        # Check hour limit
        if self.is_rate_limited(client_ip, 'hour', self.requests_per_hour, 3600):
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.',
                'retry_after': 3600
            }, status=429)
        
        return None
    
    def get_client_ip(self, request):
        """
        Get client IP address from request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_rate_limited(self, ip, period, limit, timeout):
        """
        Check if IP is rate limited for given period.
        """
        cache_key = f'rate_limit_{ip}_{period}'
        
        # Get current count
        current_count = cache.get(cache_key, 0)
        
        if current_count >= limit:
            return True
        
        # Increment counter
        cache.set(cache_key, current_count + 1, timeout)
        return False


class SecurityHeadersMiddleware:
    """
    Middleware for adding security headers to all responses.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return self.process_response(request, response)
    
    def process_response(self, request, response):
        """
        Add security headers to response.
        """
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "connect-src 'self';"
        )
        
        # Prevent clickjacking
        response['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # XSS Protection
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer Policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Feature Policy (deprecated but still useful)
        response['Permissions-Policy'] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=()"
        )
        
        return response


class InputValidationMiddleware:
    """
    Middleware for input validation and sanitization.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Dangerous patterns to check for
        self.dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS attempts
            r'javascript:',  # JavaScript URLs
            r'on\w+\s*=',  # Event handlers
            r'<!--.*?-->',  # HTML comments (potential injection)
            r'<\?php',  # PHP code injection
            r'<%\s*=',  # ASP code injection
            r'\$\{',  # Template injection
            r'\$\(',  # Function call injection
        ]
    
    def __call__(self, request):
        response = self.process_request(request)
        if response is not None:
            return response
        
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        """
        Validate and sanitize input data.
        """
        # Validate POST data
        if request.method == 'POST':
            if request.content_type == 'application/json':
                try:
                    data = json.loads(request.body.decode('utf-8'))
                    if self.contains_dangerous_content(str(data)):
                        return JsonResponse({
                            'error': 'Invalid input detected',
                            'message': 'Input contains potentially dangerous content.'
                        }, status=400)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    return JsonResponse({
                        'error': 'Invalid JSON',
                        'message': 'Request body contains invalid JSON.'
                    }, status=400)
            elif request.content_type == 'application/x-www-form-urlencoded':
                if self.contains_dangerous_content(str(request.POST)):
                    return JsonResponse({
                        'error': 'Invalid input detected',
                        'message': 'Input contains potentially dangerous content.'
                    }, status=400)
        
        # Validate query parameters
        if request.GET:
            if self.contains_dangerous_content(str(request.GET)):
                return JsonResponse({
                    'error': 'Invalid input detected',
                    'message': 'Query parameters contain potentially dangerous content.'
                }, status=400)
        
        return None
    
    def contains_dangerous_content(self, content):
        """
        Check if content contains dangerous patterns.
        """
        import re
        for pattern in self.dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
                return True
        return False


class AuthenticationTrackingMiddleware:
    """
    Middleware for tracking authentication attempts and session security.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_failed_attempts = 5
        self.lockout_duration = 900  # 15 minutes
        self.session_timeout = 3600  # 1 hour
    
    def __call__(self, request):
        response = self.process_request(request)
        if response is not None:
            return response
        
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        """
        Track authentication attempts and manage session security.
        """
        # Track failed login attempts
        if request.path in ['/admin/login/', '/frontend/login/', '/api/auth/login/']:
            if request.method == 'POST':
                self.track_failed_login(request)
        
        # Check session timeout
        if hasattr(request, 'user') and request.user.is_authenticated:
            if not self.is_session_valid(request):
                return JsonResponse({
                    'error': 'Session expired',
                    'message': 'Your session has expired. Please login again.'
                }, status=401)
        
        return None
    
    def track_failed_login(self, request):
        """
        Track failed login attempts and implement lockout.
        """
        ip = self.get_client_ip(request)
        cache_key = f'failed_login_{ip}'
        
        failed_attempts = cache.get(cache_key, 0)
        if failed_attempts >= self.max_failed_attempts:
            cache.set(f'locked_out_{ip}', True, self.lockout_duration)
            return JsonResponse({
                'error': 'Account locked',
                'message': 'Too many failed login attempts. Account temporarily locked.'
            }, status=429)
        
        # Don't increment counter here, let the view handle actual authentication
        return None
    
    def get_client_ip(self, request):
        """
        Get client IP address.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def is_session_valid(self, request):
        """
        Check if session is still valid.
        """
        last_activity = request.session.get('last_activity')
        if not last_activity:
            request.session['last_activity'] = time.time()
            return True
        
        current_time = time.time()
        if current_time - last_activity > self.session_timeout:
            request.session.flush()
            return False
        
        request.session['last_activity'] = current_time
        return True


class APILoggingMiddleware:
    """
    Middleware for logging API requests for security monitoring.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.process_request(request)
        if response is not None:
            return response
        
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        """
        Log API requests for security monitoring.
        """
        # Only log API requests
        if request.path.startswith('/api/'):
            self.log_api_request(request)
        return None
    
    def log_api_request(self, request):
        """
        Log API request details.
        """
        import logging
        logger = logging.getLogger('it_management_platform.api')
        
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
        ip = self.get_client_ip(request)
        
        log_data = {
            'timestamp': time.time(),
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': ip,
            'user': str(user) if user else 'Anonymous',
            'query_params': dict(request.GET),
        }
        
        # Only log sensitive operations in detail
        if request.method in ['POST', 'PUT', 'DELETE']:
            logger.info(f"API Request: {json.dumps(log_data)}")
        else:
            logger.debug(f"API Request: {json.dumps(log_data)}")
    
    def get_client_ip(self, request):
        """
        Get client IP address.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

