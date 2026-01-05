"""
Project models for IT Management Platform.
Project and task management with comprehensive tracking and assignment.
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from decimal import Decimal

User = get_user_model()

class ProjectCategory(models.Model):
    """
    Categories for organizing projects.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color code
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'project_categories'
        verbose_name = 'Project Category'
        verbose_name_plural = 'Project Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class TaskCategory(models.Model):
    """
    Categories for organizing tasks.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color code
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task_categories'
        verbose_name = 'Task Category'
        verbose_name_plural = 'Task Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Project(models.Model):
    """
    Project model for IT project management.
    """
    # Priority choices
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    # Status choices
    STATUS_CHOICES = [
        ('PLANNING', 'Planning'),
        ('ACTIVE', 'Active'),
        ('ON_HOLD', 'On Hold'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('ARCHIVED', 'Archived'),
    ]
    
    # Project ID (unique identifier)
    project_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Basic information
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(ProjectCategory, on_delete=models.PROTECT, related_name='projects')
    
    # Project management
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    
    # Timeline
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    
    # Budget and resources
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    spent_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Progress tracking
    completion_percentage = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Project team
    project_manager = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name='managed_projects'
    )
    team_members = models.ManyToManyField(
        User, through='ProjectMember', related_name='project_participations'
    )
    
    # Project details
    objectives = models.TextField(blank=True)
    requirements = models.TextField(blank=True)
    deliverables = models.TextField(blank=True)
    
    # Risk management
    risk_level = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    risk_description = models.TextField(blank=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects_updated')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'projects'
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['project_manager']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['deadline']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    @property
    def is_overdue(self):
        """Check if project is overdue."""
        if not self.deadline:
            return False
        return timezone.now().date() > self.deadline and self.status not in ['COMPLETED', 'CANCELLED']
    
    @property
    def days_until_deadline(self):
        """Get days until deadline."""
        if not self.deadline:
            return None
        return (self.deadline - timezone.now().date()).days
    
    @property
    def is_active(self):
        """Check if project is currently active."""
        return self.status == 'ACTIVE'
    
    @property
    def total_tasks(self):
        """Get total number of tasks."""
        return self.tasks.count()
    
    @property
    def completed_tasks(self):
        """Get number of completed tasks."""
        return self.tasks.filter(status='COMPLETED').count()
    
    @property
    def pending_tasks(self):
        """Get number of pending tasks."""
        return self.tasks.exclude(status='COMPLETED').count()
    
    def update_completion_percentage(self):
        """Update project completion percentage based on tasks."""
        total_tasks = self.total_tasks
        if total_tasks == 0:
            new_percentage = 0
        else:
            new_percentage = int((self.completed_tasks / total_tasks) * 100)
        # Use update() to avoid triggering signals and causing recursion
        Project.objects.filter(pk=self.pk).update(completion_percentage=new_percentage)

class ProjectMember(models.Model):
    """
    Project team membership with roles.
    """
    # Role choices
    ROLE_CHOICES = [
        ('MANAGER', 'Project Manager'),
        ('LEAD', 'Team Lead'),
        ('MEMBER', 'Team Member'),
        ('VIEWER', 'Viewer'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='MEMBER')
    joined_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'project_members'
        verbose_name = 'Project Member'
        verbose_name_plural = 'Project Members'
        unique_together = ['project', 'user']
        ordering = ['joined_date']
    
    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.get_role_display()})"

class Task(models.Model):
    """
    Task model for project tasks and subtasks.
    """
    # Priority choices
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    # Status choices
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('IN_REVIEW', 'In Review'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Task type choices
    TYPE_CHOICES = [
        ('TASK', 'Task'),
        ('BUG', 'Bug Fix'),
        ('FEATURE', 'Feature'),
        ('IMPROVEMENT', 'Improvement'),
        ('DOCUMENTATION', 'Documentation'),
        ('TESTING', 'Testing'),
        ('DEPLOYMENT', 'Deployment'),
    ]
    
    # Task ID (unique identifier)
    task_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Basic information
    title = models.CharField(max_length=200)
    description = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    
    # Category
    category = models.ForeignKey(
        TaskCategory, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='tasks'
    )
    
    # Task management
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='TASK')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='TODO')
    
    # Assignment
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tasks'
    )
    
    # Timeline
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    completed_date = models.DateTimeField(null=True, blank=True)
    
    # Estimation
    estimated_hours = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    
    # Task hierarchy
    parent_task = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='subtasks'
    )
    
    # Progress tracking
    completion_percentage = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Additional fields
    tags = models.JSONField(default=list, blank=True)
    dependencies = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'tasks'
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"
    
    @property
    def is_overdue(self):
        """Check if task is overdue."""
        if not self.due_date:
            return False
        return timezone.now().date() > self.due_date and self.status not in ['COMPLETED', 'CANCELLED']
    
    @property
    def days_until_due(self):
        """Get days until due date."""
        if not self.due_date:
            return None
        return (self.due_date - timezone.now().date()).days
    
    @property
    def is_subtask(self):
        """Check if this is a subtask."""
        return self.parent_task is not None
    
    @property
    def has_subtasks(self):
        """Check if this task has subtasks."""
        return self.subtasks.exists()
    
    def mark_completed(self):
        """Mark task as completed."""
        self.status = 'COMPLETED'
        self.completed_date = timezone.now()
        self.completion_percentage = 100
        self.save()
        
        # Update parent task progress if this is a subtask
        if self.parent_task:
            self.parent_task.update_completion_percentage()

class TaskComment(models.Model):
    """
    Comments and updates for tasks.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_comments')
    comment = models.TextField()
    is_internal = models.BooleanField(default=False)  # Internal notes vs public comments
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'task_comments'
        verbose_name = 'Task Comment'
        verbose_name_plural = 'Task Comments'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.task.title}"

