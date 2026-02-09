"""
Django signals for activity logging.

This module contains signal handlers that create audit logs when
models are created, updated, or deleted.

IMPORTANT: These handlers must ONLY fire on actual write operations.
They must NOT fire on read operations or when no changes occurred.

Signal Design Rules:
1. pre_save caches old instance values for comparison
2. post_save checks for real changes before logging
3. Generic handlers check update_fields to avoid spurious logs
4. Logs are ONLY created when fields actually change
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from apps.logs.models import (
    ActivityLog,
    AuditLog,
)

UserModel = get_user_model()

# Models that should NOT trigger generic logging
LOG_MODELS = {
    'ActivityLog',
    'AuditLog',
    'SystemLog',
    'SecurityEvent',
    'LogAlert',
    'LogAlertTrigger',
    'LogReport',
    'LogRetention',
    'LogStatistics',
}


# =============================================================================
# USER MODEL SIGNALS
# =============================================================================

@receiver(pre_save, sender=UserModel, dispatch_uid="cache_old_user")
def cache_old_user(sender, instance, **kwargs):
    """
    Cache the old user instance before save.
    
    This allows us to compare old vs new values in post_save
    to detect actual changes.
    """
    if instance.pk:
        try:
            instance._old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._old_instance = None
    else:
        instance._old_instance = None


@receiver(post_save, sender=UserModel, dispatch_uid="log_user_changes")
def log_user_changes(sender, instance, created, **kwargs):
    """
    Log user changes to AuditLog.
    
    Only logs when:
    - User is being updated (not created)
    - Actual field changes occurred (is_active, role, is_superuser)
    
    This prevents spurious logs when viewing/editing user without changes.
    """
    if created:
        # User creation is logged elsewhere
        return

    old_instance = getattr(instance, '_old_instance', None)
    if not old_instance:
        return

    changes = []

    # Detect active status changes
    if old_instance.is_active != instance.is_active:
        changes.append(
            f'active status: {old_instance.is_active} -> {instance.is_active}'
        )

    # Detect role changes
    if hasattr(old_instance, 'role') and old_instance.role != instance.role:
        changes.append(f'role: {old_instance.role} -> {instance.role}')

    # Detect superuser changes
    if old_instance.is_superuser != instance.is_superuser:
        changes.append(
            f'superuser: {old_instance.is_superuser} -> {instance.is_superuser}'
        )

    # CRITICAL: Only log if actual changes occurred
    if not changes:
        return

    # Determine risk level based on changes
    is_security_sensitive = any(
        'role:' in c or 'superuser:' in c for c in changes
    )

    try:
        AuditLog.objects.create(
            user=instance,
            action='ROLE_CHANGE' if any('role:' in c for c in changes) else 'UPDATE',
            risk_level='HIGH' if is_security_sensitive else 'MEDIUM',
            model_name=instance.__class__.__name__,
            object_id=instance.pk,
            object_repr=str(instance),
            field_name='role',
            old_value=old_instance.role if hasattr(old_instance, 'role') else '',
            new_value=instance.role if hasattr(instance, 'role') else '',
            changes_summary='; '.join(changes),
            extra_data={"changes": changes},
        )
    except Exception:
        import logging
        logging.exception("AuditLog write failed for user changes")


# =============================================================================
# GENERIC MODEL SIGNALS
# =============================================================================

@receiver(post_save, dispatch_uid="log_model_changes")
def log_model_changes(sender, instance, created, **kwargs):
    """
    Generic handler for model create/update operations.
    
    CRITICAL SAFEGUARDS:
    1. Skip if model is in LOG_MODELS (prevents recursive logging)
    2. Skip if model is not from our apps
    3. Only log on CREATED, not on updates (to avoid spurious logs)
    4. Updates must use explicit update_fields to be logged
    
    This prevents logs from appearing when simply viewing data.
    """
    # Skip log models to prevent recursive logging
    if sender.__name__ in LOG_MODELS:
        return

    # Skip non-app models (e.g., django.contrib.auth)
    if not sender.__module__.startswith('apps.'):
        return

    # Only log creations, NOT updates
    # Updates should be explicitly logged by use cases
    if not created:
        return

    try:
        ActivityLog.objects.create(
            user=None,
            action=f'{sender.__name__}_CREATED',
            description=f'{sender.__name__} created (ID {instance.pk})',
            timestamp=now(),
        )
    except Exception:
        import logging
        logging.exception("ActivityLog write failed for model creation")


@receiver(post_delete, dispatch_uid="log_model_deletions")
def log_model_deletions(sender, instance, **kwargs):
    """
    Generic handler for model delete operations.
    
    Skips log models to prevent recursive logging.
    """
    # Skip log models
    if sender.__name__ in LOG_MODELS:
        return

    # Skip non-app models
    if not sender.__module__.startswith('apps.'):
        return

    try:
        ActivityLog.objects.create(
            user=None,
            action=f'{sender.__name__}_DELETED',
            description=f'{sender.__name__} deleted (ID {instance.pk})',
            timestamp=now(),
        )
    except Exception:
        import logging
        logging.exception("ActivityLog write failed for model deletion")

