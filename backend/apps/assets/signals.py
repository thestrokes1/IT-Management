"""
Asset signals for IT Management Platform.
Handles asset creation, updates, assignments, and audit logging.
"""

from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Asset, AssetAssignment, AssetMaintenance, AssetAuditLog
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Asset)
def create_asset_audit_log(sender, instance, created, **kwargs):
    """
    Create audit log when asset is created or updated.
    """
    if created:
        # Log asset creation
        AssetAuditLog.objects.create(
            asset=instance,
            user=instance.created_by or User.objects.filter(is_superuser=True).first(),
            action='CREATED',
            description=f'Asset created: {instance.name}',
            new_values={
                'name': instance.name,
                'asset_type': instance.asset_type,
                'category': instance.category.name if instance.category else None,
                'status': instance.status
            }
        )
        logger.info(f"Asset created: {instance.name} ({instance.serial_number or instance.asset_id})")
    else:
        # Log significant changes for updates
        try:
            old_instance = Asset.objects.get(pk=instance.pk)
            changes = []
            old_values = {}
            new_values = {}
            
            # Check for status changes
            if old_instance.status != instance.status:
                changes.append(f"status: {old_instance.status} -> {instance.status}")
                old_values['status'] = old_instance.status
                new_values['status'] = instance.status
            
            # Check for assignment changes
            if old_instance.assigned_to != instance.assigned_to:
                if old_instance.assigned_to:
                    changes.append(f"assigned_to: {old_instance.assigned_to.username} -> {instance.assigned_to.username if instance.assigned_to else 'None'}")
                    old_values['assigned_to'] = old_instance.assigned_to.username
                    new_values['assigned_to'] = instance.assigned_to.username if instance.assigned_to else None
                else:
                    changes.append(f"assigned_to: None -> {instance.assigned_to.username if instance.assigned_to else 'None'}")
                    old_values['assigned_to'] = None
                    new_values['assigned_to'] = instance.assigned_to.username if instance.assigned_to else None
            
            # Check for location changes
            if old_instance.location != instance.location:
                changes.append(f"location: {old_instance.location} -> {instance.location}")
                old_values['location'] = old_instance.location
                new_values['location'] = instance.location
            
            # Check for warranty expiry changes
            if old_instance.warranty_expiry != instance.warranty_expiry:
                changes.append(f"warranty_expiry: {old_instance.warranty_expiry} -> {instance.warranty_expiry}")
                old_values['warranty_expiry'] = str(old_instance.warranty_expiry)
                new_values['warranty_expiry'] = str(instance.warranty_expiry)
            
            if changes:
                AssetAuditLog.objects.create(
                    asset=instance,
                    user=instance.updated_by or User.objects.filter(is_superuser=True).first(),
                    action='UPDATED',
                    description=f'Asset updated: {", ".join(changes)}',
                    old_values=old_values,
                    new_values=new_values
                )
                logger.info(f"Asset updated: {instance.name} - {', '.join(changes)}")
        except Asset.DoesNotExist:
            pass

@receiver(pre_delete, sender=Asset)
def create_asset_deletion_log(sender, instance, **kwargs):
    """
    Create audit log when asset is deleted.
    Use pre_delete to ensure the asset still exists in the database.
    """
    # Get user from updated_by if available (user performing the deletion)
    user = instance.updated_by or User.objects.filter(is_superuser=True).first()
    AssetAuditLog.objects.create(
        asset=instance,
        user=user,
        action='DELETED',
        description=f'Asset deleted: {instance.name}',
        old_values={
            'name': instance.name,
            'asset_type': instance.asset_type,
            'serial_number': instance.serial_number
        }
    )
    logger.warning(f"Asset deleted: {instance.name} ({instance.serial_number or instance.asset_id})")

@receiver(post_save, sender=AssetAssignment)
def create_assignment_audit_log(sender, instance, created, **kwargs):
    """
    Create audit log when asset assignment is created.
    """
    if created:
        action = 'ASSIGNED' if instance.assignment_type == 'ASSIGNMENT' else 'UNASSIGNED'
        
        AssetAuditLog.objects.create(
            asset=instance.asset,
            user=instance.assigned_by,
            action=action,
            description=f'Asset {action.lower()} to {instance.user.username}',
            new_values={
                'assignment_type': instance.assignment_type,
                'user': instance.user.username,
                'assigned_date': instance.assigned_date.isoformat()
            }
        )
        
        if instance.assignment_type == 'ASSIGNMENT':
            logger.info(f"Asset assigned: {instance.asset.name} -> {instance.user.username}")
        else:
            logger.info(f"Asset unassigned: {instance.asset.name} from {instance.user.username}")

