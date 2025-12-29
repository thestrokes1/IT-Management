"""
Project signals for IT Management Platform.
Handles project creation, updates, task management, and audit logging.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Project, Task, TaskComment, TaskAttachment, ProjectMember, ProjectAuditLog
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

# DISABLED: ProjectAuditLog signal causing excessive logging (100+ entries per update)
# The post_save signal was creating duplicate logs due to race conditions in comparing old/new values
# Audit logging should be handled at the view layer if needed, not in signals
#
# @receiver(post_save, sender=Project)
# def create_project_audit_log(sender, instance, created, **kwargs):
#     """
#     Create audit log when project is created or updated.
#     """
#     if created:
#         # Log project creation
#         ProjectAuditLog.objects.create(
#             project=instance,
#             user=instance.created_by or User.objects.filter(is_superuser=True).first(),
#             action='CREATED',
#             description=f'Project created: {instance.name}',
#             new_values={
#                 'name': instance.name,
#                 'category': instance.category.name if instance.category else None,
#                 'status': instance.status,
#                 'priority': instance.priority,
#                 'project_manager': instance.project_manager.username
#             }
#         )
#         logger.info(f"Project created: {instance.name} (Manager: {instance.project_manager.username})")
#     else:
#         # Log significant changes for updates
#         try:
#             old_instance = Project.objects.get(pk=instance.pk)
#             changes = []
#             old_values = {}
#             new_values = {}
#             
#             # Check for status changes
#             if old_instance.status != instance.status:
#                 changes.append(f"status: {old_instance.status} -> {instance.status}")
#                 old_values['status'] = old_instance.status
#                 new_values['status'] = instance.status
#             
#             # Check for priority changes
#             if old_instance.priority != instance.priority:
#                 changes.append(f"priority: {old_instance.priority} -> {instance.priority}")
#                 old_values['priority'] = old_instance.priority
#                 new_values['priority'] = instance.priority
#             
#             # Check for deadline changes
#             if old_instance.deadline != instance.deadline:
#                 changes.append(f"deadline: {old_instance.deadline} -> {instance.deadline}")
#                 old_values['deadline'] = str(old_instance.deadline)
#                 new_values['deadline'] = str(instance.deadline)
#             
#             # Check for budget changes
#             if str(old_instance.budget) != str(instance.budget):
#                 changes.append(f"budget: {old_instance.budget} -> {instance.budget}")
#                 old_values['budget'] = str(old_instance.budget)
#                 new_values['budget'] = str(instance.budget)
#             
#             # Check for completion percentage changes
#             if old_instance.completion_percentage != instance.completion_percentage:
#                 changes.append(f"completion_percentage: {old_instance.completion_percentage}% -> {instance.completion_percentage}%")
#                 old_values['completion_percentage'] = old_instance.completion_percentage
#                 new_values['completion_percentage'] = instance.completion_percentage
#             
#             if changes:
#                 ProjectAuditLog.objects.create(
#                     project=instance,
#                     user=instance.updated_by or User.objects.filter(is_superuser=True).first(),
#                     action='UPDATED',
#                     description=f'Project updated: {", ".join(changes)}',
#                     old_values=old_values,
#                     new_values=new_values
#                 )
#                 logger.info(f"Project updated: {instance.name} - {', '.join(changes)}")
#         except Project.DoesNotExist:
#             pass


# DISABLED: Same as above - excessive deletion logging
# @receiver(post_delete, sender=Project)
# def create_project_deletion_log(sender, instance, **kwargs):
#     """
#     Create audit log when project is deleted.
#     """
#     ProjectAuditLog.objects.create(
#         project=instance,
#         user=User.objects.filter(is_superuser=True).first(),  # System deletion
#         action='DELETED',
#         description=f'Project deleted: {instance.name}',
#         old_values={
#             'name': instance.name,
#             'status': instance.status,
#             'project_manager': instance.project_manager.username
#         }
#     )
#     logger.warning(f"Project deleted: {instance.name}")


