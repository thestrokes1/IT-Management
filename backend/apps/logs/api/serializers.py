"""
Activity Timeline API Serializers.

Enhanced serializers for the Activity Timeline API endpoint.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.logs.models import ActivityLog
from apps.logs.domain.entity import EntityType, ActionType


User = get_user_model()


class UserBriefSerializer(serializers.Serializer):
    """Brief user information serializer."""
    id = serializers.CharField()
    username = serializers.CharField()
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    
    def to_representation(self, instance):
        if isinstance(instance, dict):
            return {
                'id': instance.get('id', ''),
                'username': instance.get('username', ''),
                'first_name': instance.get('first_name', ''),
                'last_name': instance.get('last_name', ''),
            }
        return {
            'id': str(instance.id) if instance else '',
            'username': instance.username if instance else '',
            'first_name': instance.first_name if instance else '',
            'last_name': instance.last_name if instance else '',
        }


class FieldChangeSerializer(serializers.Serializer):
    """Serializer for a single field change."""
    from_value = serializers.SerializerMethodField()
    to_value = serializers.SerializerMethodField()
    
    def get_from_value(self, obj):
        return obj.get('from', obj.get('from_value', ''))
    
    def get_to_value(self, obj):
        return obj.get('to', obj.get('to_value', ''))


class ActivityLogSerializer(serializers.Serializer):
    """
    Serializer for Activity Timeline API response.
    
    Returns structured activity log entries with:
    - Entity information
    - Action type
    - User who performed the action
    - Changes (before/after diff)
    - Human-readable description
    - Timestamp
    """
    id = serializers.CharField(source='log_id')
    entity_type = serializers.CharField()
    entity_id = serializers.IntegerField(required=False, allow_null=True)
    action_type = serializers.CharField(source='action')
    performed_by = UserBriefSerializer(required=False)
    description = serializers.CharField()
    changes = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField()
    
    def get_changes(self, obj):
        """Get changes from extra_data."""
        extra_data = obj.extra_data or {}
        changes = extra_data.get('changes', {})
        
        # Transform to {field: {from: ..., to: ...}} format
        formatted_changes = {}
        for field, value in changes.items():
            if isinstance(value, dict):
                formatted_changes[field] = {
                    'from': value.get('from', ''),
                    'to': value.get('to', ''),
                }
            else:
                # Handle legacy format
                formatted_changes[field] = value
        
        return formatted_changes if formatted_changes else None
    
    def to_representation(self, instance):
        """Customize representation."""
        data = super().to_representation(instance)
        
        # Add entity type display name
        data['entity_type_display'] = instance.get_entity_type_display() if hasattr(instance, 'get_entity_type_display') else instance.entity_type
        
        # Add action display name
        data['action_type_display'] = instance.get_action_display() if hasattr(instance, 'get_action_display') else instance.action
        
        # Format performed_by as nested object
        if instance.user:
            data['performed_by'] = {
                'id': str(instance.user.id),
                'username': instance.user.username,
                'first_name': instance.user.first_name or '',
                'last_name': instance.user.last_name or '',
            }
        elif instance.actor_id:
            data['performed_by'] = {
                'id': str(instance.actor_id),
                'username': instance.actor_name or 'System',
                'first_name': '',
                'last_name': '',
            }
        else:
            data['performed_by'] = {
                'id': '',
                'username': 'System',
                'first_name': '',
                'last_name': '',
            }
        
        # Ensure changes is properly formatted
        if data.get('changes') is None:
            data['changes'] = {}
        
        return data


class ActivityTimelineRequestSerializer(serializers.Serializer):
    """
    Serializer for Activity Timeline API request parameters.
    """
    entity_type = serializers.ChoiceField(
        choices=['', 'asset', 'ticket', 'project', 'user'],
        required=False,
        allow_blank=True,
        help_text="Filter by entity type (asset, ticket, project, user)",
    )
    user_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Filter by user ID",
    )
    username = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Filter by username",
    )
    start_date = serializers.DateTimeField(
        required=False,
        help_text="Start date for filtering (ISO format)",
    )
    end_date = serializers.DateTimeField(
        required=False,
        help_text="End date for filtering (ISO format)",
    )
    page = serializers.IntegerField(
        default=1,
        min_value=1,
        help_text="Page number",
    )
    page_size = serializers.IntegerField(
        default=20,
        min_value=1,
        max_value=100,
        help_text="Number of results per page (max 100)",
    )
    search = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Search in description",
    )


class ActivityTimelineResponseSerializer(serializers.Serializer):
    """
    Serializer for Activity Timeline API response.
    """
    results = ActivityLogSerializer(many=True)
    total = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()


class ActivityLogDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for single activity log entry.
    """
    performed_by = serializers.SerializerMethodField()
    changes = serializers.SerializerMethodField()
    entity_type_display = serializers.SerializerMethodField()
    action_type_display = serializers.SerializerMethodField()
    
    class Meta:
        model = ActivityLog
        fields = [
            'id', 'log_id', 'entity_type', 'entity_type_display',
            'entity_id', 'action_type', 'action_type_display',
            'performed_by', 'description', 'changes', 'timestamp',
            'ip_address', 'user_agent',
        ]
    
    def get_performed_by(self, obj):
        """Get user info."""
        if obj.user:
            return {
                'id': str(obj.user.id),
                'username': obj.user.username,
                'first_name': obj.user.first_name or '',
                'last_name': obj.user.last_name or '',
            }
        return {
            'id': str(obj.actor_id) if obj.actor_id else '',
            'username': obj.actor_name or 'System',
            'first_name': '',
            'last_name': '',
        }
    
    def get_changes(self, obj):
        """Get formatted changes."""
        extra_data = obj.extra_data or {}
        changes = extra_data.get('changes', {})
        
        formatted = {}
        for field, value in changes.items():
            if isinstance(value, dict):
                formatted[field] = {
                    'from': value.get('from', ''),
                    'to': value.get('to', ''),
                }
        return formatted or None
    
    def get_entity_type_display(self, obj):
        return obj.get_entity_type_display() if hasattr(obj, 'get_entity_type_display') else obj.entity_type
    
    def get_action_type_display(self, obj):
        return obj.get_action_display() if hasattr(obj, 'get_action_display') else obj.action


class ActivityStatisticsSerializer(serializers.Serializer):
    """Serializer for activity statistics."""
    total = serializers.IntegerField()
    by_entity_type = serializers.DictField()
    by_action_type = serializers.DictField()
    by_user = serializers.ListField()
    recent_activities = ActivityLogSerializer(many=True)

