"""
Activity Timeline API Views.

REST API endpoints for the Activity Timeline system.
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta

from apps.logs.models import ActivityLog
from apps.logs.api.serializers import (
    ActivityLogSerializer,
    ActivityTimelineRequestSerializer,
    ActivityTimelineResponseSerializer,
    ActivityLogDetailSerializer,
    ActivityStatisticsSerializer,
)


User = get_user_model()


class ActivityTimelinePermission(permissions.BasePermission):
    """
    Permission class for Activity Timeline access.
    
    Only Admin or authorized roles can access.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Allow superusers
        if request.user.is_superuser:
            return True
        
        # Check user role
        user_role = getattr(request.user, 'role', None)
        allowed_roles = ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'ADMIN']
        
        if user_role in allowed_roles:
            return True
        
        # View logs permission
        return request.user.has_perm('logs.view_activitylog')


class ActivityTimelineAPIView(APIView):
    """
    GET /api/logs/activity-timeline/
    
    Unified Activity Timeline endpoint.
    
    Supports:
    - Pagination
    - Filtering by entity_type (asset, ticket, project, user)
    - Filtering by user (user_id or username)
    - Date range filter
    
    Response format:
    {
        "results": [
            {
                "id": "uuid",
                "entity_type": "Ticket",
                "entity_id": 123,
                "action_type": "UPDATED",
                "performed_by": {
                    "id": "1",
                    "username": "john"
                },
                "description": "Ticket status changed from Open to Closed",
                "changes": {
                    "status": {
                        "from": "Open",
                        "to": "Closed"
                    }
                },
                "timestamp": "2024-01-15T10:30:00Z"
            }
        ],
        "total": 150,
        "page": 1,
        "page_size": 20,
        "total_pages": 8
    }
    """
    permission_classes = [permissions.IsAuthenticated, ActivityTimelinePermission]
    
    def get(self, request):
        """Get activity timeline with filters and pagination."""
        # Validate request parameters
        serializer = ActivityTimelineRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid parameters', 'details': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        params = serializer.validated_data
        
        # Build queryset with select_related for performance
        qs = ActivityLog.objects.select_related('user').order_by('-timestamp')
        
        # Apply filters
        # Entity type filter
        entity_type = params.get('entity_type')
        if entity_type:
            qs = qs.filter(entity_type__iexact=entity_type)
        
        # User filters
        user_id = params.get('user_id')
        username = params.get('username')
        
        if user_id:
            qs = qs.filter(actor_id=str(user_id))
        elif username:
            # Search in both user.username and actor_name
            qs = qs.filter(
                Q(user__username__icontains=username) |
                Q(actor_name__icontains=username)
            )
        
        # Date range filter
        start_date = params.get('start_date')
        end_date = params.get('end_date')
        
        if start_date:
            qs = qs.filter(timestamp__gte=start_date)
        if end_date:
            qs = qs.filter(timestamp__lte=end_date)
        
        # Search filter
        search = params.get('search')
        if search:
            qs = qs.filter(
                Q(description__icontains=search) |
                Q(title__icontains=search) |
                Q(object_repr__icontains=search)
            )
        
        # Get total count
        total = qs.count()
        
        # Pagination
        page = params.get('page', 1)
        page_size = params.get('page_size', 20)
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Get results
        logs = qs[offset:offset + page_size]
        
        # Serialize results
        results = ActivityLogSerializer(logs, many=True).data
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        # Build response
        response_data = {
            'results': results,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
        }
        
        return Response(response_data)


class ActivityTimelineDetailAPIView(APIView):
    """
    GET /api/logs/activity-timeline/{id}/
    
    Get single activity log entry details.
    """
    permission_classes = [permissions.IsAuthenticated, ActivityTimelinePermission]
    
    def get(self, request, log_id):
        """Get single activity log entry."""
        try:
            log = ActivityLog.objects.select_related('user').get(log_id=log_id)
        except ActivityLog.DoesNotExist:
            return Response(
                {'error': 'Activity log not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ActivityLogDetailSerializer(log)
        return Response(serializer.data)


class ActivityStatisticsAPIView(APIView):
    """
    GET /api/logs/activity-timeline/statistics/
    
    Get activity statistics.
    """
    permission_classes = [permissions.IsAuthenticated, ActivityTimelinePermission]
    
    def get(self, request):
        """Get activity statistics."""
        # Get date range from query params
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        # Base queryset
        qs = ActivityLog.objects.filter(timestamp__gte=start_date)
        
        # Total count
        total = qs.count()
        
        # By entity type
        by_entity_type = dict(
            qs.values('entity_type').annotate(c=Count('id')).values_list('entity_type', 'c')
        )
        
        # By action type
        by_action_type = dict(
            qs.values('action').annotate(c=Count('id')).values_list('action', 'c')
        )
        
        # Top users
        top_users_data = (
            qs.values('actor_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        by_user = list(top_users_data)
        
        # Recent activities
        recent = qs.order_by('-timestamp')[:10]
        recent_activities = ActivityLogSerializer(recent, many=True).data
        
        response_data = {
            'total': total,
            'by_entity_type': by_entity_type,
            'by_action_type': by_action_type,
            'by_user': by_user,
            'recent_activities': recent_activities,
        }
        
        return Response(response_data)


class EntityActivityAPIView(APIView):
    """
    GET /api/logs/activity-timeline/entity/{entity_type}/{entity_id}/
    
    Get activity history for a specific entity.
    """
    permission_classes = [permissions.IsAuthenticated, ActivityTimelinePermission]
    
    def get(self, request, entity_type, entity_id):
        """Get activity history for entity."""
        # Validate entity type
        valid_types = ['asset', 'ticket', 'project', 'user']
        if entity_type.lower() not in valid_types:
            return Response(
                {'error': f'Invalid entity_type. Must be one of: {valid_types}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get limit from params
        limit = int(request.query_params.get('limit', 50))
        limit = min(limit, 100)  # Cap at 100
        
        # Get logs for entity
        logs = ActivityLog.objects.filter(
            entity_type__iexact=entity_type,
            entity_id=entity_id,
        ).select_related('user').order_by('-timestamp')[:limit]
        
        serializer = ActivityLogSerializer(logs, many=True)
        return Response({
            'entity_type': entity_type,
            'entity_id': entity_id,
            'results': serializer.data,
            'count': len(logs),
        })


# =============================================================================
# Simple function-based views for backward compatibility
# =============================================================================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, ActivityTimelinePermission])
def activity_timeline_view(request):
    """
    Function-based view for Activity Timeline.
    
    GET /api/logs/activity-timeline/
    """
    # Same logic as class-based view
    return ActivityTimelineAPIView().get(request)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, ActivityTimelinePermission])
def activity_statistics_view(request):
    """
    Function-based view for Activity Statistics.
    
    GET /api/logs/activity-timeline/statistics/
    """
    return ActivityStatisticsAPIView().get(request)