class TaskAttachment(models.Model):
    """
    File attachments for tasks.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_attachments')
    file = models.FileField(upload_to='task_attachments/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'task_attachments'
        verbose_name = 'Task Attachment'
        verbose_name_plural = 'Task Attachments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} - {self.task.title}"

class ProjectTemplate(models.Model):
    """
    Reusable project templates.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(ProjectCategory, on_delete=models.PROTECT, related_name='templates')
    
    # Template configuration
    default_tasks = models.JSONField(default=list, blank=True)
    default_settings = models.JSONField(default=dict, blank=True)
    
    # Template metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_templates')
    is_public = models.BooleanField(default=False)
    usage_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'project_templates'
        verbose_name = 'Project Template'
        verbose_name_plural = 'Project Templates'
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return self.name

class ProjectAuditLog(models.Model):
    """
    Comprehensive audit log for all project changes.
    """
    # Action choices
    ACTION_CHOICES = [
        ('CREATED', 'Created'),
        ('UPDATED', 'Updated'),
        ('DELETED', 'Deleted'),
        ('STATUS_CHANGED', 'Status Changed'),
        ('MEMBER_ADDED', 'Member Added'),
        ('MEMBER_REMOVED', 'Member Removed'),
        ('TASK_CREATED', 'Task Created'),
        ('TASK_UPDATED', 'Task Updated'),
        ('TASK_COMPLETED', 'Task Completed'),
        ('COMMENT_ADDED', 'Comment Added'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='audit_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    description = models.TextField()
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name='audit_logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'project_audit_logs'
        verbose_name = 'Project Audit Log'
        verbose_name_plural = 'Project Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['project', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.project.name} - {self.get_action_display()} - {self.timestamp}"

class ProjectReport(models.Model):
    """
    Project reports and analytics data.
    """
    # Report type choices
    REPORT_TYPE_CHOICES = [
        ('PROJECT_SUMMARY', 'Project Summary'),
        ('TASK_PROGRESS', 'Task Progress'),
        ('TEAM_PERFORMANCE', 'Team Performance'),
        ('BUDGET_ANALYSIS', 'Budget Analysis'),
        ('TIMELINE_REPORT', 'Timeline Report'),
        ('DELIVERABLE_STATUS', 'Deliverable Status'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='reports')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_reports_generated')
    generated_at = models.DateTimeField(auto_now_add=True)
    file_path = models.FilePathField(null=True, blank=True)
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True)
    
    class Meta:
        db_table = 'project_reports'
        verbose_name = 'Project Report'
        verbose_name_plural = 'Project Reports'
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.title} - {self.project.name}"