@receiver(post_save, sender=AssetMaintenance)
def create_maintenance_audit_log(sender, instance, created, **kwargs):
    """
    Create audit log when maintenance record is created or updated.
    """
    if created:
        AssetAuditLog.objects.create(
            asset=instance.asset,
            user=instance.created_by,
            action='MAINTENANCE',
            description=f'Maintenance record added: {instance.get_maintenance_type_display()}',
            new_values={
                'maintenance_type': instance.maintenance_type,
                'status': instance.status,
                'scheduled_date': instance.scheduled_date.isoformat(),
                'performed_by': instance.performed_by,
                'cost': str(instance.cost) if instance.cost else None
            }
        )
        logger.info(f"Maintenance record added for {instance.asset.name}: {instance.get_maintenance_type_display()}")
    else:
        # Log status changes
        try:
            old_instance = AssetMaintenance.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                AssetAuditLog.objects.create(
                    asset=instance.asset,
                    user=instance.created_by,
                    action='MAINTENANCE',
                    description=f'Maintenance status changed: {old_instance.status} -> {instance.status}',
                    old_values={'status': old_instance.status},
                    new_values={'status': instance.status}
                )
                logger.info(f"Maintenance status updated for {instance.asset.name}: {old_instance.status} -> {instance.status}")
        except AssetMaintenance.DoesNotExist:
            pass

@receiver(post_save, sender=Asset)
def update_asset_timestamps(sender, instance, **kwargs):
    """
    Update asset timestamps and perform automatic status checks.
    """
    # Update the updated_at timestamp
    Asset.objects.filter(pk=instance.pk).update(updated_at=timezone.now())
    
    # Check for warranty expiry (would be enhanced with actual logic)
    # This is a placeholder for automated warranty monitoring
    if instance.warranty_expiry:
        days_until_expiry = (instance.warranty_expiry - timezone.now().date()).days
        if days_until_expiry <= 0 and instance.status == 'ACTIVE':
            # Auto-update status for expired warranties (optional feature)
            logger.info(f"Warranty expired for asset: {instance.name} ({days_until_expiry} days)")

@receiver(post_save, sender=Asset)
def check_end_of_life(sender, instance, **kwargs):
    """
    Check for end of life conditions and create alerts.
    """
    if instance.end_of_life and instance.end_of_life <= timezone.now().date():
        if instance.status in ['ACTIVE', 'IN_REPAIR']:
            # Create alert for end of life assets
            logger.warning(f"Asset has reached end of life: {instance.name} (EOL: {instance.end_of_life})")
            
            # Optional: Auto-retire assets that have reached end of life
            # instance.update_status('RETIRED', User.objects.filter(is_superuser=True).first())

@receiver(post_save, sender=Asset)
def validate_license_seats(sender, instance, **kwargs):
    """
    Validate software license seat usage.
    """
    # This would typically be handled by the SoftwareAsset model
    # But we can add validation here if needed
    pass

# Custom signals for complex operations
from django.dispatch import Signal

# Define custom signals
asset_assigned = Signal()
asset_unassigned = Signal()
asset_status_changed = Signal()
asset_maintenance_scheduled = Signal()

@receiver(asset_assigned)
def log_asset_assignment(sender, asset, user, assigned_by, **kwargs):
    """
    Log asset assignment event.
    """
    logger.info(f"Asset assignment event: {asset.name} assigned to {user.username} by {assigned_by.username}")

@receiver(asset_unassigned)
def log_asset_unassignment(sender, asset, user, unassigned_by, **kwargs):
    """
    Log asset unassignment event.
    """
    logger.info(f"Asset unassignment event: {asset.name} unassigned from {user.username} by {unassigned_by.username}")

@receiver(asset_status_changed)
def log_asset_status_change(sender, asset, old_status, new_status, changed_by, **kwargs):
    """
    Log asset status change event.
    """
    logger.info(f"Asset status change event: {asset.name} status changed from {old_status} to {new_status} by {changed_by.username}")

@receiver(asset_maintenance_scheduled)
def log_asset_maintenance_scheduled(sender, maintenance, **kwargs):
    """
    Log scheduled maintenance event.
    """
    logger.info(f"Asset maintenance scheduled: {maintenance.asset.name} - {maintenance.get_maintenance_type_display()}")

# Helper functions to send signals
def send_asset_assignment_signal(asset, user, assigned_by):
    """
    Helper function to send asset assignment signal.
    """
    asset_assigned.send(sender=Asset, asset=asset, user=user, assigned_by=assigned_by)

def send_asset_unassignment_signal(asset, user, unassigned_by):
    """
    Helper function to send asset unassignment signal.
    """
    asset_unassigned.send(sender=Asset, asset=asset, user=user, unassigned_by=unassigned_by)

def send_asset_status_change_signal(asset, old_status, new_status, changed_by):
    """
    Helper function to send asset status change signal.
    """
    asset_status_changed.send(sender=Asset, asset=asset, old_status=old_status, new_status=new_status, changed_by=changed_by)

def send_asset_maintenance_scheduled_signal(maintenance):
    """
    Helper function to send asset maintenance scheduled signal.
    """
    asset_maintenance_scheduled.send(sender=AssetMaintenance, maintenance=maintenance)
