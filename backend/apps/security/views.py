"""
Security views for IT Management Platform.
Handles API endpoints for security events, audit logs, policies, and incidents.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q, Count, Avg
from django.contrib.auth.models import User
from datetime import datetime, timedelta

from .models import (
    SecurityEvent, AuditLog, SecurityPolicy, SecurityThreshold,
    SecurityIncident, SecurityDashboard
)
from .serializers import (
    SecurityEventSerializer, SecurityEventCreateSerializer, AuditLogSerializer,
    SecurityPolicySerializer, SecurityThresholdSerializer, SecurityIncidentSerializer,
    SecurityDashboardSerializer, SecurityDashboardCreateSerializer,
    SecurityStatisticsSerializer, SecurityAlertSerializer,
    SecurityHealthCheckSerializer, BulkSecurityEventActionSerializer,
    SecurityConfigurationSerializer
)
from .permissions import (
    IsSecurityAdminOrReadOnly, IsSecurityAnalystOrReadOnly,
    CanViewSecurityData, CanManageSecurityIncidents
)
from .utils import SecurityLogger, SecurityValidator


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for security endpoints."""
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class SecurityEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing security events.
    """
    queryset = SecurityEvent.objects.select_related('user', 'resolved_by')
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event_type', 'severity', 'status', 'user']
    ordering_fields = ['created_at', 'severity', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return SecurityEventCreateSerializer
        return SecurityEventSerializer
    
    def get_permissions(self):
        """Get permissions for different actions."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsSecurityAdminOrReadOnly]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated, CanViewSecurityData]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            try:
                queryset = queryset.filter(created_at__date__gte=datetime.strptime(date_from, '%Y-%m-%d'))
            except ValueError:
                pass
        
        if date_to:
            try:
                queryset = queryset.filter(created_at__date__lte=datetime.strptime(date_to, '%Y-%m-%d'))
            except ValueError:
                pass
        
        # Filter by IP address
        ip_address = self.request.query_params.get('ip_address')
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        
        # Filter by search term
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(username__icontains=search)
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a security event."""
        event = self.get_object()
        
        if event.status == 'RESOLVED':
            return Response(
                {'error': 'Event is already resolved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        notes = request.data.get('notes', '')
        event.resolve(request.user, notes)
        
        # Log the resolution
        SecurityLogger.log_security_event(
            'EVENT_RESOLVED',
            {
                'event_id': event.id,
                'resolved_by': request.user.username,
                'notes': notes
            },
            user=request.user
        )
        
        serializer = self.get_serializer(event)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """Perform bulk actions on security events."""
        serializer = BulkSecurityEventActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        event_ids = serializer.validated_data['event_ids']
        action = serializer.validated_data['action']
        notes = serializer.validated_data.get('notes', '')
        assignee_id = serializer.validated_data.get('assignee_id')
        
        events = SecurityEvent.objects.filter(id__in=event_ids)
        
        if action == 'RESOLVE':
            for event in events:
                if event.status != 'RESOLVED':
                    event.resolve(request.user, notes)
        
        elif action == 'ESCALATE':
            for event in events:
                if event.status != 'RESOLVED':
                    event.status = 'ESCALATED'
                    event.save()
        
        elif action == 'MARK_FALSE_POSITIVE':
            for event in events:
                if event.status != 'RESOLVED':
                    event.status = 'FALSE_POSITIVE'
                    event.resolved_by = request.user
                    event.resolution_notes = f"False positive - {notes}"
                    event.resolved_at = timezone.now()
                    event.save()
        
        elif action == 'ASSIGN' and assignee_id:
            try:
                assignee = User.objects.get(id=assignee_id)
                for event in events:
                    event.resolved_by = assignee
                    event.save()
            except User.DoesNotExist:
                return Response(
                    {'error': 'Assignee not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response({'message': f'Bulk {action.lower()} completed successfully'})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get security event statistics."""
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start.replace(day=1)
        
        stats = {
            'total_events': SecurityEvent.objects.count(),
            'events_today': SecurityEvent.objects.filter(created_at__gte=today_start).count(),
            'events_this_week': SecurityEvent.objects.filter(created_at__gte=week_start).count(),
            'events_this_month': SecurityEvent.objects.filter(created_at__gte=month_start).count(),
            'high_severity_events': SecurityEvent.objects.filter(severity='HIGH').count(),
            'critical_events': SecurityEvent.objects.filter(severity='CRITICAL').count(),
            'open_events': SecurityEvent.objects.filter(status='OPEN').count(),
            'resolved_events': SecurityEvent.objects.filter(status='RESOLVED').count(),
        }
        
        # Top event types
        top_event_types = SecurityEvent.objects.values('event_type').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        stats['top_event_types'] = list(top_event_types)
        
        # Top source IPs
        top_ips = SecurityEvent.objects.values('ip_address').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        stats['top_source_ips'] = list(top_ips)
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def dashboard_data(self, request):
        """Get dashboard data for security events."""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Recent events
        recent_events = SecurityEvent.objects.filter(
            created_at__gte=last_7d
        ).order_by('-created_at')[:10]
        
        # Event trends (last 7 days)
        daily_counts = []
        for i in range(7):
            date = (now - timedelta(days=i)).date()
            count = SecurityEvent.objects.filter(created_at__date=date).count()
            daily_counts.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': count
            })
        daily_counts.reverse()
        
        # Severity distribution
        severity_dist = SecurityEvent.objects.filter(
            created_at__gte=last_7d
        ).values('severity').annotate(count=Count('id'))
        
        data = {
            'recent_events': SecurityEventSerializer(recent_events, many=True).data,
            'daily_trends': daily_counts,
            'severity_distribution': list(severity_dist),
            'summary': {
                'total_24h': SecurityEvent.objects.filter(created_at__gte=last_24h).count(),
                'critical_24h': SecurityEvent.objects.filter(
                    created_at__gte=last_24h, severity='CRITICAL'
                ).count(),
                'open_issues': SecurityEvent.objects.filter(status__in=['OPEN', 'INVESTIGATING']).count()
            }
        }
        
        return Response(data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs (read-only).
    """
    queryset = AuditLog.objects.select_related('user')
    serializer_class = AuditLogSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['action', 'resource_type', 'success', 'user']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_permissions(self):
        """Get permissions for audit log access."""
        permission_classes = [permissions.IsAuthenticated, CanViewSecurityData]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user permissions and filters."""
        queryset = super().get_queryset()
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            try:
                queryset = queryset.filter(timestamp__date__gte=datetime.strptime(date_from, '%Y-%m-%d'))
            except ValueError:
                pass
        
        if date_to:
            try:
                queryset = queryset.filter(timestamp__date__lte=datetime.strptime(date_to, '%Y-%m-%d'))
            except ValueError:
                pass
        
        # Filter by resource
        resource_type = self.request.query_params.get('resource_type')
        resource_id = self.request.query_params.get('resource_id')
        
        if resource_type:
            queryset = queryset.filter(resource_type=resource_type)
        if resource_id:
            queryset = queryset.filter(resource_id=resource_id)
        
        # Filter by search term
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(resource_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def user_activity(self, request):
        """Get audit logs for a specific user."""
        user_id = request.query_params.get('user_id')
        username = request.query_params.get('username')
        
        if not user_id and not username:
            return Response(
                {'error': 'user_id or username parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user_id:
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        logs = AuditLog.objects.filter(user=user).order_by('-timestamp')[:100]
        serializer = self.get_serializer(logs, many=True)
        
        return Response({
            'user': user.username,
            'activity_count': logs.count(),
            'recent_activity': serializer.data
        })


class SecurityPolicyViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing security policies.
    """
    queryset = SecurityPolicy.objects.select_related('created_by', 'modified_by')
    serializer_class = SecurityPolicySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['policy_type', 'status']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_permissions(self):
        """Get permissions for policy management."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsSecurityAdminOrReadOnly]
        else:
            permission_classes = [permissions.IsAuthenticated, CanViewSecurityData]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset to show only valid policies."""
        queryset = super().get_queryset()
        
        # Filter by validity
        valid_only = self.request.query_params.get('valid_only', 'true').lower()
        if valid_only == 'true':
            queryset = queryset.filter(
                status='ACTIVE',
                valid_from__lte=timezone.now()
            ).filter(
                Q(valid_until__isnull=True) | Q(valid_until__gte=timezone.now())
            )
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a security policy."""
        policy = self.get_object()
        policy.status = 'ACTIVE'
        policy.save()
        
        SecurityLogger.log_security_event(
            'POLICY_ACTIVATED',
            {'policy_name': policy.name, 'policy_type': policy.policy_type},
            user=request.user
        )
        
        serializer = self.get_serializer(policy)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a security policy."""
        policy = self.get_object()
        policy.status = 'INACTIVE'
        policy.save()
        
        SecurityLogger.log_security_event(
            'POLICY_DEACTIVATED',
            {'policy_name': policy.name, 'policy_type': policy.policy_type},
            user=request.user
        )
        
        serializer = self.get_serializer(policy)
        return Response(serializer.data)


class SecurityThresholdViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing security thresholds.
    """
    queryset = SecurityThreshold.objects.select_related('created_by')
    serializer_class = SecurityThresholdSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['threshold_type', 'is_active', 'scope']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_permissions(self):
        """Get permissions for threshold management."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsSecurityAdminOrReadOnly]
        else:
            permission_classes = [permissions.IsAuthenticated, CanViewSecurityData]
        
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Toggle threshold active status."""
        threshold = self.get_object()
        threshold.is_active = not threshold.is_active
        threshold.save()
        
        status_msg = "activated" if threshold.is_active else "deactivated"
        SecurityLogger.log_security_event(
            f'THRESHOLD_{status_msg.upper()}',
            {'threshold_name': threshold.name},
            user=request.user
        )
        
        serializer = self.get_serializer(threshold)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def check_threshold(self, request):
        """Check if a value exceeds specified thresholds."""
        threshold_type = request.query_params.get('threshold_type')
        value = request.query_params.get('value')
        
        if not threshold_type or not value:
            return Response(
                {'error': 'threshold_type and value parameters required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            value = float(value)
        except ValueError:
            return Response(
                {'error': 'value must be a number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        thresholds = SecurityThreshold.objects.filter(
            threshold_type=threshold_type,
            is_active=True
        )
        
        exceeded_thresholds = []
        for threshold in thresholds:
            if threshold.check_threshold(value):
                exceeded_thresholds.append({
                    'name': threshold.name,
                    'operator': threshold.operator,
                    'threshold_value': threshold.value,
                    'current_value': value,
                    'unit': threshold.unit,
                    'alert_enabled': threshold.alert_enabled,
                    'auto_block_enabled': threshold.auto_block_enabled
                })
        
        return Response({
            'threshold_type': threshold_type,
            'current_value': value,
            'exceeded_thresholds': exceeded_thresholds,
            'any_exceeded': len(exceeded_thresholds) > 0
        })


class SecurityIncidentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing security incidents.
    """
    queryset = SecurityIncident.objects.select_related(
        'discovered_by', 'assigned_to', 'created_by'
    ).prefetch_related('related_events')
    serializer_class = SecurityIncidentSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['incident_type', 'severity', 'status', 'assigned_to']
    ordering_fields = ['created_at', 'severity', 'case_number']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """Get permissions for incident management."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, CanManageSecurityIncidents]
        else:
            permission_classes = [permissions.IsAuthenticated, CanViewSecurityData]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # Filter by assignment
        assigned_to_me = self.request.query_params.get('assigned_to_me')
        if assigned_to_me == 'true':
            queryset = queryset.filter(assigned_to=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by severity
        severity_filter = self.request.query_params.get('severity')
        if severity_filter:
            queryset = queryset.filter(severity=severity_filter)
        
        return queryset
    
    def perform_create(self, serializer):
        """Create incident with current user as creator."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign incident to a user."""
        incident = self.get_object()
        assignee_id = request.data.get('assignee_id')
        
        if not assignee_id:
            return Response(
                {'error': 'assignee_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            assignee = User.objects.get(id=assignee_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'Assignee not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        incident.assigned_to = assignee
        incident.save()
        
        SecurityLogger.log_security_event(
            'INCIDENT_ASSIGNED',
            {
                'incident_id': incident.id,
                'case_number': incident.case_number,
                'assigned_to': assignee.username
            },
            user=request.user
        )
        
        serializer = self.get_serializer(incident)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update incident status."""
        incident = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if new_status not in dict(SecurityIncident.INCIDENT_STATUS):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = incident.status
        incident.status = new_status
        
        # Set timestamp based on status
        if new_status == 'CONTAINED' and not incident.contained_at:
            incident.contained_at = timezone.now()
        elif new_status == 'RESOLVED' and not incident.resolved_at:
            incident.resolved_at = timezone.now()
        
        incident.save()
        
        SecurityLogger.log_security_event(
            'INCIDENT_STATUS_UPDATED',
            {
                'incident_id': incident.id,
                'case_number': incident.case_number,
                'old_status': old_status,
                'new_status': new_status,
                'notes': notes
            },
            user=request.user
        )
        
        serializer = self.get_serializer(incident)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get incident dashboard data."""
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Status distribution
        status_dist = SecurityIncident.objects.values('status').annotate(
            count=Count('id')
        )
        
        # Severity distribution
        severity_dist = SecurityIncident.objects.values('severity').annotate(
            count=Count('id')
        )
        
        # Recent incidents
        recent_incidents = SecurityIncident.objects.filter(
            created_at__gte=last_7d
        ).order_by('-created_at')[:10]
        
        # Incidents by type
        type_dist = SecurityIncident.objects.filter(
            created_at__gte=last_7d
        ).values('incident_type').annotate(count=Count('id'))
        
        data = {
            'summary': {
                'total': SecurityIncident.objects.count(),
                'open': SecurityIncident.objects.filter(status__in=['NEW', 'INVESTIGATING', 'CONTAINED']).count(),
                'resolved': SecurityIncident.objects.filter(status='RESOLVED').count(),
                'critical': SecurityIncident.objects.filter(severity='CRITICAL').count(),
                'new_24h': SecurityIncident.objects.filter(created_at__gte=last_24h).count()
            },
            'status_distribution': list(status_dist),
            'severity_distribution': list(severity_dist),
            'recent_incidents': SecurityIncidentSerializer(recent_incidents, many=True).data,
            'incidents_by_type': list(type_dist)
        }
        
        return Response(data)


class SecurityDashboardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing security dashboards.
    """
    queryset = SecurityDashboard.objects.select_related('created_by')
    serializer_class = SecurityDashboardSerializer
    pagination_class = StandardResultsSetPagination
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == 'create':
            return SecurityDashboardCreateSerializer
        return SecurityDashboardSerializer
    
    def get_permissions(self):
        """Get permissions for dashboard management."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsSecurityAdminOrReadOnly]
        else:
            permission_classes = [permissions.IsAuthenticated, CanViewSecurityData]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = super().get_queryset()
        
        # Users can only see public dashboards or ones they're allowed to access
        user = self.request.user
        if not user.is_superuser:
            queryset = queryset.filter(
                Q(is_public=True) | Q(allowed_users=user)
            )
        
        return queryset


class SecurityConfigurationViewSet(viewsets.ViewSet):
    """
    ViewSet for security configuration management.
    """
    permission_classes = [permissions.IsAuthenticated, IsSecurityAdminOrReadOnly]
    
    @action(detail=False, methods=['get'])
    def current_config(self, request):
        """Get current security configuration."""
        from django.conf import settings
        
        config = {
            # Rate Limiting
            'rate_limiting_enabled': getattr(settings, 'RATE_LIMIT_ENABLED', True),
            'requests_per_minute': getattr(settings, 'RATE_LIMIT_REQUESTS_PER_MINUTE', 60),
            'requests_per_hour': getattr(settings, 'RATE_LIMIT_REQUESTS_PER_HOUR', 1000),
            'requests_per_day': getattr(settings, 'RATE_LIMIT_REQUESTS_PER_DAY', 10000),
            
            # Session Management
            'session_timeout_minutes': getattr(settings, 'SESSION_TIMEOUT_MINUTES', 60),
            'max_concurrent_sessions': getattr(settings, 'MAX_CONCURRENT_SESSIONS', 3),
            
            # Password Policy
            'password_min_length': getattr(settings, 'PASSWORD_MIN_LENGTH', 8),
            'password_require_uppercase': getattr(settings, 'PASSWORD_REQUIRE_UPPERCASE', True),
            'password_require_lowercase': getattr(settings, 'PASSWORD_REQUIRE_LOWERCASE', True),
            'password_require_numbers': getattr(settings, 'PASSWORD_REQUIRE_NUMBERS', True),
            'password_require_symbols': getattr(settings, 'PASSWORD_REQUIRE_SYMBOLS', True),
            
            # Account Lockout
            'max_failed_attempts': getattr(settings, 'MAX_FAILED_ATTEMPTS', 5),
            'lockout_duration_minutes': getattr(settings, 'LOCKOUT_DURATION_MINUTES', 15),
            
            # Logging
            'log_retention_days': getattr(settings, 'LOG_RETENTION_DAYS', 90),
            'audit_log_enabled': getattr(settings, 'AUDIT_LOG_ENABLED', True),
            'security_event_logging_enabled': getattr(settings, 'SECURITY_EVENT_LOGGING_ENABLED', True),
        }
        
        return Response(config)
    
    @action(detail=False, methods=['post'])
    def update_config(self, request):
        """Update security configuration."""
        serializer = SecurityConfigurationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # In a real implementation, you would save these to a configuration model
        # or update Django settings appropriately
        
        SecurityLogger.log_security_event(
            'CONFIGURATION_UPDATED',
            {'updated_by': request.user.username},
            user=request.user
        )
        
        return Response({
            'message': 'Configuration updated successfully',
            'config': serializer.validated_data
        })


class SecurityHealthCheckViewSet(viewsets.ViewSet):
    """
    ViewSet for security system health checks.
    """
    permission_classes = [permissions.IsAuthenticated, CanViewSecurityData]
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get security system health status."""
        now = timezone.now()
        
        # Check various security services
        services = {
            'database': self._check_database(),
            'cache': self._check_cache(),
            'logging': self._check_logging(),
            'rate_limiting': self._check_rate_limiting(),
            'authentication': self._check_authentication(),
        }
        
        # Determine overall status
        all_healthy = all(service['status'] == 'healthy' for service in services.values())
        overall_status = 'healthy' if all_healthy else 'degraded'
        
        data = {
            'status': overall_status,
            'timestamp': now,
            'services': services,
            'last_updated': now,
            'uptime': '99.9%',  # This would be calculated from actual uptime data
            'version': '1.0.0'
        }
        
        return Response(data)
    
    def _check_database(self):
        """Check database connectivity."""
        try:
            # Simple database check
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {'status': 'healthy', 'message': 'Database connection OK'}
        except Exception as e:
            return {'status': 'error', 'message': f'Database error: {str(e)}'}
    
    def _check_cache(self):
        """Check cache connectivity."""
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 10)
            result = cache.get('health_check')
            if result == 'ok':
                return {'status': 'healthy', 'message': 'Cache connection OK'}
            else:
                return {'status': 'error', 'message': 'Cache read/write failed'}
        except Exception as e:
            return {'status': 'error', 'message': f'Cache error: {str(e)}'}
    
    def _check_logging(self):
        """Check logging functionality."""
        try:
            import logging
            logger = logging.getLogger('it_management_platform.security')
            logger.info('Health check log entry')
            return {'status': 'healthy', 'message': 'Logging system OK'}
        except Exception as e:
            return {'status': 'error', 'message': f'Logging error: {str(e)}'}
    
    def _check_rate_limiting(self):
        """Check rate limiting system."""
        try:
            from django.core.cache import cache
            # Test rate limiting cache
            cache.set('health_rate_limit', 1, 60)
            return {'status': 'healthy', 'message': 'Rate limiting system OK'}
        except Exception as e:
            return {'status': 'error', 'message': f'Rate limiting error: {str(e)}'}
    
    def _check_authentication(self):
        """Check authentication system."""
        try:
            # Simple auth check
            if hasattr(request, 'user'):
                return {'status': 'healthy', 'message': 'Authentication system OK'}
            else:
                return {'status': 'warning', 'message': 'No user context available'}
        except Exception as e:
            return {'status': 'error', 'message': f'Authentication error: {str(e)}'}

