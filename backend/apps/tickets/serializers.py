"""
Ticket serializers for IT Management Platform.
Handles serialization and validation for ticket operations.
"""

from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, timedelta

from apps.tickets.models import (
    TicketCategory, TicketType, Ticket, TicketComment, TicketAttachment,
    TicketHistory, TicketTemplate, SLA, TicketEscalation, TicketSatisfaction,
    TicketReport
)
from apps.users.models import User

class TicketCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for ticket categories.
    """
    default_assignee_username = serializers.CharField(source='default_assignee.username', read_only=True)
    
    class Meta:
        model = TicketCategory
        fields = ['id', 'name', 'description', 'color', 'is_active', 'auto_assign_enabled', 'default_assignee', 'default_assignee_username', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class TicketTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for ticket types.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = TicketType
        fields = ['id', 'category', 'category_name', 'name', 'description', 'sla_hours', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class TicketListSerializer(serializers.ModelSerializer):
    """
    Serializer for ticket list view.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    requester_username = serializers.CharField(source='requester.username', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    assigned_to_id = serializers.IntegerField(source='assigned_to.id', read_only=True, allow_null=True)
    is_overdue = serializers.BooleanField(read_only=True)
    hours_since_creation = serializers.FloatField(read_only=True)
    hours_to_sla = serializers.FloatField(read_only=True)
    can_self_assign = serializers.SerializerMethodField()
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_id', 'title', 'description', 'category_name',
            'ticket_type_name', 'requester_username', 'priority', 'status',
            'impact', 'urgency', 'assigned_to_username', 'assigned_to_id',
            'assigned_team', 'assignment_status', 'location',
            'created_at', 'updated_at', 'sla_due_at', 'is_overdue',
            'hours_since_creation', 'hours_to_sla', 'can_self_assign'
        ]
        read_only_fields = ['id', 'ticket_id', 'created_at', 'updated_at']
    
    def get_can_self_assign(self, obj):
        """Check if current user can self-assign this ticket."""
        from apps.tickets.domain.services.ticket_authority import can_self_assign_ticket
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return can_self_assign_ticket(request.user, obj)
        return False

class TicketDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for ticket detail view.
    """
    category = TicketCategorySerializer(read_only=True)
    ticket_type = TicketTypeSerializer(read_only=True)
    requester = serializers.StringRelatedField(read_only=True)
    assigned_to = serializers.StringRelatedField(read_only=True)
    parent_ticket = serializers.StringRelatedField(read_only=True)
    related_tickets = serializers.StringRelatedField(many=True, read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    hours_since_creation = serializers.FloatField(read_only=True)
    hours_to_sla = serializers.FloatField(read_only=True)
    resolution_hours = serializers.FloatField(read_only=True)
    
    class Meta:
        model = Ticket
        fields = [
            'id', 'ticket_id', 'title', 'description', 'category', 'ticket_type',
            'requester', 'priority', 'status', 'impact', 'urgency',
            'assigned_to', 'assigned_team', 'created_at', 'updated_at',
            'resolved_at', 'closed_at', 'sla_due_at', 'sla_breached',
            'sla_breach_notified', 'resolution_summary', 'resolution_time',
            'parent_ticket', 'related_tickets', 'location', 'contact_phone',
            'contact_email', 'tags', 'is_overdue', 'hours_since_creation',
            'hours_to_sla', 'resolution_hours', 'created_by', 'updated_by'
        ]
        read_only_fields = [
            'id', 'ticket_id', 'created_at', 'updated_at', 'resolved_at',
            'closed_at', 'is_overdue', 'hours_since_creation', 'hours_to_sla', 'resolution_hours'
        ]

class TicketCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating tickets.
    """
    related_ticket_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Ticket
        fields = [
            'title', 'description', 'category', 'ticket_type', 'priority',
            'impact', 'urgency', 'assigned_to', 'assigned_team', 'parent_ticket',
            'related_ticket_ids', 'location', 'contact_phone', 'contact_email',
            'tags'
        ]
    
    def validate(self, attrs):
        # Calculate priority if not provided
        if not attrs.get('priority'):
            impact = attrs.get('impact', 'MEDIUM')
            urgency = attrs.get('urgency', 'MEDIUM')
            attrs['priority'] = self._calculate_priority(impact, urgency)
        
        return attrs
    
    def _calculate_priority(self, impact, urgency):
        """Calculate priority based on impact and urgency."""
        if impact == 'CRITICAL' and urgency in ['HIGH', 'URGENT']:
            return 'CRITICAL'
        elif impact == 'HIGH' or urgency == 'URGENT':
            return 'URGENT'
        elif impact == 'MEDIUM' or urgency == 'HIGH':
            return 'HIGH'
        else:
            return 'MEDIUM'
    
    def create(self, validated_data):
        related_ticket_ids = validated_data.pop('related_ticket_ids', [])
        validated_data['requester'] = self.context['request'].user
        validated_data['created_by'] = self.context['request'].user
        
        ticket = Ticket.objects.create(**validated_data)
        
        # Set SLA due date
        ticket.update_sla_due()
        
        # Add related tickets
        for ticket_id in related_ticket_ids:
            try:
                related_ticket = Ticket.objects.get(ticket_id=ticket_id)
                ticket.related_tickets.add(related_ticket)
            except Ticket.DoesNotExist:
                continue
        
        return ticket

class TicketUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating tickets.
    """
    related_ticket_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Ticket
        fields = [
            'title', 'description', 'priority', 'status', 'impact', 'urgency',
            'assigned_to', 'assigned_team', 'parent_ticket', 'related_ticket_ids',
            'location', 'contact_phone', 'contact_email', 'tags'
        ]
    
    def update(self, instance, validated_data):
        related_ticket_ids = validated_data.pop('related_ticket_ids', None)
        validated_data['updated_by'] = self.context['request'].user
        
        # Handle status changes
        old_status = instance.status
        new_status = validated_data.get('status')
        
        if new_status == 'RESOLVED' and old_status != 'RESOLVED':
            validated_data['resolved_at'] = timezone.now()
        elif new_status == 'CLOSED' and old_status != 'CLOSED':
            validated_data['closed_at'] = timezone.now()
        
        # Update ticket fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update related tickets if provided
        if related_ticket_ids is not None:
            instance.related_tickets.clear()
            for ticket_id in related_ticket_ids:
                try:
                    related_ticket = Ticket.objects.get(ticket_id=ticket_id)
                    instance.related_tickets.add(related_ticket)
                except Ticket.DoesNotExist:
                    continue
        
        return instance

class TicketCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for ticket comments.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = TicketComment
        fields = ['id', 'ticket', 'user', 'user_username', 'user_full_name', 'comment', 'is_internal', 'is_resolution', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'user_username', 'user_full_name', 'created_at', 'updated_at']

class TicketAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for ticket attachments.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TicketAttachment
        fields = ['id', 'ticket', 'user', 'user_username', 'file', 'filename', 'file_size', 'mime_type', 'description', 'is_screenshot', 'created_at']
        read_only_fields = ['id', 'user', 'user_username', 'file_size', 'mime_type', 'created_at']

class TicketHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for ticket history.
    """
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TicketHistory
        fields = ['id', 'ticket', 'user', 'user_username', 'field_name', 'old_value', 'new_value', 'timestamp', 'comment']
        read_only_fields = ['id', 'timestamp']

class TicketTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for ticket templates.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = TicketTemplate
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'ticket_type', 'ticket_type_name', 'template_title', 'template_description',
            'default_priority', 'default_impact', 'default_urgency', 'default_tags',
            'created_by', 'created_by_username', 'is_public', 'usage_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_by_username', 'usage_count', 'created_at', 'updated_at']

