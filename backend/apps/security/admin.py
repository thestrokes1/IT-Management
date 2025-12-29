"""
Security admin interface for IT Management Platform.
Provides comprehensive admin interface for managing security events, policies, and incidents.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponse
import csv
from datetime import datetime, timedelta

from .models import (
    SecurityEvent, AuditLog, SecurityPolicy, SecurityThreshold,
    SecurityIncident, SecurityDashboard
)


@admin.register(SecurityEvent)
class SecurityEventAdmin(admin.ModelAdmin):
    """
    Admin interface for SecurityEvent model.
    """
    list_display = [
        'id', 'event_type', 'severity', 'status', 'title', 'username',
        'ip_address', 'created_at', 'resolved_by_display', 'actions_display'
    ]
    list_filter = [
        'event_type', 'severity', 'status', 'created_at', 'resolved_at'
    ]
    search_fields = [
        'title', 'description', 'username', 'ip_address'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'resolved_at'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'severity', 'status', 'title', 'description')
        }),
        ('User Information', {
            'fields': ('user', 'username', 'session_id')
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent', 'referer', 'request_method', 'request_path')
        }),
        ('Response Information', {
            'fields': ('response_status', 'response_data')
        }),
        ('Additional Data', {
            'fields': ('additional_data',)
        }),
        ('Resolution', {
            'fields': ('resolved_by', 'resolved_at', 'resolution_notes'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_resolved', 'mark_escalated', 'export_selected']
    
    def resolved_by_display(self, obj):
        """Display resolved by information."""
        if obj.resolved_by:
            return format_html(
                '<span style="color: green;">{}</span>',
                obj.resolved_by.username
            )
        return format_html('<span style="color: red;">Unresolved</span>')
    resolved_by_display.short_description = 'Resolved By'
    
    def actions_display(self, obj):
        """Display action buttons."""
        if obj.status == 'OPEN':
            return format_html(
                '<a href="{}" class="button">Resolve</a> ',
                reverse('admin:security_securityevent_change', args=[obj.id])
            )
        return '-'
    actions_display.short_description = 'Actions'
    
    def mark_resolved(self, request, queryset):
        """Mark selected events as resolved."""
        updated = queryset.update(status='RESOLVED', resolved_at=timezone.now())
        self.message_user(
            request,
            f'{updated} security events marked as resolved.',
            messages.SUCCESS
        )
    mark_resolved.short_description = 'Mark selected events as resolved'
    
    def mark_escalated(self, request, queryset):
        """Mark selected events as escalated."""
        updated = queryset.update(status='ESCALATED')
        self.message_user(
            request,
            f'{updated} security events marked as escalated.',
            messages.WARNING
        )
    mark_escalated.short_description = 'Mark selected events as escalated'
    
    def export_selected(self, request, queryset):
        """Export selected events to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="security_events_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Event Type', 'Severity', 'Status', 'Title', 'Description',
            'Username', 'IP Address', 'Created At', 'Resolved At', 'Resolved By'
        ])
        
        for event in queryset:
            writer.writerow([
                event.id, event.get_event_type_display(), event.get_severity_display(),
                event.get_status_display(), event.title, event.description,
                event.username, event.ip_address, event.created_at,
                event.resolved_at, event.resolved_by.username if event.resolved_by else ''
            ])
        
        self.message_user(
            request,
            f'Security events exported to CSV.',
            messages.SUCCESS
        )
        return response
    export_selected.short_description = 'Export selected events to CSV'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user', 'resolved_by')
    
    def save_model(self, request, obj, form, change):
        """Set created_by and modified_by."""
        if not change:  # Only on creation
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for AuditLog model (read-only).
    """
    list_display = [
        'id', 'action', 'resource_type', 'resource_name', 'username',
        'ip_address', 'success', 'timestamp'
    ]
    list_filter = [
        'action', 'resource_type', 'success', 'timestamp'
    ]
    search_fields = [
        'username', 'resource_name', 'description', 'ip_address'
    ]
    readonly_fields = [
        'timestamp', 'old_values', 'new_values', 'changed_fields'
    ]
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """Disable add permission for audit logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable change permission for audit logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable delete permission for audit logs."""
        return False
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')


@admin.register(SecurityPolicy)
class SecurityPolicyAdmin(admin.ModelAdmin):
    """
    Admin interface for SecurityPolicy model.
    """
    list_display = [
        'id', 'name', 'policy_type', 'status', 'version', 'created_by',
        'valid_from', 'valid_until', 'is_valid_display'
    ]
    list_filter = [
        'policy_type', 'status', 'valid_from', 'valid_until'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'created_at', 'updated_at', 'version', 'created_by', 'modified_by'
    ]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'policy_type', 'description', 'status')
        }),
        ('Configuration', {
            'fields': ('config', 'rules')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Metadata', {
            'fields': ('version', 'created_by', 'modified_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def is_valid_display(self, obj):
        """Display policy validity status."""
        if obj.is_valid():
            return format_html('<span style="color: green;">Valid</span>')
        return format_html('<span style="color: red;">Invalid</span>')
    is_valid_display.short_description = 'Validity'
    
    def save_model(self, request, obj, form, change):
        """Set created_by and modified_by."""
        if not change:  # Only on creation
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SecurityThreshold)
class SecurityThresholdAdmin(admin.ModelAdmin):
    """
    Admin interface for SecurityThreshold model.
    """
    list_display = [
        'id', 'name', 'threshold_type', 'operator', 'value', 'unit',
        'scope', 'is_active', 'alert_enabled', 'auto_block_enabled'
    ]
    list_filter = [
        'threshold_type', 'operator', 'scope', 'is_active',
        'alert_enabled', 'auto_block_enabled'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'created_at', 'updated_at', 'created_by'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'threshold_type', 'description')
        }),
        ('Threshold Configuration', {
            'fields': ('operator', 'value', 'unit', 'scope', 'context_data')
        }),
        ('Actions', {
            'fields': ('alert_enabled', 'auto_block_enabled', 'notification_recipients')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by on creation."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SecurityIncident)
class SecurityIncidentAdmin(admin.ModelAdmin):
    """
    Admin interface for SecurityIncident model.
    """
    list_display = [
        'id', 'case_number', 'title', 'incident_type', 'severity', 'status',
        'assigned_to_display', 'discovered_by', 'created_at', 'age_display'
    ]
    list_filter = [
        'incident_type', 'severity', 'status', 'discovered_at', 'resolved_at'
    ]
    search_fields = [
        'title', 'description', 'case_number', 'impact_assessment'
    ]
    readonly_fields = [
        'case_number', 'created_at', 'updated_at', 'created_by'
    ]
    date_hierarchy = 'discovered_at'
    
    fieldsets = (
        ('Incident Information', {
            'fields': ('title', 'incident_type', 'severity', 'status', 'description')
        }),
        ('Impact Assessment', {
            'fields': ('impact_assessment', 'affected_systems', 'affected_users')
        }),
        ('People Involved', {
            'fields': ('discovered_by', 'assigned_to')
        }),
        ('Timeline', {
            'fields': ('discovered_at', 'reported_at', 'contained_at', 'resolved_at')
        }),
        ('Resolution', {
            'fields': ('resolution_summary', 'lessons_learned', 'preventive_measures'),
            'classes': ('collapse',)
        }),
        ('Related Events', {
            'fields': ('related_events',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('case_number', 'created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['assign_to_me', 'mark_contained', 'mark_resolved', 'export_incidents']
    
    def assigned_to_display(self, obj):
        """Display assigned user."""
        if obj.assigned_to:
            return format_html(
                '<span style="color: blue;">{}</span>',
                obj.assigned_to.username
            )
        return format_html('<span style="color: orange;">Unassigned</span>')
    assigned_to_display.short_description = 'Assigned To'
    
    def age_display(self, obj):
        """Display incident age."""
        age_hours = obj.age_in_hours
        if age_hours < 24:
            return format_html(f'<span style="color: green;">{age_hours}h</span>')
        elif age_hours < 72:
            return format_html(f'<span style="color: orange;">{age_hours}h</span>')
        else:
            return format_html(f'<span style="color: red;">{age_hours}h</span>')
    age_display.short_description = 'Age'
    
    def assign_to_me(self, request, queryset):
        """Assign selected incidents to current user."""
        updated = queryset.update(assigned_to=request.user)
        self.message_user(
            request,
            f'{updated} incidents assigned to you.',
            messages.SUCCESS
        )
    assign_to_me.short_description = 'Assign selected incidents to me'
    
    def mark_contained(self, request, queryset):
        """Mark selected incidents as contained."""
        updated = queryset.update(
            status='CONTAINED',
            contained_at=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} incidents marked as contained.',
            messages.WARNING
        )
    mark_contained.short_description = 'Mark selected incidents as contained'
    
    def mark_resolved(self, request, queryset):
        """Mark selected incidents as resolved."""
        updated = queryset.update(
            status='RESOLVED',
            resolved_at=timezone.now()
        )
        self.message_user(
            request,
            f'{updated} incidents marked as resolved.',
            messages.SUCCESS
        )
    mark_resolved.short_description = 'Mark selected incidents as resolved'
    
    def export_incidents(self, request, queryset):
        """Export selected incidents to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="security_incidents_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Case Number', 'Title', 'Incident Type', 'Severity', 'Status',
            'Discovered At', 'Resolved At', 'Assigned To', 'Discovered By'
        ])
        
        for incident in queryset:
            writer.writerow([
                incident.case_number, incident.title,
                incident.get_incident_type_display(), incident.get_severity_display(),
                incident.get_status_display(), incident.discovered_at,
                incident.resolved_at,
                incident.assigned_to.username if incident.assigned_to else '',
                incident.discovered_by.username if incident.discovered_by else ''
            ])
        
        self.message_user(
            request,
            'Security incidents exported to CSV.',
            messages.SUCCESS
        )
        return response
    export_incidents.short_description = 'Export selected incidents to CSV'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'assigned_to', 'discovered_by', 'created_by'
        )
    
    def save_model(self, request, obj, form, change):
        """Set created_by on creation."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SecurityDashboard)
class SecurityDashboardAdmin(admin.ModelAdmin):
    """
    Admin interface for SecurityDashboard model.
    """
    list_display = [
        'id', 'name', 'is_public', 'refresh_interval', 'created_by',
        'created_at', 'allowed_users_count'
    ]
    list_filter = [
        'is_public', 'refresh_interval', 'created_at'
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'created_at', 'updated_at', 'created_by'
    ]
    
    filter_horizontal = ('allowed_users',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Configuration', {
            'fields': ('widgets', 'layout', 'refresh_interval')
        }),
        ('Access Control', {
            'fields': ('is_public', 'allowed_users', 'allowed_roles')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def allowed_users_count(self, obj):
        """Display count of allowed users."""
        return obj.allowed_users.count()
    allowed_users_count.short_description = 'Allowed Users'
    
    def save_model(self, request, obj, form, change):
        """Set created_by on creation."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# Custom Admin Views and Actions