@receiver(post_save, sender=Task)
def create_task_audit_log(sender, instance, created, **kwargs):
    """
    Create audit log when task is created or updated.
    """
    if created:
        # Log task creation
        ProjectAuditLog.objects.create(
            project=instance.project,
            user=instance.created_by,
            action='TASK_CREATED',
            description=f'Task created: {instance.title}',
            task=instance,
            new_values={
                'title': instance.title,
                'type': instance.type,
                'priority': instance.priority,
                'status': instance.status,
                'assigned_to': instance.assigned_to.username if instance.assigned_to else None,
                'due_date': instance.due_date.isoformat() if instance.due_date else None
            }
        )
        logger.info(f"Task created: {instance.title} in project {instance.project.name}")
    else:
        # Log significant changes for updates
        try:
            old_instance = Task.objects.get(pk=instance.pk)
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
                old_assignee = old_instance.assigned_to.username if old_instance.assigned_to else None
                new_assignee = instance.assigned_to.username if instance.assigned_to else None
                changes.append(f"assigned_to: {old_assignee} -> {new_assignee}")
                old_values['assigned_to'] = old_assignee
                new_values['assigned_to'] = new_assignee
            
            # Check for priority changes
            if old_instance.priority != instance.priority:
                changes.append(f"priority: {old_instance.priority} -> {instance.priority}")
                old_values['priority'] = old_instance.priority
                new_values['priority'] = instance.priority
            
            # Check for due date changes
            if old_instance.due_date != instance.due_date:
                changes.append(f"due_date: {old_instance.due_date} -> {instance.due_date}")
                old_values['due_date'] = str(old_instance.due_date)
                new_values['due_date'] = str(instance.due_date)
            
            # Check for completion percentage changes
            if old_instance.completion_percentage != instance.completion_percentage:
                changes.append(f"completion_percentage: {old_instance.completion_percentage}% -> {instance.completion_percentage}%")
                old_values['completion_percentage'] = old_instance.completion_percentage
                new_values['completion_percentage'] = instance.completion_percentage
            
            if changes:
                ProjectAuditLog.objects.create(
                    project=instance.project,
                    user=instance.created_by,
                    action='TASK_UPDATED',
                    description=f'Task updated: {", ".join(changes)}',
                    task=instance,
                    old_values=old_values,
                    new_values=new_values
                )
                logger.info(f"Task updated: {instance.title} - {', '.join(changes)}")
                
                # If task was marked as completed, log completion
                if old_instance.status != 'COMPLETED' and instance.status == 'COMPLETED':
                    ProjectAuditLog.objects.create(
                        project=instance.project,
                        user=instance.assigned_to or instance.created_by,
                        action='TASK_COMPLETED',
                        description=f'Task completed: {instance.title}',
                        task=instance
                    )
                    logger.info(f"Task completed: {instance.title}")
        except Task.DoesNotExist:
            pass

@receiver(post_delete, sender=Task)
def create_task_deletion_log(sender, instance, **kwargs):
    """
    Create audit log when task is deleted.
    """
    ProjectAuditLog.objects.create(
        project=instance.project,
        user=User.objects.filter(is_superuser=True).first(),  # System deletion
        action='DELETED',
        description=f'Task deleted: {instance.title}',
        task=instance,
        old_values={
            'title': instance.title,
            'status': instance.status,
            'project': instance.project.name
        }
    )
    logger.warning(f"Task deleted: {instance.title}")

@receiver(post_save, sender=TaskComment)
def create_comment_audit_log(sender, instance, created, **kwargs):
    """
    Create audit log when task comment is created.
    """
    if created:
        ProjectAuditLog.objects.create(
            project=instance.task.project,
            user=instance.user,
            action='COMMENT_ADDED',
            description=f'Comment added to task: {instance.task.title}',
            task=instance.task,
            new_values={
                'comment_preview': instance.comment[:100] + '...' if len(instance.comment) > 100 else instance.comment,
                'is_internal': instance.is_internal
            }
        )
        logger.info(f"Comment added to task: {instance.task.title} by {instance.user.username}")

@receiver(post_save, sender=ProjectMember)
def create_member_audit_log(sender, instance, created, **kwargs):
    """
    Create audit log when project member is added or removed.
    """
    if created:
        ProjectAuditLog.objects.create(
            project=instance.project,
            user=User.objects.filter(is_superuser=True).first(),  # System action
            action='MEMBER_ADDED',
            description=f'Member added to project: {instance.user.username} ({instance.get_role_display()})',
            new_values={
                'user': instance.user.username,
                'role': instance.role
            }
        )
        logger.info(f"Member added to project: {instance.project.name} - {instance.user.username}")
    else:
        # This will be handled by post_delete signal
        pass

@receiver(post_delete, sender=ProjectMember)
def create_member_removal_log(sender, instance, **kwargs):
    """
    Create audit log when project member is removed.
    """
    ProjectAuditLog.objects.create(
        project=instance.project,
        user=User.objects.filter(is_superuser=True).first(),  # System action
        action='MEMBER_REMOVED',
        description=f'Member removed from project: {instance.user.username}',
        old_values={
            'user': instance.user.username,
            'role': instance.role
        }
    )
    logger.info(f"Member removed from project: {instance.project.name} - {instance.user.username}")

@receiver(post_save, sender=Project)
def update_project_completion(sender, instance, **kwargs):
    """
    Update project completion percentage based on task progress.
    """
    instance.update_completion_percentage()

@receiver(post_save, sender=Task)
def update_project_on_task_change(sender, instance, created, **kwargs):
    """
    Update project when tasks are created, updated, or deleted.
    """
    # Update project completion percentage
    instance.project.update_completion_percentage()
    
    # Check for overdue tasks and create alerts
    if instance.is_overdue and instance.status not in ['COMPLETED', 'CANCELLED']:
        logger.warning(f"Task overdue: {instance.title} (Due: {instance.due_date})")

