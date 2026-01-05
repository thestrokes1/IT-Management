"""
Ticket signals for IT Management Platform.
Handles ticket creation, updates, assignments, and audit logging.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Ticket, TicketComment, TicketAttachment, TicketHistory, TicketEscalation
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Ticket)
def create_ticket_history(sender, instance, created, **kwargs):
    """
    Create history record when ticket is created or updated.
    """
    if created:
        # Log ticket creation
        TicketHistory.objects.create(
            ticket=instance,
            user=instance.created_by or User.objects.filter(is_superuser=True).first(),
            field_name='created',
            new_value=f'Ticket created: {instance.title}'
        )
        logger.info(f"Ticket created: {instance.title} (ID: {instance.ticket_id})")
    else:
        # Log significant changes for updates
        try:
            old_instance = Ticket.objects.get(pk=instance.pk)
            changes = []
            
            # Check for status changes
            if old_instance.status != instance.status:
                changes.append(f"status: {old_instance.status} -> {instance.status}")
                TicketHistory.objects.create(
                    ticket=instance,
                    user=instance.updated_by or User.objects.filter(is_superuser=True).first(),
                    field_name='status',
                    old_value=old_instance.status,
                    new_value=instance.status
                )
            
            # Check for assignment changes
            if old_instance.assigned_to != instance.assigned_to:
                old_assignee = old_instance.assigned_to.username if old_instance.assigned_to else None
                new_assignee = instance.assigned_to.username if instance.assigned_to else None
                changes.append(f"assigned_to: {old_assignee} -> {new_assignee}")
                TicketHistory.objects.create(
                    ticket=instance,
                    user=instance.updated_by or User.objects.filter(is_superuser=True).first(),
                    field_name='assigned_to',
                    old_value=old_assignee,
                    new_value=new_assignee
                )
            
            # Check for priority changes
            if old_instance.priority != instance.priority:
                changes.append(f"priority: {old_instance.priority} -> {instance.priority}")
                TicketHistory.objects.create(
                    ticket=instance,
                    user=instance.updated_by or User.objects.filter(is_superuser=True).first(),
                    field_name='priority',
                    old_value=old_instance.priority,
                    new_value=instance.priority
                )
            
            # Check for resolution summary changes
            if old_instance.resolution_summary != instance.resolution_summary:
                changes.append("resolution_summary updated")
                TicketHistory.objects.create(
                    ticket=instance,
                    user=instance.updated_by or User.objects.filter(is_superuser=True).first(),
                    field_name='resolution_summary',
                    old_value=old_instance.resolution_summary[:100] + '...' if len(old_instance.resolution_summary) > 100 else old_instance.resolution_summary,
                    new_value=instance.resolution_summary[:100] + '...' if len(instance.resolution_summary) > 100 else instance.resolution_summary
                )
            
            if changes:
                logger.info(f"Ticket updated: {instance.title} - {', '.join(changes)}")
        except Ticket.DoesNotExist:
            pass


@receiver(post_save, sender=TicketComment)
def create_comment_history(sender, instance, created, **kwargs):
    """
    Create history record when ticket comment is created.
    """
    if created:
        TicketHistory.objects.create(
            ticket=instance.ticket,
            user=instance.user,
            field_name='comment_added',
            new_value=f'Comment added by {instance.user.username}: {instance.comment[:100]}...' if len(instance.comment) > 100 else f'Comment added by {instance.user.username}: {instance.comment}'
        )
        logger.info(f"Comment added to ticket {instance.ticket.ticket_id} by {instance.user.username}")

@receiver(post_save, sender=TicketAttachment)
def create_attachment_history(sender, instance, created, **kwargs):
    """
    Create history record when ticket attachment is added.
    """
    if created:
        TicketHistory.objects.create(
            ticket=instance.ticket,
            user=instance.user,
            field_name='attachment_added',
            new_value=f'Attachment added by {instance.user.username}: {instance.filename}'
        )
        logger.info(f"Attachment added to ticket {instance.ticket.ticket_id}: {instance.filename}")

@receiver(post_save, sender=TicketEscalation)
def create_escalation_history(sender, instance, created, **kwargs):
    """
    Create history record when ticket is escalated.
    """
    if created:
        TicketHistory.objects.create(
            ticket=instance.ticket,
            user=instance.escalated_by,
            field_name='escalated',
            new_value=f'Ticket escalated to {instance.escalation_level} by {instance.escalated_by.username}'
        )
        logger.info(f"Ticket {instance.ticket.ticket_id} escalated to {instance.escalation_level} by {instance.escalated_by.username}")

@receiver(post_save, sender=Ticket)
def check_ticket_workflow(sender, instance, **kwargs):
    """
    Check for workflow-based automatic actions.
    """
    # This is a placeholder for workflow automation
    # You could implement automatic status changes, notifications, etc.
    pass

# Custom signals for complex operations
from django.dispatch import Signal

# Define custom signals
ticket_created = Signal()
ticket_updated = Signal()
ticket_assigned = Signal()
ticket_resolved = Signal()
ticket_closed = Signal()
ticket_escalated = Signal()

@receiver(ticket_created)
def log_ticket_creation(sender, ticket, created_by, **kwargs):
    """
    Log ticket creation event.
    """
    logger.info(f"Ticket creation event: {ticket.title} created by {created_by.username}")

@receiver(ticket_updated)
def log_ticket_update(sender, ticket, updated_by, changes, **kwargs):
    """
    Log ticket update event.
    """
    logger.info(f"Ticket update event: {ticket.title} updated by {updated_by.username} - {changes}")

@receiver(ticket_assigned)
def log_ticket_assignment(sender, ticket, assignee, assigned_by, **kwargs):
    """
    Log ticket assignment event.
    """
    logger.info(f"Ticket assignment event: {ticket.title} assigned to {assignee.username} by {assigned_by.username}")

@receiver(ticket_resolved)
def log_ticket_resolution(sender, ticket, resolved_by, **kwargs):
    """
    Log ticket resolution event.
    """
    logger.info(f"Ticket resolution event: {ticket.title} resolved by {resolved_by.username}")

@receiver(ticket_closed)
def log_ticket_closure(sender, ticket, closed_by, **kwargs):
    """
    Log ticket closure event.
    """
    logger.info(f"Ticket closure event: {ticket.title} closed by {closed_by.username}")

@receiver(ticket_escalated)
def log_ticket_escalation(sender, ticket, escalated_to, escalated_by, level, **kwargs):
    """
    Log ticket escalation event.
    """
    logger.info(f"Ticket escalation event: {ticket.title} escalated to {level} by {escalated_by.username}")

# Helper functions to send signals
def send_ticket_created_signal(ticket, created_by):
    """
    Helper function to send ticket creation signal.
    """
    ticket_created.send(sender=Ticket, ticket=ticket, created_by=created_by)

def send_ticket_updated_signal(ticket, updated_by, changes):
    """
    Helper function to send ticket update signal.
    """
    ticket_updated.send(sender=Ticket, ticket=ticket, updated_by=updated_by, changes=changes)

def send_ticket_assigned_signal(ticket, assignee, assigned_by):
    """
    Helper function to send ticket assignment signal.
    """
    ticket_assigned.send(sender=Ticket, ticket=ticket, assignee=assignee, assigned_by=assigned_by)

def send_ticket_resolved_signal(ticket, resolved_by):
    """
    Helper function to send ticket resolution signal.
    """
    ticket_resolved.send(sender=Ticket, ticket=ticket, resolved_by=resolved_by)

def send_ticket_closed_signal(ticket, closed_by):
    """
    Helper function to send ticket closure signal.
    """
    ticket_closed.send(sender=Ticket, ticket=ticket, closed_by=closed_by)

def send_ticket_escalated_signal(ticket, escalated_to, escalated_by, level):
    """
    Helper function to send ticket escalation signal.
    """
    ticket_escalated.send(sender=Ticket, ticket=ticket, escalated_to=escalated_to, escalated_by=escalated_by, level=level)

# Scheduled tasks (would be run by celery or similar)
def check_overdue_tickets():
    """
    Check for overdue tickets and take appropriate action.
    """
    overdue_tickets = Ticket.objects.filter(
        sla_due_at__isnull=False,
        sla_due_at__lt=timezone.now(),
        status__in=['NEW', 'OPEN', 'IN_PROGRESS', 'PENDING']
    )
    
    for ticket in overdue_tickets:
        if not ticket.sla_breached:
            ticket.sla_breached = True
            ticket.save()
            logger.warning(f"SLA breach detected and marked: {ticket.ticket_id}")

def send_sla_breach_notifications():
    """
    Send notifications for SLA breaches.
    """
    # This would integrate with your notification system
    pass

def check_ticket_auto_closure():
    """
    Automatically close tickets that have been resolved for a certain period.
    """
    # Auto-close tickets resolved more than 7 days ago
    resolved_tickets = Ticket.objects.filter(
        status='RESOLVED',
        resolved_at__lt=timezone.now() - timezone.timedelta(days=7)
    )
    
    for ticket in resolved_tickets:
        ticket.mark_closed()
        logger.info(f"Ticket auto-closed: {ticket.ticket_id}")