class SecurityAdminSite(admin.AdminSite):
    """
    Custom admin site for security module.
    """
    site_header = "IT Management Platform - Security Admin"
    site_title = "Security Admin"
    index_title = "Security Dashboard"
    
    def get_urls(self):
        """Add custom URLs to admin."""
        from django.urls import path
        from .views import (
            SecurityDashboardView, SecurityReportsView,
            SecurityConfigurationView, SecurityMonitoringView
        )
        
        urls = super().get_urls()
        custom_urls = [
            path('security/dashboard/', self.admin_view(SecurityDashboardView.as_view()), name='security_dashboard'),
            path('security/reports/', self.admin_view(SecurityReportsView.as_view()), name='security_reports'),
            path('security/configuration/', self.admin_view(SecurityConfigurationView.as_view()), name='security_configuration'),
            path('security/monitoring/', self.admin_view(SecurityMonitoringView.as_view()), name='security_monitoring'),
        ]
        return custom_urls + urls


# Create custom admin site instance
security_admin_site = SecurityAdminSite(name='security_admin')

# Register models with custom admin site
security_admin_site.register(SecurityEvent, SecurityEventAdmin)
security_admin_site.register(AuditLog, AuditLogAdmin)
security_admin_site.register(SecurityPolicy, SecurityPolicyAdmin)
security_admin_site.register(SecurityThreshold, SecurityThresholdAdmin)
security_admin_site.register(SecurityIncident, SecurityIncidentAdmin)
security_admin_site.register(SecurityDashboard, SecurityDashboardAdmin)


