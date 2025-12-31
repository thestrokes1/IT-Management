"""
Project serializers for IT Management Platform.
Handles serialization and validation for project and task operations.
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import datetime

from apps.projects.models import (
    ProjectCategory, TaskCategory, Project, ProjectMember, Task, TaskComment,
    TaskAttachment, ProjectTemplate, ProjectAuditLog, ProjectReport
)
from apps.users.models import User

class ProjectCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for project categories.
    """
    class Meta:
        model = ProjectCategory
        fields = ['id', 'name', 'description', 'color', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class TaskCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for task categories.
    """
    task_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = TaskCategory
        fields = ['id', 'name', 'description', 'color', 'is_active', 'task_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'task_count', 'created_at', 'updated_at']

class ProjectMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for project members.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = ProjectMember
        fields = ['id', 'user', 'user_username', 'user_email', 'user_full_name', 'role', 'joined_date', 'is_active']
        read_only_fields = ['id', 'joined_date']

class ProjectListSerializer(serializers.ModelSerializer):
    """
    Serializer for project list view.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    project_manager_name = serializers.CharField(source='project_manager.username', read_only=True)
    total_tasks = serializers.IntegerField(read_only=True)
    completed_tasks = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'project_id', 'name', 'description', 'category_name',
            'priority', 'status', 'start_date', 'end_date', 'deadline',
            'budget', 'completion_percentage', 'project_manager_name',
            'total_tasks', 'completed_tasks', 'is_overdue', 'created_at'
        ]
        read_only_fields = ['id', 'project_id', 'created_at']

class ProjectDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for project detail view.
    """
    category = ProjectCategorySerializer(read_only=True)
    project_manager = serializers.StringRelatedField(read_only=True)
    team_members = serializers.StringRelatedField(many=True, read_only=True)
    memberships = ProjectMemberSerializer(source='memberships', many=True, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_until_deadline = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    total_tasks = serializers.IntegerField(read_only=True)
    completed_tasks = serializers.IntegerField(read_only=True)
    pending_tasks = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'project_id', 'name', 'description', 'category',
            'priority', 'status', 'start_date', 'end_date', 'deadline',
            'budget', 'spent_budget', 'completion_percentage',
            'project_manager', 'team_members', 'memberships',
            'objectives', 'requirements', 'deliverables',
            'risk_level', 'risk_description',
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'is_overdue', 'days_until_deadline', 'is_active',
            'total_tasks', 'completed_tasks', 'pending_tasks'
        ]
        read_only_fields = [
            'id', 'project_id', 'created_at', 'updated_at', 'is_overdue',
            'days_until_deadline', 'is_active', 'total_tasks', 'completed_tasks', 'pending_tasks'
        ]

class ProjectCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating projects.
    """
    team_member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'category', 'priority', 'status',
            'start_date', 'end_date', 'deadline', 'budget', 'objectives',
            'requirements', 'deliverables', 'risk_level', 'risk_description',
            'team_member_ids'
        ]
    
    def validate(self, attrs):
        # Validate dates
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        deadline = attrs.get('deadline')
        
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("End date cannot be before start date.")
        
        if deadline and start_date and deadline < start_date:
            raise serializers.ValidationError("Deadline cannot be before start date.")
        
        return attrs
    
    def create(self, validated_data):
        team_member_ids = validated_data.pop('team_member_ids', [])
        
        project = Project.objects.create(**validated_data)
        
        # Add team members
        for user_id in team_member_ids:
            try:
                user = User.objects.get(id=user_id)
                ProjectMember.objects.create(project=project, user=user)
            except User.DoesNotExist:
                continue
        
        return project

class ProjectUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating projects.
    """
    team_member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'priority', 'status',
            'start_date', 'end_date', 'deadline', 'budget', 'objectives',
            'requirements', 'deliverables', 'risk_level', 'risk_description',
            'team_member_ids'
        ]
    
    def update(self, instance, validated_data):
        team_member_ids = validated_data.pop('team_member_ids', None)
        
        # Update project fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update team members if provided
        if team_member_ids is not None:
            # Remove existing members not in the new list
            ProjectMember.objects.filter(project=instance).exclude(
                user_id__in=team_member_ids
            ).delete()
            
            # Add new members
            for user_id in team_member_ids:
                ProjectMember.objects.get_or_create(
                    project=instance,
                    user_id=user_id
                )
        
        return instance

class TaskListSerializer(serializers.ModelSerializer):
    """
    Serializer for task list view.
    """
    project_name = serializers.CharField(source='project.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    is_subtask = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'task_id', 'title', 'description', 'project_name',
            'category', 'category_name', 'type', 'priority', 'status',
            'assigned_to_username', 'created_by_username', 'start_date',
            'due_date', 'estimated_hours', 'completion_percentage',
            'is_overdue', 'is_subtask', 'created_at'
        ]
        read_only_fields = ['id', 'task_id', 'created_at']

class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for task detail view.
    """
    project = ProjectListSerializer(read_only=True)
    category = TaskCategorySerializer(read_only=True)
    assigned_to = serializers.StringRelatedField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    parent_task = serializers.StringRelatedField(read_only=True)
    dependencies = TaskListSerializer(many=True, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_until_due = serializers.IntegerField(read_only=True)
    is_subtask = serializers.BooleanField(read_only=True)
    has_subtasks = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'task_id', 'title', 'description', 'project', 'category',
            'type', 'priority', 'status', 'assigned_to', 'created_by',
            'start_date', 'due_date', 'completed_date',
            'estimated_hours', 'actual_hours', 'parent_task',
            'dependencies', 'completion_percentage', 'tags',
            'created_at', 'updated_at', 'is_overdue', 'days_until_due',
            'is_subtask', 'has_subtasks'
        ]
        read_only_fields = [
            'id', 'task_id', 'created_at', 'updated_at', 'is_overdue',
            'days_until_due', 'is_subtask', 'has_subtasks'
        ]

class TaskCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating tasks.
    """
    dependency_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'project', 'type', 'priority',
            'start_date', 'due_date', 'estimated_hours', 'parent_task',
            'completion_percentage', 'tags', 'dependency_ids'
        ]
    
    def create(self, validated_data):
        dependency_ids = validated_data.pop('dependency_ids', [])
        validated_data['created_by'] = self.context['request'].user
        
        task = Task.objects.create(**validated_data)
        
        # Add dependencies
        for dep_id in dependency_ids:
            try:
                dep_task = Task.objects.get(task_id=dep_id)
                task.dependencies.add(dep_task)
            except Task.DoesNotExist:
                continue
        
        return task

class TaskUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating tasks.
    """
    dependency_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Task
        fields = [
            'title', 'description', 'type', 'priority', 'status',
            'assigned_to', 'start_date', 'due_date', 'estimated_hours',
            'actual_hours', 'parent_task', 'completion_percentage', 'tags',
            'dependency_ids'
        ]
    
    def update(self, instance, validated_data):
        dependency_ids = validated_data.pop('dependency_ids', None)
        
        # Handle status changes
        old_status = instance.status
        new_status = validated_data.get('status')
        
        if new_status == 'COMPLETED' and old_status != 'COMPLETED':
            validated_data['completed_date'] = timezone.now()
            validated_data['completion_percentage'] = 100
        
        # Update task fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update dependencies if provided
        if dependency_ids is not None:
            instance.dependencies.clear()
            for dep_id in dependency_ids:
                try:
                    dep_task = Task.objects.get(task_id=dep_id)
                    instance.dependencies.add(dep_task)
                except Task.DoesNotExist:
                    continue
        
        # Update parent project completion percentage
        instance.project.update_completion_percentage()
        
        return instance

class TaskCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for task comments.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = TaskComment
        fields = ['id', 'task', 'user', 'user_username', 'user_full_name', 'comment', 'is_internal', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'user_username', 'user_full_name', 'created_at', 'updated_at']

class TaskAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for task attachments.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TaskAttachment
        fields = ['id', 'task', 'user', 'user_username', 'file', 'filename', 'file_size', 'mime_type', 'description', 'created_at']
        read_only_fields = ['id', 'user', 'user_username', 'file_size', 'mime_type', 'created_at']

class ProjectTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for project templates.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ProjectTemplate
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'default_tasks', 'default_settings', 'created_by',
            'created_by_username', 'is_public', 'usage_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_by_username', 'usage_count', 'created_at', 'updated_at']

class ProjectAuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for project audit logs.
    """
    project_name = serializers.CharField(source='project.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    
    class Meta:
        model = ProjectAuditLog
        fields = [
            'id', 'project', 'project_name', 'user', 'user_username',
            'action', 'description', 'old_values', 'new_values',
            'task', 'task_title', 'ip_address', 'user_agent', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']

class ProjectReportSerializer(serializers.ModelSerializer):
    """
    Serializer for project reports.
    """
    project_name = serializers.CharField(source='project.name', read_only=True)
    generated_by_username = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = ProjectReport
        fields = [
            'id', 'project', 'project_name', 'report_type', 'title',
            'description', 'parameters', 'generated_by', 'generated_by_username',
            'generated_at', 'file_path', 'is_scheduled', 'schedule_frequency'
        ]
        read_only_fields = ['id', 'generated_at', 'generated_by_username']

class ProjectStatisticsSerializer(serializers.Serializer):
    """
    Serializer for project statistics.
    """
    total_projects = serializers.IntegerField()
    active_projects = serializers.IntegerField()
    completed_projects = serializers.IntegerField()
    overdue_projects = serializers.IntegerField()
    projects_by_status = serializers.DictField()
    projects_by_priority = serializers.DictField()
    projects_by_category = serializers.DictField()
    total_tasks = serializers.IntegerField()
    completed_tasks = serializers.IntegerField()
    overdue_tasks = serializers.IntegerField()
    tasks_by_status = serializers.DictField()
    tasks_by_priority = serializers.DictField()
    recent_activities = serializers.ListField()
    upcoming_deadlines = TaskListSerializer(many=True)

class ProjectSearchSerializer(serializers.Serializer):
    """
    Serializer for project search functionality.
    """
    search = serializers.CharField(required=False)
    status = serializers.ChoiceField(choices=Project.STATUS_CHOICES, required=False)
    priority = serializers.ChoiceField(choices=Project.PRIORITY_CHOICES, required=False)
    category = serializers.IntegerField(required=False)
    project_manager = serializers.IntegerField(required=False)
    team_member = serializers.IntegerField(required=False)
    overdue = serializers.BooleanField(required=False)
    start_date_from = serializers.DateField(required=False)
    start_date_to = serializers.DateField(required=False)

class TaskSearchSerializer(serializers.Serializer):
    """
    Serializer for task search functionality.
    """
    search = serializers.CharField(required=False)
    project = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(choices=Task.STATUS_CHOICES, required=False)
    priority = serializers.ChoiceField(choices=Task.PRIORITY_CHOICES, required=False)
    type = serializers.ChoiceField(choices=Task.TYPE_CHOICES, required=False)
    assigned_to = serializers.IntegerField(required=False)
    created_by = serializers.IntegerField(required=False)
    overdue = serializers.BooleanField(required=False)
    due_date_from = serializers.DateField(required=False)
    due_date_to = serializers.DateField(required=False)
