"""
Django admin configuration for projects app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    ProjectCategory, TaskCategory, Project, ProjectMember, Task, TaskComment,
    TaskAttachment, ProjectTemplate, ProjectAuditLog, ProjectReport
)

class ProjectMemberInline(admin.TabularInline):
    """Inline admin for project members."""
    model = ProjectMember
    extra = 1
    fields = ['user', 'role', 'is_active']
    
class TaskInline(admin.TabularInline):
    """Inline admin for project tasks."""
    model = Task
    extra = 0
    fields = ['title', 'type', 'priority', 'status', 'assigned_to', 'due_date', 'completion_percentage']
    
class ProjectAuditLogInline(admin.TabularInline):
    """Inline admin for project audit logs."""
    model = ProjectAuditLog
    extra = 0
    readonly_fields = ['timestamp']
    fields = ['user', 'action', 'description', 'timestamp']

class ProjectReportInline(admin.TabularInline):
    """Inline admin for project reports."""
    model = ProjectReport
    extra = 0
    readonly_fields = ['generated_at']
    fields = ['report_type', 'title', 'generated_by', 'generated_at', 'file_path']

@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    """Admin interface for ProjectCategory model."""
    list_display = ['name', 'color_display', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def color_display(self, obj):
        return format_html(
            '<span style="color: {};">●</span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'color')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    """Admin interface for TaskCategory model."""
    list_display = ['name', 'color_display', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def color_display(self, obj):
        return format_html(
            '<span style="color: {};">●</span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'color')
        }),
        ('Settings', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin interface for Project model."""
    list_display = ['name', 'status', 'priority', 'project_manager', 'start_date', 'deadline', 'completion_percentage']
    list_filter = ['status', 'priority', 'category', 'start_date', 'deadline', 'completion_percentage']
    search_fields = ['name', 'description', 'project_manager__username']
    readonly_fields = ['project_id', 'created_at', 'updated_at', 'completion_percentage']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('project_id', 'name', 'description', 'category')
        }),
        ('Project Management', {
            'fields': ('priority', 'status')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date', 'deadline')
        }),
        ('Budget & Resources', {
            'fields': ('budget', 'spent_budget')
        }),
        ('Progress', {
            'fields': ('completion_percentage',)
        }),
        ('Project Team', {
            'fields': ('project_manager',)  # team_members handled via inline
        }),
        ('Project Details', {
            'fields': ('objectives', 'requirements', 'deliverables')
        }),
        ('Risk Management', {
            'fields': ('risk_level', 'risk_description')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'updated_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProjectMemberInline, TaskInline, ProjectAuditLogInline, ProjectReportInline]
    
    def get_readonly_fields(self, request, obj=None):
        """Make project_id readonly after creation."""
        readonly_fields = list(self.readonly_fields)
        if obj:  # editing an existing object
            readonly_fields.extend(['project_id'])
        return readonly_fields

@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    """Admin interface for ProjectMember model."""
    list_display = ['user', 'project', 'role', 'joined_date', 'is_active']
    list_filter = ['role', 'is_active', 'joined_date', 'project__category']
    search_fields = ['user__username', 'user__email', 'project__name']
    
    fieldsets = (
        ('Membership Details', {
            'fields': ('project', 'user', 'role', 'is_active')
        }),
        ('Join Information', {
            'fields': ('joined_date',)
        }),
    )

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin interface for Task model."""
    list_display = ['title', 'project', 'category', 'type', 'priority', 'status', 'assigned_to', 'due_date', 'completion_percentage']
    list_filter = ['category', 'type', 'priority', 'status', 'project', 'assigned_to', 'due_date']
    search_fields = ['title', 'description', 'project__name', 'assigned_to__username', 'category__name']
    readonly_fields = ['task_id', 'created_at', 'updated_at', 'completion_percentage']
    date_hierarchy = 'due_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('task_id', 'title', 'description', 'project', 'category')
        }),
        ('Task Management', {
            'fields': ('type', 'priority', 'status')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Timeline', {
            'fields': ('start_date', 'due_date', 'completed_date')
        }),
        ('Estimation', {
            'fields': ('estimated_hours', 'actual_hours')
        }),
        ('Task Hierarchy', {
            'fields': ('parent_task',)
        }),
        ('Progress', {
            'fields': ('completion_percentage',)
        }),
        ('Additional Fields', {
            'fields': ('tags', 'dependencies')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make task_id readonly after creation."""
        readonly_fields = list(self.readonly_fields)
        if obj:  # editing an existing object
            readonly_fields.extend(['task_id'])
        return readonly_fields

@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """Admin interface for TaskComment model."""
    list_display = ['task', 'user', 'comment_preview', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at', 'task__project']
    search_fields = ['task__title', 'user__username', 'comment']
    
    def comment_preview(self, obj):
        return obj.comment[:50] + "..." if len(obj.comment) > 50 else obj.comment
    comment_preview.short_description = 'Comment'
    
    fieldsets = (
        ('Comment Details', {
            'fields': ('task', 'user', 'comment', 'is_internal')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TaskAttachment)
class TaskAttachmentAdmin(admin.ModelAdmin):
    """Admin interface for TaskAttachment model."""
    list_display = ['filename', 'task', 'user', 'file_size_display', 'created_at']
    list_filter = ['created_at', 'task__project', 'mime_type']
    search_fields = ['filename', 'task__title', 'user__username', 'description']
    readonly_fields = ['created_at']
    
    def file_size_display(self, obj):
        """Display file size in human readable format."""
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    file_size_display.short_description = 'File Size'
    
    fieldsets = (
        ('Attachment Details', {
            'fields': ('task', 'user', 'file', 'filename', 'description')
        }),
        ('File Information', {
            'fields': ('file_size', 'mime_type')
        }),
        ('Upload Information', {
            'fields': ('created_at',)
        }),
    )

@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    """Admin interface for ProjectTemplate model."""
    list_display = ['name', 'category', 'created_by', 'is_public', 'usage_count', 'created_at']
    list_filter = ['category', 'is_public', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Template Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Configuration', {
            'fields': ('default_tasks', 'default_settings')
        }),
        ('Template Metadata', {
            'fields': ('created_by', 'is_public', 'usage_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ProjectAuditLog)
class ProjectAuditLogAdmin(admin.ModelAdmin):
    """Admin interface for ProjectAuditLog model."""
    list_display = ['project', 'user', 'action', 'task', 'timestamp']
    list_filter = ['action', 'timestamp', 'project__category']
    search_fields = ['project__name', 'user__username', 'description']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Audit Details', {
            'fields': ('project', 'user', 'action', 'description')
        }),
        ('Changes', {
            'fields': ('old_values', 'new_values')
        }),
        ('Task Association', {
            'fields': ('task',)
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Timestamp', {
            'fields': ('timestamp',)
        }),
    )

@admin.register(ProjectReport)
class ProjectReportAdmin(admin.ModelAdmin):
    """Admin interface for ProjectReport model."""
    list_display = ['title', 'project', 'report_type', 'generated_by', 'generated_at', 'is_scheduled']
    list_filter = ['report_type', 'is_scheduled', 'schedule_frequency', 'generated_at']
    search_fields = ['title', 'description', 'project__name']
    readonly_fields = ['generated_at']
    date_hierarchy = 'generated_at'
    
    fieldsets = (
        ('Report Information', {
            'fields': ('project', 'report_type', 'title', 'description')
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

