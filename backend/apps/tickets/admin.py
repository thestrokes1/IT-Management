"""
Django admin configuration for tickets app.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    TicketCategory, TicketType, Ticket, TicketComment, TicketAttachment, 
    TicketHistory, TicketTemplate, SLA, TicketEscalation, TicketSatisfaction, 
    TicketReport
)

@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for TicketCategory model.
    """
    list_display = ['name', 'description', 'color', 'is_active', 'auto_assign_enabled', 'created_at']
    list_filter = ['is_active', 'auto_assign_enabled', 'created_at']
    search_fields = ['name', 'description']

@admin.register(TicketType)
class TicketTypeAdmin(admin.ModelAdmin):
    """
    Admin interface for TicketType model.
    """
    list_display = ['category', 'name', 'sla_hours', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['name', 'description', 'category__name']

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    """
    Admin interface for Ticket model.
    """
    list_display = ['ticket_id', 'title', 'category', 'ticket_type', 'status', 'priority', 'requester', 'assigned_to', 'created_at']
    list_filter = ['status', 'priority', 'impact', 'urgency', 'category', 'ticket_type', 'created_at', 'sla_breached']
    search_fields = ['title', 'description', 'ticket_id', 'requester__username', 'assigned_to__username']
    readonly_fields = ['created_at', 'updated_at', 'ticket_id', 'resolved_at', 'closed_at', 'sla_due_at', 'resolution_time']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('ticket_id', 'title', 'description', 'category', 'ticket_type')
        }),
        ('Requester Information', {
            'fields': ('requester', 'location', 'contact_phone', 'contact_email')
        }),
        ('Ticket Management', {
            'fields': ('priority', 'status', 'impact', 'urgency', 'assigned_to', 'assigned_team')
        }),
        ('Timeline & SLA', {
            'fields': ('sla_due_at', 'sla_breached', 'resolved_at', 'closed_at', 'resolution_time')
        }),
        ('Resolution', {
            'fields': ('resolution_summary',)
        }),
        ('Related Tickets', {
            'fields': ('parent_ticket', 'related_tickets')
        }),
        ('Additional', {
            'fields': ('tags', 'created_by', 'updated_by', 'created_at', 'updated_at')
        }),
    )

@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    """
    Admin interface for TicketComment model.
    """
    list_display = ['ticket', 'user', 'comment_excerpt', 'is_internal', 'is_resolution', 'created_at']
    list_filter = ['is_internal', 'is_resolution', 'created_at']
    search_fields = ['ticket__title', 'ticket__ticket_id', 'user__username', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    
    def comment_excerpt(self, obj):
        """
        Display first 50 characters of comment.
        """
        return obj.comment[:50] + '...' if len(obj.comment) > 50 else obj.comment

@admin.register(TicketAttachment)
class TicketAttachmentAdmin(admin.ModelAdmin):
    """
    Admin interface for TicketAttachment model.
    """
    list_display = ['ticket', 'filename', 'file_size', 'user', 'is_screenshot', 'created_at']
    list_filter = ['is_screenshot', 'mime_type', 'created_at']
    search_fields = ['ticket__title', 'ticket__ticket_id', 'filename', 'description', 'user__username']

@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for TicketHistory model.
    """
    list_display = ['ticket', 'field_name', 'user', 'timestamp']
    list_filter = ['field_name', 'timestamp']
    search_fields = ['ticket__title', 'ticket__ticket_id', 'user__username', 'comment']
    readonly_fields = ['timestamp']

@admin.register(TicketTemplate)
class TicketTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for TicketTemplate model.
    """
    list_display = ['name', 'category', 'ticket_type', 'created_by', 'is_public', 'usage_count', 'created_at']
    list_filter = ['is_public', 'category', 'ticket_type', 'created_at']
    search_fields = ['name', 'description', 'template_title']

@admin.register(SLA)
class SLAAdmin(admin.ModelAdmin):
    """
    Admin interface for SLA model.
    """
    list_display = ['name', 'category', 'ticket_type', 'response_time_hours', 'resolution_time_hours', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'ticket_type', 'created_at']
    search_fields = ['name', 'description']

@admin.register(TicketEscalation)
class TicketEscalationAdmin(admin.ModelAdmin):
    """
    Admin interface for TicketEscalation model.
    """
    list_display = ['ticket', 'escalated_by', 'escalated_to', 'escalation_level', 'escalated_at', 'resolved']
    list_filter = ['escalation_level', 'resolved', 'escalated_at']
    search_fields = ['ticket__title', 'ticket__ticket_id', 'escalated_by__username', 'escalated_to__username', 'reason']

@admin.register(TicketSatisfaction)
class TicketSatisfactionAdmin(admin.ModelAdmin):
    """
    Admin interface for TicketSatisfaction model.
    """
    list_display = ['ticket', 'rating', 'feedback_excerpt', 'rated_by', 'rated_at']
    list_filter = ['rating', 'rated_at']
    search_fields = ['ticket__title', 'ticket__ticket_id', 'rated_by__username', 'feedback']
    readonly_fields = ['rated_at']
    
    def feedback_excerpt(self, obj):
        """
        Display first 50 characters of feedback.
        """
        return obj.feedback[:50] + '...' if len(obj.feedback) > 50 else obj.feedback

@admin.register(TicketReport)
class TicketReportAdmin(admin.ModelAdmin):
    """
    Admin interface for TicketReport model.
    """
    list_display = ['title', 'report_type', 'generated_by', 'generated_at', 'is_scheduled']
    list_filter = ['report_type', 'is_scheduled', 'schedule_frequency', 'generated_at']
    search_fields = ['title', 'description']
