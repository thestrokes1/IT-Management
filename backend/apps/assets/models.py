"""
Asset models for IT Management Platform.
Hardware and software asset management with tracking and assignment.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid
from decimal import Decimal

User = get_user_model()

class AssetCategory(models.Model):
    """
    Categories for organizing assets.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'asset_categories'
        verbose_name = 'Asset Category'
        verbose_name_plural = 'Asset Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Asset(models.Model):
    """
    Base asset model for hardware and software assets.
    """
    # Asset type choices
    TYPE_CHOICES = [
        ('HARDWARE', 'Hardware'),
        ('SOFTWARE', 'Software'),
    ]
    
    # Status choices
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('IN_REPAIR', 'In Repair'),
        ('RETIRED', 'Retired'),
        ('DISPOSED', 'Disposed'),
        ('MISSING', 'Missing'),
    ]
    
    # Asset ID (unique identifier)
    asset_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Basic information
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    asset_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    category = models.ForeignKey(AssetCategory, on_delete=models.PROTECT, related_name='assets')
    
    # Identification
    serial_number = models.CharField(max_length=100, blank=True, unique=True)
    model = models.CharField(max_length=100, blank=True)
    manufacturer = models.CharField(max_length=100, blank=True)
    version = models.CharField(max_length=50, blank=True)
    
    # Status and lifecycle
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    warranty_expiry = models.DateField(null=True, blank=True)
    end_of_life = models.DateField(null=True, blank=True)
    
    # Location and assignment
    location = models.CharField(max_length=200, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_assets')
    assigned_date = models.DateTimeField(null=True, blank=True)
    
    # Asset details (JSON for flexibility)
    specifications = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assets_updated')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'assets'
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['asset_type', 'status']),
            models.Index(fields=['assigned_to']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.serial_number or self.asset_id})"
    
    @property
    def is_assigned(self):
        """Check if asset is currently assigned."""
        return self.assigned_to is not None and self.status == 'ACTIVE'
    
    @property
    def is_under_warranty(self):
        """Check if asset is under warranty."""
        if not self.warranty_expiry:
            return False
        return timezone.now().date() <= self.warranty_expiry
    
    @property
    def days_since_purchase(self):
        """Get days since purchase."""
        if not self.purchase_date:
            return None
        return (timezone.now().date() - self.purchase_date).days
    
    def assign_to_user(self, user, assigned_by):
        """Assign asset to a user."""
        self.assigned_to = user
        self.assigned_date = timezone.now()
        self.status = 'ACTIVE'
        self.updated_by = assigned_by
        self.save()
    
    def unassign(self, unassigned_by):
        """Unassign asset from user."""
        self.assigned_to = None
        self.assigned_date = None
        self.updated_by = unassigned_by
        self.save()
    
    def update_status(self, new_status, updated_by):
        """Update asset status."""
        old_status = self.status
        self.status = new_status
        self.updated_by = updated_by
        self.save()
        
        # If retiring asset, unassign it
        if new_status in ['RETIRED', 'DISPOSED'] and self.assigned_to:
            self.unassign(updated_by)