@receiver(post_save, sender=Project)
def check_project_deadlines(sender, instance, **kwargs):
    """
    Check for project deadline violations and create alerts.
    """
    if instance.is_overdue and instance.status in ['PLANNING', 'ACTIVE', 'ON_HOLD']:
        logger.warning(f"Project overdue: {instance.name} (Deadline: {instance.deadline})")

@receiver(post_save, sender=Project)
def update_team_memberships(sender, instance, **kwargs):
    """
    Keep project team_members ManyToManyField in sync with ProjectMember entries.
    """
    # Get all active members
    active_members = instance.memberships.filter(is_active=True).values_list('user', flat=True)
    
    # Update team_members
    current_members = set(instance.team_members.values_list('id', flat=True))
    new_members = set(active_members)
    
    # Add new members
    to_add = new_members - current_members
    if to_add:
        instance.team_members.add(*to_add)
    
    # Remove old members
    to_remove = current_members - new_members
    if to_remove:
        instance.team_members.remove(*to_remove)

# Custom signals for complex operations
from django.dispatch import Signal

# Define custom signals
project_created = Signal()
project_updated = Signal()
project_status_changed = Signal()
task_created = Signal()
task_updated = Signal()
task_completed = Signal()
member_added = Signal()
member_removed = Signal()

@receiver(project_created)
def log_project_creation(sender, project, created_by, **kwargs):
    """
    Log project creation event.
    """
    logger.info(f"Project creation event: {project.name} created by {created_by.username}")

@receiver(project_updated)
def log_project_update(sender, project, updated_by, changes, **kwargs):
    """
    Log project update event.
    """
    logger.info(f"Project update event: {project.name} updated by {updated_by.username} - {changes}")

@receiver(project_status_changed)
def log_project_status_change(sender, project, old_status, new_status, changed_by, **kwargs):
    """
    Log project status change event.
    """
    logger.info(f"Project status change event: {project.name} status changed from {old_status} to {new_status} by {changed_by.username}")

@receiver(task_created)
def log_task_creation(sender, task, created_by, **kwargs):
    """
    Log task creation event.
    """
    logger.info(f"Task creation event: {task.title} created in project {task.project.name} by {created_by.username}")

@receiver(task_updated)
def log_task_update(sender, task, updated_by, changes, **kwargs):
    """
    Log task update event.
    """
    logger.info(f"Task update event: {task.title} updated by {updated_by.username} - {changes}")

@receiver(task_completed)
def log_task_completion(sender, task, completed_by, **kwargs):
    """
    Log task completion event.
    """
    logger.info(f"Task completion event: {task.title} completed by {completed_by.username}")

@receiver(member_added)
def log_member_addition(sender, project, user, added_by, role, **kwargs):
    """
    Log member addition event.
    """
    logger.info(f"Member addition event: {user.username} added to project {project.name} as {role} by {added_by.username}")

@receiver(member_removed)
def log_member_removal(sender, project, user, removed_by, **kwargs):
    """
    Log member removal event.
    """
    logger.info(f"Member removal event: {user.username} removed from project {project.name} by {removed_by.username}")

# Helper functions to send signals
def send_project_created_signal(project, created_by):
    """
    Helper function to send project creation signal.
    """
    project_created.send(sender=Project, project=project, created_by=created_by)

def send_project_updated_signal(project, updated_by, changes):
    """
    Helper function to send project update signal.
    """
    project_updated.send(sender=Project, project=project, updated_by=updated_by, changes=changes)

def send_project_status_change_signal(project, old_status, new_status, changed_by):
    """
    Helper function to send project status change signal.
    """
    project_status_changed.send(sender=Project, project=project, old_status=old_status, new_status=new_status, changed_by=changed_by)

def send_task_created_signal(task, created_by):
    """
    Helper function to send task creation signal.
    """
    task_created.send(sender=Task, task=task, created_by=created_by)

def send_task_updated_signal(task, updated_by, changes):
    """
    Helper function to send task update signal.
    """
    task_updated.send(sender=Task, task=task, updated_by=updated_by, changes=changes)

def send_task_completed_signal(task, completed_by):
    """
    Helper function to send task completion signal.
    """
    task_completed.send(sender=Task, task=task, completed_by=completed_by)

def send_member_added_signal(project, user, added_by, role):
    """
    Helper function to send member addition signal.
    """
    member_added.send(sender=ProjectMember, project=project, user=user, added_by=added_by, role=role)

def send_member_removed_signal(project, user, removed_by):
    """
    Helper function to send member removal signal.
    """
    member_removed.send(sender=ProjectMember, project=project, user=user, removed_by=removed_by)
