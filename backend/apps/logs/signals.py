from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from apps.logs.models import (
    ActivityLog,
    AuditLog,
    SystemLog,
    SecurityEvent,
    LogAlert,
    LogAlertTrigger,
    LogReport,
    LogRetention,
    LogStatistics,
)

UserModel = get_user_model()

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


@receiver(pre_save, sender=UserModel, dispatch_uid="cache_old_user")
def cache_old_user(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_instance = sender.objects.get(pk=instance.pk)
        except sender.DoesNotExist:
            instance._old_instance = None


@receiver(post_save, sender=UserModel, dispatch_uid="log_user_changes")
def log_user_changes(sender, instance, created, **kwargs):
    if created:
        return

    old_instance = getattr(instance, '_old_instance', None)
    if not old_instance:
        return

    changes = []

    if old_instance.is_active != instance.is_active:
        changes.append(
            f'active status: {old_instance.is_active} -> {instance.is_active}'
        )

    if hasattr(old_instance, 'role') and old_instance.role != instance.role:
        changes.append(f'role: {old_instance.role} -> {instance.role}')

    if old_instance.is_superuser != instance.is_superuser:
        changes.append(
            f'superuser: {old_instance.is_superuser} -> {instance.is_superuser}'
        )

    if not changes:
        return

    try:
            AuditLog.objects.create(
            user=instance,
            action='ROLE_CHANGE'
            if any('role:' in c for c in changes)
            else 'UPDATE',

            risk_level=(
                'HIGH'
                if any('role:' in c or 'superuser:' in c for c in changes)
                else 'MEDIUM'
            ),

            # REQUIRED BY MODEL
            model_name=instance.__class__.__name__,
            object_id=instance.pk,
            object_repr=str(instance),

            # CHANGE TRACKING
            field_name='role',
            old_value=old_instance.role if hasattr(old_instance, 'role') else '',
            new_value=instance.role if hasattr(instance, 'role') else '',
            changes_summary='; '.join(changes),

            # OPTIONAL CONTEXT
            extra_data={
                "changes": changes,
            },
            )
    except Exception:
            import logging
            logging.exception("AuditLog write failed")



@receiver(post_save, dispatch_uid="log_model_changes")
def log_model_changes(sender, instance, created, **kwargs):
    if sender.__name__ in LOG_MODELS:
        return

    if not sender.__module__.startswith('apps.'):
        return

    action = 'CREATED' if created else 'UPDATED'

    ActivityLog.objects.create(
        user=None,
        action=f'{sender.__name__}_{action}',
        description=f'{sender.__name__} {action.lower()} (ID {instance.pk})',
        timestamp=now(),
    )


@receiver(post_delete, dispatch_uid="log_model_deletions")
def log_model_deletions(sender, instance, **kwargs):
    if sender.__name__ in LOG_MODELS:
        return

    if not sender.__module__.startswith('apps.'):
        return

    ActivityLog.objects.create(
        user=None,
        action=f'{sender.__name__}_DELETED',
        description=f'{sender.__name__} deleted (ID {instance.pk})',
        timestamp=now(),
    )