class SLASerializer(serializers.ModelSerializer):
    """
    Serializer for SLA configurations.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    ticket_type_name = serializers.CharField(source='ticket_type.name', read_only=True)
    
    class Meta:
        model = SLA
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'ticket_type', 'ticket_type_name', 'response_time_hours',
            'resolution_time_hours', 'low_priority_multiplier',
            'medium_priority_multiplier', 'high_priority_multiplier',
            'critical_priority_multiplier', 'urgent_priority_multiplier',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class TicketEscalationSerializer(serializers.ModelSerializer):
    """
    Serializer for ticket escalations.
    """
    ticket_title = serializers.CharField(source='ticket.title', read_only=True)
    escalated_by_username = serializers.CharField(source='escalated_by.username', read_only=True)
    escalated_to_username = serializers.CharField(source='escalated_to.username', read_only=True)
    
    class Meta:
        model = TicketEscalation
        fields = [
            'id', 'ticket', 'ticket_title', 'escalated_by', 'escalated_by_username',
            'escalated_to', 'escalated_to_username', 'escalation_level',
            'reason', 'escalated_at', 'resolved', 'resolved_at'
        ]
        read_only_fields = ['id', 'escalated_at']

class TicketSatisfactionSerializer(serializers.ModelSerializer):
    """
    Serializer for ticket satisfaction ratings.
    """
    ticket_title = serializers.CharField(source='ticket.title', read_only=True)
    rated_by_username = serializers.CharField(source='rated_by.username', read_only=True)
    
    class Meta:
        model = TicketSatisfaction
        fields = [
            'id', 'ticket', 'ticket_title', 'rating', 'feedback',
            'rated_by', 'rated_by_username', 'rated_at'
        ]
        read_only_fields = ['id', 'rated_at']

class TicketReportSerializer(serializers.ModelSerializer):
    """
    Serializer for ticket reports.
    """
    generated_by_username = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = TicketReport
        fields = [
            'id', 'title', 'report_type', 'description', 'parameters',
            'generated_by', 'generated_by_username', 'generated_at',
            'file_path', 'is_scheduled', 'schedule_frequency'
        ]
        read_only_fields = ['id', 'generated_at', 'generated_by_username']

class TicketStatisticsSerializer(serializers.Serializer):
    """
    Serializer for ticket statistics.
    """
    total_tickets = serializers.IntegerField()
    open_tickets = serializers.IntegerField()
    in_progress_tickets = serializers.IntegerField()
    resolved_tickets = serializers.IntegerField()
    closed_tickets = serializers.IntegerField()
    overdue_tickets = serializers.IntegerField()
    tickets_by_status = serializers.DictField()
    tickets_by_priority = serializers.DictField()
    tickets_by_category = serializers.DictField()
    sla_compliance_rate = serializers.FloatField()
    average_resolution_time = serializers.FloatField()
    recent_activities = serializers.ListField()
    upcoming_sla_breaches = TicketListSerializer(many=True)

class TicketSearchSerializer(serializers.Serializer):
    """
    Serializer for ticket search functionality.
    """
    search = serializers.CharField(required=False)
    status = serializers.ChoiceField(choices=Ticket.STATUS_CHOICES, required=False)
    priority = serializers.ChoiceField(choices=Ticket.PRIORITY_CHOICES, required=False)
    category = serializers.IntegerField(required=False)
    ticket_type = serializers.IntegerField(required=False)
    requester = serializers.IntegerField(required=False)
    assigned_to = serializers.IntegerField(required=False)
    overdue = serializers.BooleanField(required=False)
    created_from = serializers.DateField(required=False)
    created_to = serializers.DateField(required=False)

class TicketActionSerializer(serializers.Serializer):
    """
    Serializer for ticket actions like resolve, close, assign, etc.
    """
    action = serializers.ChoiceField(choices=[
        'assign', 'resolve', 'close', 'reopen', 'escalate', 'update_status'
    ])
    assignee = serializers.IntegerField(required=False)
    resolution_summary = serializers.CharField(required=False)
    status = serializers.ChoiceField(choices=Ticket.STATUS_CHOICES, required=False)
    escalation_level = serializers.ChoiceField(choices=TicketEscalation.LEVEL_CHOICES, required=False)
    escalation_reason = serializers.CharField(required=False)
    comment = serializers.CharField(required=False)

class TicketTemplateUseSerializer(serializers.Serializer):
    """
    Serializer for using ticket templates.
    """
    template_id = serializers.IntegerField()
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    location = serializers.CharField(required=False)
    contact_phone = serializers.CharField(required=False)
    contact_email = serializers.EmailField(required=False)
