"""
Ticket models for IT Management Platform.
IT support ticket management with comprehensive tracking and SLA management.
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from decimal import Decimal

User = get_user_model()

class TicketCategory(models.Model):
    """
    Categories for organizing tickets (Incident, Request, Change, etc.).
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color code
    is_active = models.BooleanField(default=True)
    auto_assign_enabled = models.BooleanField(default=False)
    default_assignee = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='default_ticket_categories'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ticket_categories'
        verbose_name = 'Ticket Category'
        verbose_name_plural = 'Ticket Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class TicketType(models.Model):
    """
    Types of tickets within each category.
    """
    category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE, related_name='ticket_types')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    sla_hours = models.PositiveIntegerField(default=24)  # Service Level Agreement in hours
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ticket_types'
        verbose_name = 'Ticket Type'
        verbose_name_plural = 'Ticket Types'
        unique_together = ['category', 'name']
        ordering = ['category__name', 'name']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"

class Ticket(models.Model):
    """
    Main ticket model for IT support tickets.
    """
    # Priority choices
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
        ('URGENT', 'Urgent'),
    ]
    
    # Status choices
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('PENDING', 'Pending'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    # Impact choices
    IMPACT_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    # Urgency choices
    URGENCY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    # Assignment status choices
    ASSIGNMENT_STATUS_CHOICES = [
        ('UNASSIGNED', 'Unassigned'),
        ('ASSIGNED', 'Assigned'),
    ]
    
    # Ticket ID (unique identifier)
    ticket_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Basic information
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(TicketCategory, on_delete=models.PROTECT, related_name='tickets')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.PROTECT, related_name='tickets')
    
    # Requester information
    requester = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_created'
    )
    
    # Ticket management
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    impact = models.CharField(max_length=10, choices=IMPACT_CHOICES, default='MEDIUM')
    urgency = models.CharField(max_length=10, choices=URGENCY_CHOICES, default='MEDIUM')
    
    # Assignment
    assigned_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_assigned'
    )
    assigned_team = models.CharField(max_length=100, blank=True)
    assignment_status = models.CharField(
        max_length=20, choices=ASSIGNMENT_STATUS_CHOICES, default='UNASSIGNED'
    )
    
    # Timeline
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    
    # SLA tracking
    sla_due_at = models.DateTimeField(null=True, blank=True)
    sla_breached = models.BooleanField(default=False)
    sla_breach_notified = models.BooleanField(default=False)
    
    # Resolution
    resolution_summary = models.TextField(blank=True)
    resolution_time = models.DurationField(null=True, blank=True)  # Total time to resolve
    
    # Related tickets
    parent_ticket = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='child_tickets'
    )
    related_tickets = models.ManyToManyField('self', blank=True, symmetrical=False)
    
    # Location and contact
    location = models.CharField(max_length=200, blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    
    # Tags and custom fields
    tags = models.JSONField(default=list, blank=True)
    
    # Audit fields
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_created_by'
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tickets_updated_by'
    )
    
    class Meta:
        db_table = 'tickets'
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['requester']),
            models.Index(fields=['category', 'ticket_type']),
            models.Index(fields=['sla_due_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"#{self.ticket_id} - {self.title}"
    
    @property
    def is_overdue(self):
        """Check if ticket is overdue based on SLA."""
        if not self.sla_due_at:
            return False
        return timezone.now() > self.sla_due_at and self.status not in ['RESOLVED', 'CLOSED', 'CANCELLED']
    
    @property
    def hours_since_creation(self):
        """Get hours since ticket creation."""
        return (timezone.now() - self.created_at).total_seconds() / 3600
    
    @property
    def hours_to_sla(self):
        """Get hours until SLA breach."""
        if not self.sla_due_at:
            return None
        return (self.sla_due_at - timezone.now()).total_seconds() / 3600
    
    @property
    def resolution_hours(self):
        """Get resolution time in hours."""
        if not self.resolved_at:
            return None
        return (self.resolved_at - self.created_at).total_seconds() / 3600
    
    def update_sla_due(self):
        """Update SLA due date based on ticket type and priority."""
        if self.ticket_type and self.ticket_type.sla_hours:
            # Calculate SLA multiplier based on priority
            priority_multipliers = {
                'LOW': 4,      # 4x the base SLA
                'MEDIUM': 2,   # 2x the base SLA
                'HIGH': 1,     # 1x the base SLA
                'CRITICAL': 0.5,  # 0.5x the base SLA
                'URGENT': 0.25,   # 0.25x the base SLA
            }
            
            multiplier = priority_multipliers.get(self.priority, 1)
            sla_hours = self.ticket_type.sla_hours * multiplier
            
            self.sla_due_at = self.created_at + timezone.timedelta(hours=sla_hours)
            self.save()
    
    def mark_resolved(self, resolution_summary=None, resolved_by=None):
        """Mark ticket as resolved."""
        self.status = 'RESOLVED'
        self.resolved_at = timezone.now()
        if resolution_summary:
            self.resolution_summary = resolution_summary
        self.resolution_time = self.resolved_at - self.created_at
        self.updated_by = resolved_by or self.updated_by
        self.save()
    
    def mark_closed(self, closed_by=None):
        """Mark ticket as closed."""
        self.status = 'CLOSED'
        self.closed_at = timezone.now()
        self.updated_by = closed_by or self.updated_by
        self.save()
    
    def assign_to(self, assignee, assigned_by=None):
        """Assign ticket to a user."""
        self.assigned_to = assignee
        if assigned_by:
            self.updated_by = assigned_by
        self.save()
    
    def calculate_priority(self, impact, urgency):
        """Calculate priority based on impact and urgency."""
        # Simple matrix calculation
        if impact == 'CRITICAL' and urgency in ['HIGH', 'URGENT']:
            return 'CRITICAL'
        elif impact == 'HIGH' or urgency == 'URGENT':
            return 'URGENT'
        elif impact == 'MEDIUM' or urgency == 'HIGH':
            return 'HIGH'
        else:
            return 'MEDIUM'

class TicketComment(models.Model):
    """
    Comments and updates for tickets.
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_comments')
    comment = models.TextField()
    is_internal = models.BooleanField(default=False)  # Internal notes vs public comments
    is_resolution = models.BooleanField(default=False)  # Resolution comments
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ticket_comments'
        verbose_name = 'Ticket Comment'
        verbose_name_plural = 'Ticket Comments'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on ticket {self.ticket.ticket_id}"

class TicketAttachment(models.Model):
    """
    File attachments for tickets.
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_attachments')
    file = models.FileField(upload_to='ticket_attachments/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    is_screenshot = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ticket_attachments'
        verbose_name = 'Ticket Attachment'
        verbose_name_plural = 'Ticket Attachments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} - Ticket {self.ticket.ticket_id}"

class TicketHistory(models.Model):
    """
    Historical changes to tickets for audit trail.
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.SET_NULL,null=True,blank=True, related_name='history')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_history')
    field_name = models.CharField(max_length=50)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)  # Optional comment explaining the change
    
    class Meta:
        db_table = 'ticket_history'
        verbose_name = 'Ticket History'
        verbose_name_plural = 'Ticket History'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ticket', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Ticket {self.ticket.ticket_id} - {self.field_name} changed"


class TicketStatusHistory(models.Model):
    """
    Immutable status change history for tickets.
    
    Records every status transition with:
    - ticket: Reference to the ticket
    - from_status: Previous status before the change
    - to_status: New status after the change
    - changed_by: User who made the change
    - changed_at: Timestamp of the change (auto_now_add)
    
    Rules:
    - Write only when status changes
    - Immutable records (no updates or deletes)
    - Created inside the same transaction as ticket update
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=20, choices=Ticket.STATUS_CHOICES)
    to_status = models.CharField(max_length=20, choices=Ticket.STATUS_CHOICES)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='ticket_status_changes')
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ticket_status_history'
        verbose_name = 'Ticket Status History'
        verbose_name_plural = 'Ticket Status Histories'
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['ticket', 'changed_at']),
            models.Index(fields=['changed_by', 'changed_at']),
        ]
        # Ensure no updates or deletes at application level
        # (Django doesn't enforce this, but the model represents immutable records)
    
    def __str__(self):
        return f"Ticket {self.ticket.ticket_id}: {self.from_status} -> {self.to_status} by {self.changed_by}"
    
    def save(self, *args, **kwargs):
        """Override save to prevent updates to immutable records."""
        if self.pk and TicketStatusHistory.objects.filter(pk=self.pk).exists():
            raise ValueError("TicketStatusHistory records are immutable and cannot be updated")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete to prevent deletion of immutable records."""
        raise ValueError("TicketStatusHistory records are immutable and cannot be deleted")

class TicketTemplate(models.Model):
    """
    Reusable ticket templates.
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(TicketCategory, on_delete=models.PROTECT, related_name='templates')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.PROTECT, related_name='templates')
    
    # Template content
    template_title = models.CharField(max_length=200)
    template_description = models.TextField()
    default_priority = models.CharField(max_length=10, choices=Ticket.PRIORITY_CHOICES, default='MEDIUM')
    default_impact = models.CharField(max_length=10, choices=Ticket.IMPACT_CHOICES, default='MEDIUM')
    default_urgency = models.CharField(max_length=10, choices=Ticket.URGENCY_CHOICES, default='MEDIUM')
    default_tags = models.JSONField(default=list, blank=True)
    
    # Template metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_templates')
    is_public = models.BooleanField(default=False)
    usage_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ticket_templates'
        verbose_name = 'Ticket Template'
        verbose_name_plural = 'Ticket Templates'
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return self.name