# Inline Admin Classes
class SecurityEventInline(admin.TabularInline):
    """
    Inline admin for security events.
    """
    model = SecurityEvent
    extra = 0
    readonly_fields = ['created_at', 'event_type', 'severity', 'status']
    can_delete = False


class AuditLogInline(admin.TabularInline):
    """
    Inline admin for audit logs.
    """
    model = AuditLog
    extra = 0
    readonly_fields = ['timestamp', 'action', 'resource_type', 'success']
    can_delete = False


# Admin Actions
def bulk_security_action(modeladmin, request, queryset):
    """
    Generic bulk action for security models.
    """
    action = request.POST.get('action')
    if action == 'export_csv':
        return modeladmin.export_csv(request, queryset)
    elif action == 'archive':
        return modeladmin.archive_selected(request, queryset)
    # Add more actions as needed

bulk_security_action.short_description = "Perform selected action on selected items"


# Admin Filters
class RecentSecurityEventFilter(admin.SimpleListFilter):
    """
    Custom filter for recent security events.
    """
    title = 'Recency'
    parameter_name = 'recency'
    
    def lookups(self, request, model_admin):
        return (
            ('today', 'Today'),
            ('week', 'This Week'),
            ('month', 'This Month'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'today':
            return queryset.filter(created_at__date=timezone.now().date())
        elif self.value() == 'week':
            week_ago = timezone.now() - timedelta(days=7)
            return queryset.filter(created_at__gte=week_ago)
        elif self.value() == 'month':
            month_ago = timezone.now() - timedelta(days=30)
            return queryset.filter(created_at__gte=month_ago)


# Override default admin site with security admin site
# This should be done in the main urls.py if using custom admin site
# admin.site = security_admin_site

