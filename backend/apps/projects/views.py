"""
Project views for IT Management Platform.
API endpoints for project and task management with role-based access control.
"""

from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime, timedelta

from apps.projects.models import (
    ProjectCategory, Project, ProjectMember, Task, TaskComment,
    TaskAttachment, ProjectTemplate, ProjectAuditLog, ProjectReport
)
from apps.projects.serializers import (
    ProjectCategorySerializer, ProjectListSerializer, ProjectDetailSerializer,
    ProjectCreateSerializer, ProjectUpdateSerializer, TaskListSerializer,
    TaskDetailSerializer, TaskCreateSerializer, TaskUpdateSerializer,
    TaskCommentSerializer, TaskAttachmentSerializer, ProjectTemplateSerializer,
    ProjectAuditLogSerializer, ProjectReportSerializer, ProjectStatisticsSerializer,
    ProjectSearchSerializer, TaskSearchSerializer
)
from apps.projects.permissions import (
    CanManageProjects, IsProjectManagerOrReadOnly, IsProjectMember,
    CanCreateProjects, CanManageProjectMembers, CanViewProjectDetails,
    CanManageTasks, IsTaskAssigneeOrCreator, CanViewTaskComments,
    CanCreateTaskComments, CanManageTaskAttachments, CanViewProjectReports,
    CanGenerateProjectReports, CanManageProjectTemplates, CanUseProjectTemplates,
    CanViewProjectAuditLogs
)
from apps.projects.domain.services.project_authority import (
    assert_can_create_project, assert_can_update_project,
    assert_can_delete_project, assert_can_assign_project_members
)
from apps.core.exceptions import PermissionDeniedError
from apps.core.domain.authorization import AuthorizationError
from apps.users.models import User

class ProjectCategoryViewSet(viewsets.ModelViewSet):
    """
    Project category management viewset.
    """
    queryset = ProjectCategory.objects.all()
    serializer_class = ProjectCategorySerializer
    permission_classes = [CanManageProjects]
    
    def get_queryset(self):
        queryset = ProjectCategory.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('name')