class SLA(models.Model):
    """
    Service Level Agreement configurations.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE, related_name='slas')
    ticket_type = models.ForeignKey(TicketType, on_delete=models.CASCADE, related_name='slas')
    
    # SLA targets
    response_time_hours = models.PositiveIntegerField(default=4)
    resolution_time_hours = models.PositiveIntegerField(default=24)
    
    # Priority-based SLA multipliers
    low_priority_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=4.0)
    medium_priority_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=2.0)
    high_priority_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.0)
    critical_priority_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=0.5)
    urgent_priority_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=0.25)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'slas'
        verbose_name = 'SLA'
        verbose_name_plural = 'SLAs'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_sla_hours(self, priority):
        """Get SLA hours based on priority."""
        multipliers = {
            'LOW': self.low_priority_multiplier,
            'MEDIUM': self.medium_priority_multiplier,
            'HIGH': self.high_priority_multiplier,
            'CRITICAL': self.critical_priority_multiplier,
            'URGENT': self.urgent_priority_multiplier,
        }
        
        multiplier = multipliers.get(priority, 1)
        return self.resolution_time_hours * multiplier

class TicketEscalation(models.Model):
    """
    Ticket escalation rules and history.
    """
    # Escalation level choices
    LEVEL_CHOICES = [
        ('L1', 'Level 1 - First Line Support'),
        ('L2', 'Level 2 - Technical Support'),
        ('L3', 'Level 3 - Specialist Support'),
        ('MANAGEMENT', 'Management Escalation'),
    ]
    
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='escalations')
    escalated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_escalations')
    escalated_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='escalated_tickets')
    escalation_level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    reason = models.TextField()
    escalated_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'ticket_escalations'
        verbose_name = 'Ticket Escalation'
        verbose_name_plural = 'Ticket Escalations'
        ordering = ['-escalated_at']
    
    def __str__(self):
        return f"Ticket {self.ticket.ticket_id} escalated to {self.escalation_level}"

class TicketSatisfaction(models.Model):
    """
    Customer satisfaction ratings for closed tickets.
    """
    # Rating choices (1-5 stars)
    RATING_CHOICES = [
        (1, '1 - Very Dissatisfied'),
        (2, '2 - Dissatisfied'),
        (3, '3 - Neutral'),
        (4, '4 - Satisfied'),
        (5, '5 - Very Satisfied'),
    ]
    
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='satisfaction')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    feedback = models.TextField(blank=True)
    rated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_ratings')
    rated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ticket_satisfaction'
        verbose_name = 'Ticket Satisfaction'
        verbose_name_plural = 'Ticket Satisfaction'
        ordering = ['-rated_at']
    
    def __str__(self):
        return f"Ticket {self.ticket.ticket_id} - Rating: {self.rating}"

class TicketReport(models.Model):
    """
    Ticket reports and analytics data.
    """
    # Report type choices
    REPORT_TYPE_CHOICES = [
        ('TICKET_SUMMARY', 'Ticket Summary'),
        ('SLA_PERFORMANCE', 'SLA Performance'),
        ('AGENT_PERFORMANCE', 'Agent Performance'),
        ('CATEGORY_ANALYSIS', 'Category Analysis'),
        ('TREND_ANALYSIS', 'Trend Analysis'),
        ('SATISFACTION_REPORT', 'Satisfaction Report'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    description = models.TextField(blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ticket_reports_generated')
    generated_at = models.DateTimeField(auto_now_add=True)
    file_path = models.FilePathField(null=True, blank=True)
    is_scheduled = models.BooleanField(default=False)
    schedule_frequency = models.CharField(max_length=20, blank=True)
    
    class Meta:
        db_table = 'ticket_reports'
        verbose_name = 'Ticket Report'
        verbose_name_plural = 'Ticket Reports'
        ordering = ['-generated_at']
    
    def __str__(self):
        return self.title
