"""
Security signals for IT Management Platform.
Handles automatic logging of security events and audit trails.
"""

from django.db.models.signals import post_save, pre_save, pre_delete, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.core.cache import cache
from django.http import HttpRequest
import json
import logging

from .models import SecurityEvent, AuditLog, SecurityIncident
from .utils import SecurityLogger, SecurityValidator, get_client_ip

# Configure logger
logger = logging.getLogger('it_management_platform.security')


# Authentication Signals
@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    """
    Log successful login attempts.
    """
    try:
        # Get client IP address
        ip_address = get_client_ip(request) if hasattr(request, 'META') else None
        
        # Create security event
        SecurityEvent.objects.create(
            event_type='LOGIN_SUCCESS',
            severity='LOW',
            title=f'Successful login for user {user.username}',
            description=f'User {user.username} logged in successfully',
            user=user,
            username=user.username,
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            referer=request.META.get('HTTP_REFERER', ''),
            request_method='POST',
            request_path=request.path,
            session_id=request.session.session_key or '',
            additional_data={
                'login_time': timezone.now().isoformat(),
                'session_key': request.session.session_key,
            }
        )
        
        # Log to audit trail
        AuditLog.objects.create(
            action='LOGIN',
            resource_type='user_session',
            resource_id=str(user.id),
            resource_name=f'Login session for {user.username}',
            user=user,
            username=user.username,
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            session_id=request.session.session_key or '',
            description=f'User {user.username} logged in successfully',
            success=True
        )
        
        # Update last activity
        request.session['last_activity'] = timezone.now().timestamp()
        
        # Clear any failed login attempts
        cache_key = f'failed_login_{ip_address}'
        cache.delete(cache_key)
        
        # Log with utility
        SecurityLogger.log_successful_login(user.username, ip_address)
        
    except Exception as e:
        logger.error(f"Error logging successful login: {str(e)}")


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    """
    Log failed login attempts.
    """
    try:
        # Get client IP address
        ip_address = get_client_ip(request) if hasattr(request, 'META') else None
        
        # Determine severity based on number of failed attempts
        failed_attempts = cache.get(f'failed_login_{ip_address}', 0)
        severity = 'MEDIUM' if failed_attempts >= 3 else 'LOW'
        
        # Create security event
        SecurityEvent.objects.create(
            event_type='LOGIN_FAILURE',
            severity=severity,
            title=f'Failed login attempt for {credentials.get("username", "unknown")}',
            description=f'Failed login attempt for username: {credentials.get("username", "unknown")}',
            username=credentials.get('username', 'unknown'),
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            referer=request.META.get('HTTP_REFERER', ''),
            request_method='POST',
            request_path=request.path,
            session_id=request.session.session_key or '',
            additional_data={
                'failed_attempts': failed_attempts + 1,
                'login_time': timezone.now().isoformat(),
            }
        )
        
        # Log to audit trail
        AuditLog.objects.create(
            action='LOGIN',
            resource_type='user_session',
            resource_id='0',
            resource_name=f'Failed login for {credentials.get("username", "unknown")}',
            username=credentials.get('username', 'unknown'),
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            session_id=request.session.session_key or '',
            description=f'Failed login attempt for {credentials.get("username", "unknown")}',
            success=False,
            error_message='Invalid credentials'
        )
        
        # Track failed login attempts for rate limiting
        cache_key = f'failed_login_{ip_address}'
        cache.set(cache_key, failed_attempts + 1, 900)  # 15 minutes
        
        # Check for potential brute force attack
        if failed_attempts + 1 >= 5:
            # Create high severity event for potential brute force
            SecurityEvent.objects.create(
                event_type='SUSPICIOUS_ACTIVITY',
                severity='HIGH',
                title=f'Potential brute force attack from {ip_address}',
                description=f'Multiple failed login attempts detected from IP {ip_address}',
                username=credentials.get('username', 'unknown'),
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                request_method='POST',
                request_path=request.path,
                additional_data={
                    'failed_attempts': failed_attempts + 1,
                    'attack_type': 'brute_force',
                }
            )
        
        # Log with utility
        SecurityLogger.log_failed_login(
            credentials.get('username', 'unknown'), 
            ip_address, 
            'Invalid credentials'
        )
        
    except Exception as e:
        logger.error(f"Error logging failed login: {str(e)}")


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Log user logout events.
    """
    try:
        # Get client IP address
        ip_address = get_client_ip(request) if hasattr(request, 'META') else None
        
        # Create security event
        SecurityEvent.objects.create(
            event_type='LOGOUT',
            severity='LOW',
            title=f'User logout for {user.username}',
            description=f'User {user.username} logged out',
            user=user,
            username=user.username,
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            referer=request.META.get('HTTP_REFERER', ''),
            request_method='POST',
            request_path=request.path,
            session_id=request.session.session_key or '',
            additional_data={
                'logout_time': timezone.now().isoformat(),
                'session_duration': request.session.get('last_activity'),
            }
        )
        
        # Log to audit trail
        AuditLog.objects.create(
            action='LOGOUT',
            resource_type='user_session',
            resource_id=str(user.id),
            resource_name=f'Logout session for {user.username}',
            user=user,
            username=user.username,
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            session_id=request.session.session_key or '',
            description=f'User {user.username} logged out',
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error logging user logout: {str(e)}")


# Model Change Signals
@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """
    Log user creation and modification events.
    """
    try:
        # Get current user from context if available
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        
        # Try to get the user who made the change
        current_user = getattr(instance, '_current_user', None)
        
        if created:
            # User creation event
            SecurityEvent.objects.create(
                event_type='SECURITY_VIOLATION',  # User creation could be security relevant
                severity='MEDIUM',
                title=f'New user account created: {instance.username}',
                description=f'New user account created for {instance.username}',
                user=current_user,
                username=current_user.username if current_user else 'system',
                ip_address=None,  # Would need to be passed in context
                additional_data={
                    'new_user_id': instance.id,
                    'new_user_username': instance.username,
                    'new_user_email': instance.email,
                    'new_user_is_active': instance.is_active,
                    'new_user_is_staff': instance.is_staff,
                    'new_user_is_superuser': instance.is_superuser,
                    'action': 'create',
                }
            )
            
            # Audit log entry
            AuditLog.objects.create(
                action='CREATE',
                resource_type='user',
                resource_id=str(instance.id),
                resource_name=f'User account: {instance.username}',
                user=current_user,
                username=current_user.username if current_user else 'system',
                description=f'Created new user account for {instance.username}',
                success=True,
                additional_data={
                    'user_email': instance.email,
                    'user_is_active': instance.is_active,
                    'user_is_staff': instance.is_staff,
                    'user_is_superuser': instance.is_superuser,
                }
            )
            
        else:
            # User modification event - track significant changes
            # This would require storing old values, which is complex
            # For now, log significant role changes
            if hasattr(instance, '_changed_fields'):
                changed_fields = getattr(instance, '_changed_fields', [])
                
                if any(field in changed_fields for field in ['is_active', 'is_staff', 'is_superuser']):
                    SecurityEvent.objects.create(
                        event_type='SECURITY_VIOLATION',
                        severity='MEDIUM',
                        title=f'User account modified: {instance.username}',
                        description=f'User account properties modified for {instance.username}',
                        user=current_user,
                        username=current_user.username if current_user else 'system',
                        additional_data={
                            'modified_user_id': instance.id,
                            'modified_user_username': instance.username,
                            'changed_fields': changed_fields,
                            'action': 'modify',
                        }
                    )
    
    except Exception as e:
        logger.error(f"Error logging user changes: {str(e)}")


# Session Management Signals
@receiver(post_save, sender=Session)
def log_session_changes(sender, instance, created, **kwargs):
    """
    Log session creation and expiration events.
    """
    try:
        if created:
            # Session creation - could be part of login process
            pass  # This is typically handled by login signals
        
        # Session expiration is handled by session cleanup middleware
        # We can add logic here if needed
    
    except Exception as e:
        logger.error(f"Error logging session changes: {str(e)}")


# Custom Security Event Creation Signals
@receiver(post_save, sender=SecurityEvent)
def process_security_event_creation(sender, instance, created, **kwargs):
    """
    Process security event creation - could trigger alerts, etc.
    """
    try:
        if created:
            # Check for high/critical severity events that need immediate attention
            if instance.severity in ['HIGH', 'CRITICAL']:
                # Log the event for monitoring
                logger.warning(f"High/Critical Security Event: {instance.event_type} - {instance.title}")
                
                # Could trigger alerts here (email, SMS, etc.)
                # self._trigger_security_alert(instance)
                
                # Could update security dashboard metrics
                # self._update_dashboard_metrics(instance)
            
            # Log the event creation itself
            logger.info(f"Security Event Created: {instance.event_type} - {instance.title}")
    
    except Exception as e:
        logger.error(f"Error processing security event creation: {str(e)}")


@receiver(post_save, sender=SecurityIncident)
def process_security_incident_creation(sender, instance, created, **kwargs):
    """
    Process security incident creation.
    """
    try:
        if created:
            # Log incident creation
            logger.warning(f"Security Incident Created: {instance.case_number} - {instance.title}")
            
            # Could trigger incident response procedures
            # self._trigger_incident_response(instance)
            
            # Could notify security team
            # self._notify_security_team(instance)
    
    except Exception as e:
        logger.error(f"Error processing security incident creation: {str(e)}")


# Data Access Signals
@receiver(post_save)
def log_data_changes(sender, instance, created, **kwargs):
    """
    Generic signal to log data changes for audit purposes.
    This could be extended to log changes to specific models.
    """
    try:
        # Only log for specific models that need audit trails
        audit_models = [
            'user', 'asset', 'ticket', 'project'
        ]  # Add your models here
        
        model_name = sender._meta.model_name
        
        if model_name in audit_models and not created:
            # Get current user from context
            current_user = getattr(instance, '_current_user', None)
            
            if current_user:
                # Log the change
                AuditLog.objects.create(
                    action='UPDATE',
                    resource_type=model_name,
                    resource_id=str(instance.id),
                    resource_name=getattr(instance, 'name', str(instance)),
                    user=current_user,
                    username=current_user.username,
                    description=f'Updated {model_name}: {getattr(instance, "name", instance)}',
                    success=True,
                    additional_data={
                        'model_name': model_name,
                        'instance_id': instance.id,
                        'timestamp': timezone.now().isoformat(),
                    }
                )
    
    except Exception as e:
        logger.error(f"Error logging data changes: {str(e)}")


# Security Monitoring Signals
@receiver(post_delete)
def log_data_deletion(sender, instance, **kwargs):
    """
    Log data deletion events.
    """
    try:
        # Only log deletion for sensitive models
        sensitive_models = [
            'user', 'asset', 'ticket', 'project', 'securityevent', 'securityincident'
        ]  # Add your models here
        
        model_name = sender._meta.model_name
        
        if model_name in sensitive_models:
            # Get current user from context
            current_user = getattr(instance, '_current_user', None)
            
            # Create high severity security event for sensitive data deletion
            SecurityEvent.objects.create(
                event_type='SECURITY_VIOLATION',
                severity='HIGH',
                title=f'Sensitive data deletion: {model_name}',
                description=f'Deletion of {model_name} instance detected',
                user=current_user,
                username=current_user.username if current_user else 'unknown',
                additional_data={
                    'deleted_model': model_name,
                    'deleted_instance_id': instance.id,
                    'deleted_instance_name': getattr(instance, 'name', str(instance)),
                    'timestamp': timezone.now().isoformat(),
                }
            )
            
            # Log to audit trail
            AuditLog.objects.create(
                action='DELETE',
                resource_type=model_name,
                resource_id=str(instance.id),
                resource_name=getattr(instance, 'name', str(instance)),
                user=current_user,
                username=current_user.username if current_user else 'unknown',
                description=f'Deleted {model_name}: {getattr(instance, "name", instance)}',
                success=True,
                additional_data={
                    'model_name': model_name,
                    'instance_id': instance.id,
                    'timestamp': timezone.now().isoformat(),
                }
            )
    
    except Exception as e:
        logger.error(f"Error logging data deletion: {str(e)}")


# Utility functions that could be called by signals
def get_current_user():
    """
    Get the current user from thread local storage.
    This is a common pattern for getting the current user in signals.
    """
    from threading import local
    _thread_locals = local()
    return getattr(_thread_locals, 'user', None)


def set_current_user(user):
    """
    Set the current user in thread local storage.
    """
    from threading import local
    _thread_locals = local()
    _thread_locals.user = user


# Middleware integration
class SecuritySignalMiddleware:
    """
    Middleware to set the current user for signal processing.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Set current user
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)
        
        response = self.get_response(request)
        
        # Clear current user
        set_current_user(None)
        
        return response