class ProjectViewSet(viewsets.ModelViewSet):
    """
    Project management viewset with comprehensive filtering and actions.
    """
    permission_classes = [CanManageProjects, IsProjectManagerOrReadOnly, IsProjectMember]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action == 'retrieve':
            return ProjectDetailSerializer
        elif self.action == 'create':
            return ProjectCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return ProjectUpdateSerializer
        return ProjectDetailSerializer
    
    def get_queryset(self):
        queryset = Project.objects.select_related(
            'category', 'project_manager', 'created_by', 'updated_by'
        ).prefetch_related('team_members', 'tasks', 'memberships')
        
        # Filter by project manager
        project_manager = self.request.query_params.get('project_manager')
        if project_manager:
            queryset = queryset.filter(project_manager_id=project_manager)
        
        # Filter by team member
        team_member = self.request.query_params.get('team_member')
        if team_member:
            queryset = queryset.filter(team_members__id=team_member)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by overdue projects
        overdue = self.request.query_params.get('overdue')
        if overdue and overdue.lower() == 'true':
            queryset = queryset.filter(
                deadline__isnull=False,
                deadline__lt=timezone.now().date(),
                status__in=['PLANNING', 'ACTIVE', 'ON_HOLD']
            )
        
        # Date range filtering
        start_date_from = self.request.query_params.get('start_date_from')
        start_date_to = self.request.query_params.get('start_date_to')
        
        if start_date_from:
            queryset = queryset.filter(start_date__gte=start_date_from)
        if start_date_to:
            queryset = queryset.filter(start_date__lte=start_date_to)
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(objectives__icontains=search) |
                Q(requirements__icontains=search)
            )
        
        # For non-admin users, only show projects they are members of
        if not self.request.user.is_admin and not self.request.user.can_manage_projects:
            queryset = queryset.filter(
                Q(project_manager=self.request.user) |
                Q(team_members=self.request.user)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        try:
            assert_can_create_project(self.request.user)
        except AuthorizationError:
            raise PermissionDeniedError(
                "You do not have permission to create projects"
            )
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        project = serializer.instance
        try:
            assert_can_update_project(self.request.user, project)
        except AuthorizationError:
            raise PermissionDeniedError(
                "You do not have permission to update this project"
            )
        serializer.save(updated_by=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to properly handle cascade deletion and signal disconnection.
        """
        from django.db.models.signals import pre_delete
        from django.db import transaction
        
        instance = self.get_object()
        
        # Check authorization before deletion
        try:
            assert_can_delete_project(self.request.user, instance)
        except AuthorizationError:
            raise PermissionDeniedError(
                "You do not have permission to delete this project"
            )
        
        # Temporarily disconnect the pre_delete signal to prevent
        # creating a ProjectAuditLog while the project is being deleted
        try:
            from apps.projects.signals import create_project_deletion_log
            pre_delete.disconnect(create_project_deletion_log, sender=Project)
            signal_disconnected = True
        except Exception:
            signal_disconnected = False
        
        try:
            with transaction.atomic():
                # Delete related TaskComment records (via tasks)
                TaskComment.objects.filter(task__project=instance).delete()
                
                # Delete related TaskAttachment records (via tasks)
                TaskAttachment.objects.filter(task__project=instance).delete()
                
                # Delete related ProjectMember records
                ProjectMember.objects.filter(project=instance).delete()
                
                # Delete related ProjectAuditLog records
                ProjectAuditLog.objects.filter(project=instance).delete()
                
                # Delete related ProjectReport records
                ProjectReport.objects.filter(project=instance).delete()
                
                # Delete tasks (this will also delete subtasks via CASCADE)
                Task.objects.filter(project=instance).delete()
                
                # Delete the project (M2M team_members will be cleared automatically)
                instance.delete()
                
                return Response(
                    {'message': f'Project "{instance.name}" deleted successfully.'},
                    status=status.HTTP_200_OK
                )
        finally:
            # Reconnect the signal if it was disconnected
            if signal_disconnected:
                try:
                    pre_delete.connect(create_project_deletion_log, sender=Project)
                except Exception:
                    pass
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the project."""
        project = self.get_object()
        
        # Check authorization
        try:
            assert_can_assign_project_members(self.request.user, project)
        except AuthorizationError:
            raise PermissionDeniedError(
                "You do not have permission to assign project members"
            )
        
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'MEMBER')
        
        if not user_id:
            return Response({'error': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user is already a member
        if ProjectMember.objects.filter(project=project, user=user).exists():
            return Response({'error': 'User is already a member of this project'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create membership
        membership = ProjectMember.objects.create(
            project=project,
            user=user,
            role=role
        )
        
        # Add user to project team
        project.team_members.add(user)
        
        return Response({'message': 'Member added successfully'})
    
    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from the project."""
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Cannot remove project manager
        if project.project_manager == user:
            return Response({'error': 'Cannot remove project manager'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Remove membership
        ProjectMember.objects.filter(project=project, user=user).delete()
        
        # Remove user from project team
        project.team_members.remove(user)
        
        return Response({'message': 'Member removed successfully'})
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """Get project members."""
        project = self.get_object()
        memberships = project.memberships.select_related('user').all()
        serializer = ProjectMemberSerializer(memberships, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change project status."""
        project = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = project.status
        project.status = new_status
        project.save()
        
        return Response({'message': f'Status changed from {old_status} to {new_status}'})
    
    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Get project tasks."""
        project = self.get_object()
        tasks = project.tasks.select_related('assigned_to', 'created_by').all()
        
        # Apply task filters
        status = request.query_params.get('status')
        if status:
            tasks = tasks.filter(status=status)
        
        priority = request.query_params.get('priority')
        if priority:
            tasks = tasks.filter(priority=priority)
        
        assigned_to = request.query_params.get('assigned_to')
        if assigned_to:
            tasks = tasks.filter(assigned_to_id=assigned_to)
        
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def audit_logs(self, request, pk=None):
        """Get project audit logs."""
        project = self.get_object()
        audit_logs = project.audit_logs.select_related('user', 'task').all()
        serializer = ProjectAuditLogSerializer(audit_logs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reports(self, request, pk=None):
        """Get project reports."""
        project = self.get_object()
        reports = project.reports.select_related('generated_by').all()
        serializer = ProjectReportSerializer(reports, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get project statistics."""
        # Cache statistics for 5 minutes
        cache_key = f'project_statistics_{request.user.id}'
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            return Response(cached_stats)
        
        total_projects = Project.objects.count()
        active_projects = Project.objects.filter(status='ACTIVE').count()
        completed_projects = Project.objects.filter(status='COMPLETED').count()
        overdue_projects = Project.objects.filter(
            deadline__isnull=False,
            deadline__lt=timezone.now().date(),
            status__in=['PLANNING', 'ACTIVE', 'ON_HOLD']
        ).count()
        
        projects_by_status = dict(
            Project.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        
        projects_by_priority = dict(
            Project.objects.values('priority').annotate(count=Count('id')).values_list('priority', 'count')
        )
        
        projects_by_category = dict(
            Project.objects.values('category__name').annotate(count=Count('id')).values_list('category__name', 'count')
        )
        
        total_tasks = Task.objects.count()
        completed_tasks = Task.objects.filter(status='COMPLETED').count()
        overdue_tasks = Task.objects.filter(
            due_date__isnull=False,
            due_date__lt=timezone.now().date(),
            status__in=['TODO', 'IN_PROGRESS', 'IN_REVIEW']
        ).count()
        
        tasks_by_status = dict(
            Task.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        
        tasks_by_priority = dict(
            Task.objects.values('priority').annotate(count=Count('id')).values_list('priority', 'count')
        )
        
        recent_activities = ProjectAuditLog.objects.select_related('project', 'user')[:10]
        
        upcoming_deadlines = Task.objects.filter(
            due_date__isnull=False,
            due_date__gte=timezone.now().date(),
            due_date__lte=timezone.now().date() + timedelta(days=7),
            status__in=['TODO', 'IN_PROGRESS', 'IN_REVIEW']
        ).select_related('project', 'assigned_to')[:10]
        
        stats = {
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
            'overdue_projects': overdue_projects,
            'projects_by_status': projects_by_status,
            'projects_by_priority': projects_by_priority,
            'projects_by_category': projects_by_category,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'overdue_tasks': overdue_tasks,
            'tasks_by_status': tasks_by_status,
            'tasks_by_priority': tasks_by_priority,
            'recent_activities': ProjectAuditLogSerializer(recent_activities, many=True).data,
            'upcoming_deadlines': TaskListSerializer(upcoming_deadlines, many=True).data
        }
        
        cache.set(cache_key, stats, 300)  # Cache for 5 minutes
        return Response(stats)

class TaskViewSet(viewsets.ModelViewSet):
    """
    Task management viewset with comprehensive filtering and actions.
    """
    permission_classes = [CanManageTasks, IsTaskAssigneeOrCreator, IsProjectMember]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        elif self.action == 'retrieve':
            return TaskDetailSerializer
        elif self.action == 'create':
            return TaskCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return TaskUpdateSerializer
        return TaskDetailSerializer
    
    def get_queryset(self):
        queryset = Task.objects.select_related(
            'project', 'assigned_to', 'created_by', 'parent_task'
        ).prefetch_related('dependencies', 'comments', 'attachments')
        
        # Filter by project
        project = self.request.query_params.get('project')
        if project:
            queryset = queryset.filter(project_id=project)
        
        # Filter by assigned user
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        
        # Filter by creator
        created_by = self.request.query_params.get('created_by')
        if created_by:
            queryset = queryset.filter(created_by_id=created_by)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by type
        type = self.request.query_params.get('type')
        if type:
            queryset = queryset.filter(type=type)
        
        # Filter by overdue tasks
        overdue = self.request.query_params.get('overdue')
        if overdue and overdue.lower() == 'true':
            queryset = queryset.filter(
                due_date__isnull=False,
                due_date__lt=timezone.now().date(),
                status__in=['TODO', 'IN_PROGRESS', 'IN_REVIEW']
            )
        
        # Date range filtering
        due_date_from = self.request.query_params.get('due_date_from')
        due_date_to = self.request.query_params.get('due_date_to')
        
        if due_date_from:
            queryset = queryset.filter(due_date__gte=due_date_from)
        if due_date_to:
            queryset = queryset.filter(due_date__lte=due_date_to)
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        # For non-admin users, only show tasks from projects they are members of
        if not self.request.user.is_admin and not self.request.user.can_manage_projects:
            queryset = queryset.filter(
                Q(project__project_manager=self.request.user) |
                Q(project__team_members=self.request.user) |
                Q(assigned_to=self.request.user) |
                Q(created_by=self.request.user)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark task as completed."""
        task = self.get_object()
        task.mark_completed()
        
        return Response({'message': 'Task marked as completed'})
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change task status."""
        task = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = task.status
        task.status = new_status
        
        if new_status == 'COMPLETED':
            task.completed_date = timezone.now()
            task.completion_percentage = 100
        
        task.save()
        
        # Update parent project completion percentage
        task.project.update_completion_percentage()
        
        return Response({'message': f'Status changed from {old_status} to {new_status}'})
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get task comments."""
        task = self.get_object()
        comments = task.comments.select_related('user').all()
        serializer = TaskCommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def attachments(self, request, pk=None):
        """Get task attachments."""
        task = self.get_object()
        attachments = task.attachments.select_related('user').all()
        serializer = TaskAttachmentSerializer(attachments, many=True)
        return Response(serializer.data)

class TaskCommentViewSet(viewsets.ModelViewSet):
    """
    Task comment management viewset.
    """
    serializer_class = TaskCommentSerializer
    permission_classes = [CanViewTaskComments, CanCreateTaskComments]
    
    def get_queryset(self):
        queryset = TaskComment.objects.select_related('task', 'user')
        
        # Filter by task
        task = self.request.query_params.get('task')
        if task:
            queryset = queryset.filter(task_id=task)
        
        # Filter by user
        user = self.request.query_params.get('user')
        if user:
            queryset = queryset.filter(user_id=user)
        
        return queryset.order_by('created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TaskAttachmentViewSet(viewsets.ModelViewSet):
    """
    Task attachment management viewset.
    """
    serializer_class = TaskAttachmentSerializer
    permission_classes = [CanManageTaskAttachments]
    
    def get_queryset(self):
        queryset = TaskAttachment.objects.select_related('task', 'user')
        
        # Filter by task
        task = self.request.query_params.get('task')
        if task:
            queryset = queryset.filter(task_id=task)
        
        # Filter by user
        user = self.request.query_params.get('user')
        if user:
            queryset = queryset.filter(user_id=user)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ProjectTemplateViewSet(viewsets.ModelViewSet):
    """
    Project template management viewset.
    """
    serializer_class = ProjectTemplateSerializer
    permission_classes = [CanManageProjectTemplates, CanUseProjectTemplates]
    
    def get_queryset(self):
        queryset = ProjectTemplate.objects.select_related('category', 'created_by')
        
        # Only show public templates or templates created by current user
        if not self.request.user.is_admin:
            queryset = queryset.filter(
                Q(is_public=True) | Q(created_by=self.request.user)
            )
        
        return queryset.order_by('-usage_count', 'name')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Use template to create a new project."""
        template = self.get_object()
        
        # Increment usage count
        template.usage_count += 1
        template.save()
        
        # Create project from template (implementation would depend on template structure)
        return Response({'message': 'Template usage recorded'})

class ProjectAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Project audit log viewset.
    """
    serializer_class = ProjectAuditLogSerializer
    permission_classes = [CanViewProjectAuditLogs]
    
    def get_queryset(self):
        queryset = ProjectAuditLog.objects.select_related('project', 'user', 'task')
        
        # Filter by project
        project = self.request.query_params.get('project')
        if project:
            queryset = queryset.filter(project_id=project)
        
        # Filter by user
        user = self.request.query_params.get('user')
        if user:
            queryset = queryset.filter(user_id=user)
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        return queryset.order_by('-timestamp')[:1000]  # Limit to recent 1000 records

class ProjectSearchView(APIView):
    """
    Advanced project search endpoint.
    """
    permission_classes = [CanManageProjects]
    
    def post(self, request):
        serializer = ProjectSearchSerializer(data=request.data)
        
        if serializer.is_valid():
            queryset = Project.objects.select_related('category', 'project_manager')
            
            # Apply filters
            search = serializer.validated_data.get('search')
            status = serializer.validated_data.get('status')
            priority = serializer.validated_data.get('priority')
            category = serializer.validated_data.get('category')
            project_manager = serializer.validated_data.get('project_manager')
            team_member = serializer.validated_data.get('team_member')
            overdue = serializer.validated_data.get('overdue')
            start_date_from = serializer.validated_data.get('start_date_from')
            start_date_to = serializer.validated_data.get('start_date_to')
            
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(description__icontains=search) |
                    Q(objectives__icontains=search) |
                    Q(requirements__icontains=search)
                )
            
            if status:
                queryset = queryset.filter(status=status)
            
            if priority:
                queryset = queryset.filter(priority=priority)
            
            if category:
                queryset = queryset.filter(category_id=category)
            
            if project_manager:
                queryset = queryset.filter(project_manager_id=project_manager)
            
            if team_member:
                queryset = queryset.filter(team_members__id=team_member)
            
            if overdue:
                queryset = queryset.filter(
                    deadline__isnull=False,
                    deadline__lt=timezone.now().date(),
                    status__in=['PLANNING', 'ACTIVE', 'ON_HOLD']
                )
            
            if start_date_from:
                queryset = queryset.filter(start_date__gte=start_date_from)
            if start_date_to:
                queryset = queryset.filter(start_date__lte=start_date_to)
            
            # Paginate results
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            start = (page - 1) * page_size
            end = start + page_size
            
            results = queryset.order_by('-created_at')[start:end]
            total_count = queryset.count()
            
            response_data = {
                'results': ProjectListSerializer(results, many=True).data,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            }
            
            return Response(response_data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TaskSearchView(APIView):
    """
    Advanced task search endpoint.
    """
    permission_classes = [CanManageTasks]
    
    def post(self, request):
        serializer = TaskSearchSerializer(data=request.data)
        
        if serializer.is_valid():
            queryset = Task.objects.select_related('project', 'assigned_to', 'created_by')
            
            # Apply filters
            search = serializer.validated_data.get('search')
            project = serializer.validated_data.get('project')
            status = serializer.validated_data.get('status')
            priority = serializer.validated_data.get('priority')
            type = serializer.validated_data.get('type')
            assigned_to = serializer.validated_data.get('assigned_to')
            created_by = serializer.validated_data.get('created_by')
            overdue = serializer.validated_data.get('overdue')
            due_date_from = serializer.validated_data.get('due_date_from')
            due_date_to = serializer.validated_data.get('due_date_to')
            
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search)
                )
            
            if project:
                queryset = queryset.filter(project_id=project)
            
            if status:
                queryset = queryset.filter(status=status)
            
            if priority:
                queryset = queryset.filter(priority=priority)
            
            if type:
                queryset = queryset.filter(type=type)
            
            if assigned_to:
                queryset = queryset.filter(assigned_to_id=assigned_to)
            
            if created_by:
                queryset = queryset.filter(created_by_id=created_by)
            
            if overdue:
                queryset = queryset.filter(
                    due_date__isnull=False,
                    due_date__lt=timezone.now().date(),
                    status__in=['TODO', 'IN_PROGRESS', 'IN_REVIEW']
                )
            
            if due_date_from:
                queryset = queryset.filter(due_date__gte=due_date_from)
            if due_date_to:
                queryset = queryset.filter(due_date__lte=due_date_to)
            
            # Paginate results
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            start = (page - 1) * page_size
            end = start + page_size
            
            results = queryset.order_by('-created_at')[start:end]
            total_count = queryset.count()
            
            response_data = {
                'results': TaskListSerializer(results, many=True).data,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            }
            
            return Response(response_data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