class HardwareAsset(Asset):
    """
    Hardware-specific asset model.
    """
    # Hardware type choices
    HARDWARE_TYPE_CHOICES = [
        ('COMPUTER', 'Desktop Computer'),
        ('LAPTOP', 'Laptop'),
        ('SERVER', 'Server'),
        ('MONITOR', 'Monitor'),
        ('PRINTER', 'Printer'),
        ('NETWORK_DEVICE', 'Network Device'),
        ('MOBILE_DEVICE', 'Mobile Device'),
        ('PERIPHERAL', 'Peripheral'),
        ('OTHER', 'Other'),
    ]
    
    # Hardware-specific fields
    hardware_type = models.CharField(max_length=20, choices=HARDWARE_TYPE_CHOICES)
    cpu = models.CharField(max_length=100, blank=True)
    memory = models.CharField(max_length=50, blank=True)
    storage = models.CharField(max_length=100, blank=True)
    operating_system = models.CharField(max_length=100, blank=True)
    mac_address = models.CharField(max_length=17, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        db_table = 'hardware_assets'
        verbose_name = 'Hardware Asset'
        verbose_name_plural = 'Hardware Assets'

class SoftwareAsset(Asset):
    """
    Software-specific asset model.
    """
    # Software type choices
    SOFTWARE_TYPE_CHOICES = [
        ('OPERATING_SYSTEM', 'Operating System'),
        ('PRODUCTIVITY', 'Productivity Suite'),
        ('DEVELOPMENT', 'Development Tool'),
        ('SECURITY', 'Security Software'),
        ('DATABASE', 'Database'),
        ('SERVER_SOFTWARE', 'Server Software'),
        ('MOBILE_APP', 'Mobile Application'),
        ('WEB_SERVICE', 'Web Service'),
        ('OTHER', 'Other'),
    ]
    
    # License type choices
    LICENSE_TYPE_CHOICES = [
        ('PERPETUAL', 'Perpetual License'),
        ('SUBSCRIPTION', 'Subscription'),
        ('FREEMIUM', 'Freemium'),
        ('OPEN_SOURCE', 'Open Source'),
        ('TRIAL', 'Trial'),
    ]
    
    # Software-specific fields
    software_type = models.CharField(max_length=20, choices=SOFTWARE_TYPE_CHOICES)
    license_type = models.CharField(max_length=20, choices=LICENSE_TYPE_CHOICES, blank=True)
    license_key = models.TextField(blank=True)
    license_seats = models.PositiveIntegerField(default=1)
    seats_used = models.PositiveIntegerField(default=0)
    vendor = models.CharField(max_length=100, blank=True)
    support_end_date = models.DateField(null=True, blank=True)
    download_url = models.URLField(blank=True)
    installation_guide = models.TextField(blank=True)
    
    class Meta:
        db_table = 'software_assets'
        verbose_name = 'Software Asset'
        verbose_name_plural = 'Software Assets'
    
    @property
    def seats_available(self):
        """Get available license seats."""
        return self.license_seats - self.seats_used
    
    @property
    def license_utilization(self):
        """Get license utilization percentage."""
        if self.license_seats == 0:
            return 0
        return round((self.seats_used / self.license_seats) * 100, 2)

class AssetAssignment(models.Model):
    """
    Track asset assignments over time.
    """
    # Assignment type choices
    ASSIGNMENT_TYPE_CHOICES = [
        ('ASSIGNMENT', 'Assignment'),
        ('UNASSIGNMENT', 'Unassignment'),
        ('TRANSFER', 'Transfer'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asset_assignments')
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPE_CHOICES)
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asset_assignments_made')
    assigned_date = models.DateTimeField(auto_now_add=True)
    return_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'asset_assignments'
        verbose_name = 'Asset Assignment'
        verbose_name_plural = 'Asset Assignments'
        ordering = ['-assigned_date']
        indexes = [
            models.Index(fields=['asset', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        action = "Assigned to" if self.assignment_type == 'ASSIGNMENT' else "Unassigned from"
        return f"{self.asset.name} {action} {self.user.username}"

class AssetMaintenance(models.Model):
    """
    Track asset maintenance and service history.
    """
    # Maintenance type choices
    MAINTENANCE_TYPE_CHOICES = [
        ('PREVENTIVE', 'Preventive Maintenance'),
        ('CORRECTIVE', 'Corrective Maintenance'),
        ('UPGRADE', 'Upgrade'),
        ('REPAIR', 'Repair'),
        ('INSPECTION', 'Inspection'),
    ]
    
    # Status choices
    MAINTENANCE_STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='maintenance_records')
    maintenance_type = models.CharField(max_length=20, choices=MAINTENANCE_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=MAINTENANCE_STATUS_CHOICES, default='SCHEDULED')
    scheduled_date = models.DateTimeField()
    completed_date = models.DateTimeField(null=True, blank=True)
    performed_by = models.CharField(max_length=200, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='maintenance_records_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'asset_maintenance'
        verbose_name = 'Asset Maintenance'
        verbose_name_plural = 'Asset Maintenance Records'
        ordering = ['-scheduled_date']
        indexes = [
            models.Index(fields=['asset', 'status']),
            models.Index(fields=['scheduled_date']),
        ]
    
    def __str__(self):
        return f"{self.asset.name} - {self.get_maintenance_type_display()} - {self.scheduled_date}"

class AssetAuditLog(models.Model):
    """
    Comprehensive audit log for all asset changes.
    """
    # Action choices
    ACTION_CHOICES = [
        ('CREATED', 'Created'),
        ('UPDATED', 'Updated'),
        ('DELETED', 'Deleted'),
        ('ASSIGNED', 'Assigned'),
        ('UNASSIGNED', 'Unassigned'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('TRANSFERRED', 'Transferred'),
        ('MAINTENANCE', 'Maintenance Record Added'),
    ]
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asset_audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'asset_audit_logs'
        verbose_name = 'Asset Audit Log'
        verbose_name_plural = 'Asset Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['asset', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.asset.name} - {self.get_action_display()} - {self.timestamp}"

class AssetReport(models.Model):
    """
    Asset reports and analytics data.
    """
    # Report type choices
    REPORT_TYPE_CHOICES = [
        ('ASSET_SUMMARY', 'Asset Summary'),
        ('ASSIGNMENT_REPORT', 'Assignment Report'),
        ('MAINTENANCE_REPORT', 'Maintenance Report'),
        ('WARRANTY_REPORT', 'Warranty Report'),
        ('COST_ANALYSIS', 'Cost Analysis'),
        ('DEPRECIATION_REPORT', 'Depreciation Report'),
    ]
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asset_reports_generated')
    generated_at = models.DateTimeField(auto_now_add=True)
    file_path = models.FilePathField(null=True, blank=True)
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True)  # daily, weekly, monthly
    
    class Meta:
        db_table = 'asset_reports'
        verbose_name = 'Asset Report'
        verbose_name_plural = 'Asset Reports'
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} - {self.generated_at}"
