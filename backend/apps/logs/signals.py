"""
Log signals for IT Management Platform.
Handles automatic activity logging and audit trail creation.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.conf import settings
import logging

from .models import ActivityLog, AuditLog, SystemLog, SecurityEvent, LogAlert, LogAlertTrigger
from apps.users.models import User

UserModel = get_user_model()
logger = logging.getLogger(__name__)

@receiver(post_save, sender=UserModel)
def log_user_changes(sender, instance, created, **kwargs):
    """
    Create audit log for user changes.
    """
    if created:
        # Log user creation
        ActivityLog.objects.create(
            user=instance,
            action='CREATE',
            level='INFO',
            title=f'User account created',
            description=f'New user account created for {instance.username}',
            model_name='User',
            object_id=instance.id,
            object_repr=str(instance),
            ip_address=None,  # Will be set by middleware if available
        )
    else:
        # Log significant user changes
        try:
            old_instance = UserModel.objects.get(pk=instance.pk)
            changes = []
            
            # Check for important field changes
            if old_instance.is_active != instance.is_active:
                changes.append(f'active status: {old_instance.is_active} -> {instance.is_active}')
            
            if old_instance.role != instance.role:
                changes.append(f'role: {old_instance.role} -> {instance.role}')
            
            if old_instance.email != instance.email:
                changes.append('email address changed')
            
            if old_instance.is_superuser != instance.is_superuser:
                changes.append(f'superuser status: {old_instance.is_superuser} -> {instance.is_superuser}')
            
            if changes:
                ActivityLog.objects.create(
                    user=instance if instance.is_authenticated else None,
                    action='UPDATE',
                    level='INFO',
                    title='User profile updated',
                    description=f'User profile changes: {", ".join(changes)}',
                    model_name='User',
                    object_id=instance.id,
                    object_repr=str(instance),
                    ip_address=None,
                )
                
                # Create audit log for sensitive changes
                if 'role' in changes or 'superuser' in changes:
                    AuditLog.objects.create(
                        user=instance if instance.is_authenticated else None,
                        action='ROLE_CHANGE',
                        risk_level='HIGH',
                        model_name='User',
                        object_id=instance.id,
                        object_repr=str(instance),
                        changes_summary=f'Role/superuser changes: {", ".join(changes)}',
                        ip_address=None,
                    )
        except UserModel.DoesNotExist:
            pass

@receiver(post_delete, sender=UserModel)
def log_user_deletion(sender, instance, **kwargs):
    """
    Create audit log for user deletion.
    """
    AuditLog.objects.create(
        user=None,  # System deletion
        action='DELETE',
        risk_level='CRITICAL',
        model_name='User',
        object_id=instance.id,
        object_repr=str(instance),
        changes_summary=f'User account deleted: {instance.username}',
        ip_address=None,
    )

@receiver(post_save, sender=UserModel)
def log_login_activity(sender, instance, created, **kwargs):
    """
    Log user login activity.
    """
    # This would typically be triggered by a login signal or middleware
    # For now, we'll check if last_login has changed significantly
    if not created and hasattr(instance, '_login_detected'):
        ActivityLog.objects.create(
            user=instance,
            action='LOGIN',
            level='INFO',
            title='User login',
            description=f'User {instance.username} logged in',
            model_name='User',
            object_id=instance.id,
            object_repr=str(instance),
            ip_address=getattr(instance, '_last_login_ip', None),
        )

@receiver(post_save)
def log_model_changes(sender, instance, created, **kwargs):
    """
    Generic signal to log model changes across the system.
    """
    # Skip if this is a log model to avoid infinite recursion
    if sender.__name__ in ['ActivityLog', 'AuditLog', 'SystemLog', 'SecurityEvent']:
        return
    
    # Skip if no user is associated (system operations)
    if not hasattr(instance, 'created_by') and not hasattr(instance, 'updated_by'):
        return
    
    user = getattr(instance, 'created_by', None) or getattr(instance, 'updated_by', None)
    if not user or not user.is_authenticated:
        return
    
    if created:
        # Log creation
        ActivityLog.objects.create(
            user=user,
            action='CREATE',
            level='INFO',
            title=f'{sender.__name__} created',
            description=f'New {sender.__name__} created: {str(instance)[:100]}',
            model_name=sender.__name__,
            object_id=instance.id,
            object_repr=str(instance)[:255],
            ip_address=None,  # Will be set by middleware
        )
        
        # Create audit log for sensitive models
        if sender.__name__ in ['User', 'Project', 'Ticket']:
            AuditLog.objects.create(
                user=user,
                action='CREATE',
                risk_level='MEDIUM',
                model_name=sender.__name__,
                object_id=instance.id,
                object_repr=str(instance)[:255],
                changes_summary=f'New {sender.__name__} created',
                ip_address=None,
            )
    else:
        # Log updates for significant changes
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            changes = []
            
            # Compare important fields
            for field in instance._meta.fields:
                if field.name in ['name', 'title', 'status', 'priority', 'assigned_to', 'is_active']:
                    old_value = getattr(old_instance, field.name)
                    new_value = getattr(instance, field.name)
                    if old_value != new_value:
                        changes.append(f'{field.name}: {old_value} -> {new_value}')
            
            if changes:
                ActivityLog.objects.create(
                    user=user,
                    action='UPDATE',
                    level='INFO',
                    title=f'{sender.__name__} updated',
                    description=f'{sender.__name__} changes: {", ".join(changes)}',
                    model_name=sender.__name__,
                    object_id=instance.id,
                    object_repr=str(instance)[:255],
                    ip_address=None,
                )
                
                # Create audit log for sensitive changes
                if sender.__name__ in ['User', 'Project', 'Ticket'] and any(field in changes for field in ['status', 'priority', 'assigned_to']):
                    AuditLog.objects.create(
                        user=user,
                        action='UPDATE',
                        risk_level='MEDIUM',
                        model_name=sender.__name__,
                        object_id=instance.id,
                        object_repr=str(instance)[:255],
                        changes_summary=f'Changes: {", ".join(changes)}',
                        ip_address=None,
                    )
        except sender.DoesNotExist:
            pass

@receiver(post_delete)
def log_model_deletions(sender, instance, **kwargs):
    """
    Generic signal to log model deletions.
    """
    # Skip Django's built-in models (like Session) that don't have id attribute
    if not hasattr(instance, 'id'):
        return
    
    # Skip if this is a log model to avoid infinite recursion
    if sender.__name__ in ['ActivityLog', 'AuditLog', 'SystemLog', 'SecurityEvent', 'LogAlert', 'LogAlertTrigger']:
        return
    
    # Skip Django's built-in models
    if sender.__module__ == 'django.contrib.sessions.models':
        return
    
    # Get user from the instance if possible
    user = getattr(instance, 'updated_by', None) or getattr(instance, 'created_by', None)
    
    try:
        ActivityLog.objects.create(
            user=user,
            action='DELETE',
            level='WARNING',
            title=f'{sender.__name__} deleted',
            description=f'{sender.__name__} deleted: {str(instance)[:100]}',
            model_name=sender.__name__,
            object_id=instance.id,
            object_repr=str(instance)[:255],
            ip_address=None,
        )
        
        # Create audit log for sensitive deletions
        if sender.__name__ in ['User', 'Project', 'Ticket']:
            AuditLog.objects.create(
                user=user,
                action='DELETE',
                risk_level='HIGH',
                model_name=sender.__name__,
                object_id=instance.id,
                object_repr=str(instance)[:255],
                changes_summary=f'{sender.__name__} deleted',
                ip_address=None,
            )
    except Exception as e:
        # Log the error but don't crash the deletion process
        logger.error(f"Error logging deletion for {sender.__name__}: {e}")

def trigger_alert(alert, matching_logs):
    """
    Trigger an alert with matching logs.
    """
    trigger = LogAlertTrigger.objects.create(
        alert=alert,
        matching_logs_count=len(matching_logs),
        matching_logs_sample=[{
            'id': log.id,
            'title': log.title,
            'timestamp': log.timestamp.isoformat(),
            'user': log.user.username if log.user else None
        } for log in matching_logs[:10]]  # Store first 10 as sample
    )
    
    # Update alert stats
    alert.last_triggered = timezone.now()
    alert.trigger_count += 1
    alert.save()
    
    logger.info(f"Alert triggered: {alert.name} with {len(matching_logs)} matching logs")

def cleanup_old_logs():
    """
    Clean up old logs based on retention policies.
    """
    from .models import LogRetention
    
    retention_policies = LogRetention.objects.filter(is_active=True)
    
    for policy in retention_policies:
        cutoff_date = timezone.now() - timezone.timedelta(days=policy.retention_days)
        
        if policy.log_type == 'ACTIVITY':
            ActivityLog.objects.filter(timestamp__lt=cutoff_date).delete()
        elif policy.log_type == 'AUDIT':
            AuditLog.objects.filter(timestamp__lt=cutoff_date).delete()
        elif policy.log_type == 'SYSTEM':
            SystemLog.objects.filter(timestamp__lt=cutoff_date).delete()
        elif policy.log_type == 'SECURITY':
            SecurityEvent.objects.filter(detected_at__lt=cutoff_date).delete()
        elif policy.log_type == 'ALL':
            ActivityLog.objects.filter(timestamp__lt=cutoff_date).delete()
            AuditLog.objects.filter(timestamp__lt=cutoff_date).delete()
            SystemLog.objects.filter(timestamp__lt=cutoff_date).delete()
            SecurityEvent.objects.filter(detected_at__lt=cutoff_date).delete()
        
        policy.last_run = timezone.now()
        policy.save()
        
        logger.info(f"Cleaned up logs for policy: {policy.name}")

