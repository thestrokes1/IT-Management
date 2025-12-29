"""
User signals for IT Management Platform.
Handles user creation, profile management, and audit logging.
"""

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import UserProfile, UserSession, LoginAttempt
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create user profile when user is created.
    """
    if created:
        try:
            UserProfile.objects.create(user=instance)
            logger.info(f"User profile created for user: {instance.username}")
        except Exception as e:
            logger.error(f"Failed to create user profile for {instance.username}: {str(e)}")

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save user profile when user is updated.
    """
    try:
        if hasattr(instance, 'profile'):
            instance.profile.save()
    except UserProfile.DoesNotExist:
        # Create profile if it doesn't exist
        UserProfile.objects.create(user=instance)
    except Exception as e:
        logger.error(f"Failed to save user profile for {instance.username}: {str(e)}")

@receiver(post_save, sender=User)
def log_user_changes(sender, instance, created, **kwargs):
    """
    Log user creation and updates.
    """
    if created:
        logger.info(f"New user created: {instance.username} ({instance.email})")
    else:
        # Log significant changes
        try:
            old_instance = User.objects.get(pk=instance.pk)
            changes = []
            
            if old_instance.role != instance.role:
                changes.append(f"role: {old_instance.role} -> {instance.role}")
            if old_instance.status != instance.status:
                changes.append(f"status: {old_instance.status} -> {instance.status}")
            if old_instance.is_active != instance.is_active:
                changes.append(f"is_active: {old_instance.is_active} -> {instance.is_active}")
            
            if changes:
                logger.info(f"User {instance.username} updated: {', '.join(changes)}")
        except User.DoesNotExist:
            pass

@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """
    Log user deletion.
    """
    logger.warning(f"User deleted: {instance.username} ({instance.email})")

@receiver(post_save, sender=UserSession)
def log_session_changes(sender, instance, created, **kwargs):
    """
    Log user session creation and updates.
    """
    if created:
        logger.info(f"User session created: {instance.user.username} from {instance.ip_address}")
    else:
        if not instance.is_active:
            logger.info(f"User session ended: {instance.user.username}")

@receiver(post_save, sender=LoginAttempt)
def log_login_attempts(sender, instance, **kwargs):
    """
    Log login attempts for security monitoring.
    """
    if instance.successful:
        logger.info(f"Successful login: {instance.username} from {instance.ip_address}")
    else:
        logger.warning(f"Failed login attempt: {instance.username} from {instance.ip_address} - {instance.failure_reason}")

@receiver(post_save, sender=User)
def update_last_activity(sender, instance, **kwargs):
    """
    Update user's last activity timestamp.
    """
    instance.last_active = timezone.now()
    # Don't save here to avoid infinite recursion - just update the timestamp field
    User.objects.filter(pk=instance.pk).update(last_active=timezone.now())

# Custom signal for password changes
from django.dispatch import Signal

# Define custom signals
user_password_changed = Signal()
user_role_changed = Signal()
user_status_changed = Signal()

@receiver(user_password_changed)
def log_password_change(sender, user, **kwargs):
    """
    Log password changes.
    """
    logger.info(f"Password changed for user: {user.username}")
    # Update password_changed_at timestamp
    User.objects.filter(pk=user.pk).update(password_changed_at=timezone.now())

@receiver(user_role_changed)
def log_role_change(sender, user, old_role, new_role, **kwargs):
    """
    Log role changes.
    """
    logger.info(f"Role changed for user {user.username}: {old_role} -> {new_role}")

@receiver(user_status_changed)
def log_status_change(sender, user, old_status, new_status, **kwargs):
    """
    Log status changes.
    """
    logger.info(f"Status changed for user {user.username}: {old_status} -> {new_status}")

def send_password_change_signal(user):
    """
    Helper function to send password change signal.
    """
    user_password_changed.send(sender=User, user=user)

def send_role_change_signal(user, old_role):
    """
    Helper function to send role change signal.
    """
    user_role_changed.send(sender=User, user=user, old_role=old_role, new_role=user.role)

def send_status_change_signal(user, old_status):
    """
    Helper function to send status change signal.
    """
    user_status_changed.send(sender=User, user=user, old_status=old_status, new_status=user.status)
