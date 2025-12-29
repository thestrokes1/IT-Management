"""
Django admin configuration for assets app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    AssetCategory, Asset, HardwareAsset, SoftwareAsset,
    AssetAssignment, AssetMaintenance, AssetAuditLog, AssetReport
)

@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    """Admin interface for AssetCategory model."""
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

class AssetAssignmentInline(admin.TabularInline):
    """Inline admin for asset assignments."""
    model = AssetAssignment
    extra = 0
    readonly_fields = ['assigned_date', 'is_active']
    fields = ['user', 'assignment_type', 'assigned_by', 'assigned_date', 'return_date', 'notes', 'is_active']

class AssetMaintenanceInline(admin.TabularInline):
    """Inline admin for asset maintenance."""
    model = AssetMaintenance
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['maintenance_type', 'status', 'scheduled_date', 'completed_date', 'performed_by', 'cost', 'description']

class AssetAuditLogInline(admin.TabularInline):
    """Inline admin for asset audit logs."""
    model = AssetAuditLog
    extra = 0
    readonly_fields = ['timestamp']
    fields = ['user', 'action', 'description', 'timestamp']

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """Admin interface for Asset model."""
    list_display = ['name', 'asset_type', 'status', 'assigned_to', 'category', 'serial_number']
    list_filter = ['asset_type', 'status', 'category', 'manufacturer', 'created_at']
    search_fields = ['name', 'serial_number', 'model', 'manufacturer']
    readonly_fields = ['asset_id', 'created_at', 'updated_at', 'asset_id']
    
    fieldsets = (
        ('Asset Information', {
            'fields': ('asset_id', 'name', 'description', 'asset_type', 'category')
        }),
        ('Identification', {
            'fields': ('serial_number', 'model', 'manufacturer', 'version')
        }),
        ('Status & Lifecycle', {
            'fields': ('status', 'purchase_date', 'purchase_cost', 'warranty_expiry', 'end_of_life')
        }),
        ('Location & Assignment', {
            'fields': ('location', 'assigned_to', 'assigned_date')
        }),
        ('Details', {
            'fields': ('specifications', 'tags')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'updated_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [AssetAssignmentInline, AssetMaintenanceInline, AssetAuditLogInline]
    
    def get_readonly_fields(self, request, obj=None):
        """Make asset_id readonly after creation."""
        readonly_fields = list(self.readonly_fields)
        if obj:  # editing an existing object
            readonly_fields.extend(['asset_id'])
        return readonly_fields

@admin.register(HardwareAsset)
class HardwareAssetAdmin(admin.ModelAdmin):
    """Admin interface for HardwareAsset model."""
    list_display = ['name', 'hardware_type', 'cpu', 'memory', 'assigned_to']
    list_filter = ['hardware_type', 'operating_system', 'manufacturer']
    search_fields = ['name', 'serial_number', 'cpu', 'memory', 'storage']
    readonly_fields = ['asset_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Asset Information', {
            'fields': ('asset_ptr', 'name', 'description', 'asset_type', 'category')
        }),
        ('Hardware Details', {
            'fields': ('hardware_type', 'cpu', 'memory', 'storage', 'operating_system', 'mac_address', 'ip_address')
        }),
        ('Identification', {
            'fields': ('serial_number', 'model', 'manufacturer', 'version')
        }),
        ('Status & Lifecycle', {
            'fields': ('status', 'purchase_date', 'purchase_cost', 'warranty_expiry', 'end_of_life')
        }),
        ('Location & Assignment', {
            'fields': ('location', 'assigned_to', 'assigned_date')
        }),
        ('Details', {
            'fields': ('specifications', 'tags')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'updated_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(SoftwareAsset)
class SoftwareAssetAdmin(admin.ModelAdmin):
    """Admin interface for SoftwareAsset model."""
    list_display = ['name', 'software_type', 'license_type', 'license_seats', 'seats_used']
    list_filter = ['software_type', 'license_type', 'vendor', 'support_end_date']
    search_fields = ['name', 'vendor', 'license_key', 'version']
    readonly_fields = ['asset_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Asset Information', {
            'fields': ('asset_ptr', 'name', 'description', 'asset_type', 'category')
        }),
        ('Software Details', {
            'fields': ('software_type', 'license_type', 'license_key', 'license_seats', 'seats_used', 'vendor', 'support_end_date')
        }),
        ('Installation', {
            'fields': ('download_url', 'installation_guide')
        }),
        ('Identification', {
            'fields': ('serial_number', 'model', 'manufacturer', 'version')
        }),
        ('Status & Lifecycle', {
            'fields': ('status', 'purchase_date', 'purchase_cost', 'warranty_expiry', 'end_of_life')
        }),
        ('Location & Assignment', {
            'fields': ('location', 'assigned_to', 'assigned_date')
        }),
        ('Details', {
            'fields': ('specifications', 'tags')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'updated_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    """Admin interface for AssetAssignment model."""
    list_display = ['asset', 'user', 'assignment_type', 'assigned_by', 'assigned_date', 'is_active']
    list_filter = ['assignment_type', 'is_active', 'assigned_date']
    search_fields = ['asset__name', 'user__username', 'notes']
    readonly_fields = ['assigned_date', 'is_active']
    
    fieldsets = (
        ('Assignment Details', {
            'fields': ('asset', 'user', 'assignment_type', 'assigned_by')
        }),
        ('Dates', {
            'fields': ('assigned_date', 'return_date')
        }),
        ('Notes', {
            'fields': ('notes', 'is_active')
        }),
    )

@admin.register(AssetMaintenance)
class AssetMaintenanceAdmin(admin.ModelAdmin):
    """Admin interface for AssetMaintenance model."""
    list_display = ['asset', 'maintenance_type', 'status', 'scheduled_date', 'performed_by']
    list_filter = ['maintenance_type', 'status', 'scheduled_date', 'completed_date']
    search_fields = ['asset__name', 'description', 'performed_by']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Maintenance Details', {
            'fields': ('asset', 'maintenance_type', 'status', 'description')
        }),
        ('Scheduling', {
            'fields': ('scheduled_date', 'completed_date')
        }),
        ('Service Information', {
            'fields': ('performed_by', 'cost')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Audit Information', {
            'fields': ('created_by',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AssetAuditLog)
class AssetAuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AssetAuditLog model."""
    list_display = ['asset', 'user', 'action', 'timestamp']
    list_filter = ['action', 'timestamp', 'asset']
    search_fields = ['asset__name', 'user__username', 'description']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Audit Details', {
            'fields': ('asset', 'user', 'action', 'description')
        }),
        ('Changes', {
            'fields': ('old_values', 'new_values')
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )

@admin.register(AssetReport)
class AssetReportAdmin(admin.ModelAdmin):
    """Admin interface for AssetReport model."""
    list_display = ['title', 'report_type', 'generated_by', 'generated_at', 'is_scheduled']
    list_filter = ['report_type', 'is_scheduled', 'schedule_frequency', 'generated_at']
    search_fields = ['title', 'description']
    readonly_fields = ['generated_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_type', 'title', 'description')
        }),
        ('Configuration', {
            'fields': ('parameters',)
        }),
        ('Generation', {
            'fields': ('generated_by', 'generated_at', 'file_path')
        }),
        ('Scheduling', {
            'fields': ('is_scheduled', 'schedule_frequency')
        }),
    )

