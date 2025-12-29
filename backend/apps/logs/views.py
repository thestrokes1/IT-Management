"""
Log views for IT Management Platform.
Comprehensive activity logging and audit trail management.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
import json
import csv
import io
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator

from apps.logs.models import (
    LogCategory, ActivityLog, AuditLog, SystemLog, SecurityEvent,
    LogAlert, LogAlertTrigger, LogReport, LogRetention, LogStatistics
)
from apps.logs.serializers import (
    LogCategorySerializer, ActivityLogSerializer, ActivityLogListSerializer,
    AuditLogSerializer, AuditLogListSerializer, SystemLogSerializer,
    SystemLogListSerializer, SecurityEventSerializer, SecurityEventListSerializer,
    LogAlertSerializer, LogAlertTriggerSerializer, LogReportSerializer,
    LogRetentionSerializer, LogStatisticsSerializer, LogSearchSerializer,
    LogExportSerializer, LogAlertCreateSerializer, LogReportCreateSerializer,
    SecurityEventUpdateSerializer, AuditLogApprovalSerializer
)
from apps.logs.permissions import *

class LogCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing log categories.
    """
    queryset = LogCategory.objects.all()
    serializer_class = LogCategorySerializer
    permission_classes = [permissions.IsAuthenticated, CanManageLogCategories]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'name']
    search_fields = ['name', 'description']

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing activity logs.
    """
    queryset = ActivityLog.objects.select_related('user', 'category')
    serializer_class = ActivityLogListSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewLogs]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['action', 'level', 'category', 'user']
    search_fields = ['title', 'description', 'model_name', 'object_repr']
    ordering_fields = ['timestamp', 'action', 'level']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        
        # Apply IP filtering
        ip_address = self.request.query_params.get('ip_address')
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ActivityLogSerializer
        return ActivityLogListSerializer
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Get activity log statistics.
        """
        queryset = self.get_queryset()
        
        stats = {
            'total_logs': queryset.count(),
            'logs_by_level': dict(queryset.values('level').annotate(count=Count('id')).values_list('level', 'count')),
            'logs_by_action': dict(queryset.values('action').annotate(count=Count('id')).values_list('action', 'count')),
            'unique_users': queryset.filter(user__isnull=False).values('user').distinct().count(),
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def create_custom_log(self, request):
        """
        Create a custom activity log entry.
        """
        if not request.user.has_perm('logs.can_view_logs'):
            return Response({'detail': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ActivityLogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing audit logs.
    """
    queryset = AuditLog.objects.select_related('user', 'approved_by')
    serializer_class = AuditLogListSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewAuditLogs]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['action', 'risk_level', 'approval_status', 'user']
    search_fields = ['model_name', 'object_repr', 'changes_summary']
    ordering_fields = ['timestamp', 'action', 'risk_level']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AuditLogSerializer
        return AuditLogListSerializer

class SystemLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing system logs.
    """
    queryset = SystemLog.objects.all()
    serializer_class = SystemLogListSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewSystemLogs]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['level', 'component', 'server_name']
    search_fields = ['title', 'message', 'error_code']
    ordering_fields = ['timestamp', 'level', 'component']
    ordering = ['-timestamp']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SystemLogSerializer
        return SystemLogListSerializer

class SecurityEventViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing security events.
    """
    queryset = SecurityEvent.objects.select_related('affected_user', 'assigned_to')
    serializer_class = SecurityEventListSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewSecurityEvents]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event_type', 'severity', 'status', 'assigned_to']
    search_fields = ['title', 'description', 'source_ip']
    ordering_fields = ['detected_at', 'severity', 'status']
    ordering = ['-detected_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Apply date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(detected_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(detected_at__date__lte=date_to)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SecurityEventSerializer
        elif self.action in ['update', 'partial_update']:
            return SecurityEventUpdateSerializer
        return SecurityEventListSerializer

class LogAlertViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing log alerts.
    """
    queryset = LogAlert.objects.select_related('created_by')
    serializer_class = LogAlertSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageLogAlerts]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['severity', 'status', 'log_type']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'last_triggered']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LogAlertCreateSerializer
        return LogAlertSerializer

class LogAlertTriggerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing log alert triggers.
    """
    queryset = LogAlertTrigger.objects.select_related('alert', 'acknowledged_by')
    serializer_class = LogAlertTriggerSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewLogAlerts]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['alert', 'email_sent', 'sms_sent', 'webhook_sent']
    ordering_fields = ['triggered_at']
    ordering = ['-triggered_at']

class LogReportViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing log reports.
    """
    queryset = LogReport.objects.select_related('created_by')
    serializer_class = LogReportSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageLogReports]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['report_type', 'format', 'is_scheduled', 'is_public']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'usage_count']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LogReportCreateSerializer
        return LogReportSerializer

class LogRetentionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing log retention policies.
    """
    queryset = LogRetention.objects.all()
    serializer_class = LogRetentionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageLogRetention]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['log_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at']
    ordering = ['name']

class LogStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing log statistics.
    """
    queryset = LogStatistics.objects.all().order_by('-date')
    serializer_class = LogStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewLogStatistics]

class LogSearchView(APIView):
    """
    API view for searching logs across different types.
    """
    permission_classes = [permissions.IsAuthenticated, CanViewLogs]
    
    def get(self, request):
        """
        Search activity logs.
        """
        serializer = LogSearchSerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = ActivityLog.objects.select_related('user', 'category')
        data = serializer.validated_data
        
        # Apply filters
        if data.get('search'):
            queryset = queryset.filter(
                Q(title__icontains=data['search']) |
                Q(description__icontains=data['search']) |
                Q(model_name__icontains=data['search']) |
                Q(object_repr__icontains=data['search'])
            )
        
        # Apply additional filters
        if data.get('level'):
            queryset = queryset.filter(level=data['level'])
        if data.get('action'):
            queryset = queryset.filter(action=data['action'])
        if data.get('category'):
            queryset = queryset.filter(category_id=data['category'])
        if data.get('user'):
            queryset = queryset.filter(user_id=data['user'])
        
        # Paginate results
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = ActivityLogListSerializer(page_obj, many=True)
        
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': page,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous()
        })

class LogExportView(APIView):
    """
    API view for exporting logs.
    """
    permission_classes = [permissions.IsAuthenticated, CanExportLogs]
    
    def post(self, request):
        """
        Export logs in specified format.
        """
        serializer = LogExportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        log_type = data['log_type']
        format_type = data['format']
        
        # Get the appropriate queryset
        if log_type == 'ACTIVITY':
            queryset = ActivityLog.objects.select_related('user', 'category')
            serializer_class = ActivityLogSerializer
        elif log_type == 'AUDIT':
            queryset = AuditLog.objects.select_related('user')
            serializer_class = AuditLogSerializer
        elif log_type == 'SYSTEM':
            queryset = SystemLog.objects.all()
            serializer_class = SystemLogSerializer
        elif log_type == 'SECURITY':
            queryset = SecurityEvent.objects.select_related('affected_user', 'assigned_to')
            serializer_class = SecurityEventSerializer
        
        # Apply date filters
        if data.get('date_from'):
            queryset = queryset.filter(timestamp__date__gte=data['date_from'])
        if data.get('date_to'):
            queryset = queryset.filter(timestamp__date__lte=data['date_to'])
        
        # Apply additional filters
        filters = data.get('filters', {})
        for key, value in filters.items():
            queryset = queryset.filter(**{key: value})
        
        # Limit export size
        queryset = queryset[:10000]  # Limit to 10k records
        
        if format_type == 'CSV':
            return self.export_csv(queryset, serializer_class, log_type)
        elif format_type == 'JSON':
            return self.export_json(queryset, serializer_class)
        else:
            return Response({'detail': 'Unsupported format'}, status=status.HTTP_400_BAD_REQUEST)
    
    def export_csv(self, queryset, serializer_class, log_type):
        """
        Export logs as CSV.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        if queryset.exists():
            serializer = serializer_class(queryset.first())
            headers = list(serializer.data.keys())
            writer.writerow(headers)
        
        # Write data
        for item in queryset:
            serializer = serializer_class(item)
            writer.writerow([str(serializer.data.get(header, '')) for header in headers])
        
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{log_type.lower()}_logs_export.csv"'
        return response
    
    def export_json(self, queryset, serializer_class):
        """
        Export logs as JSON.
        """
        serializer = serializer_class(queryset, many=True)
        response = JsonResponse(serializer.data, safe=False)
        response['Content-Disposition'] = 'attachment; filename="logs_export.json"'
        return response

class LogDashboardView(APIView):
    """
    API view for log dashboard data.
    """
    permission_classes = [permissions.IsAuthenticated, CanAccessLogDashboard]
    
    def get(self, request):
        """
        Get dashboard statistics for all log types.
        """
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        # Activity log stats
        activity_stats = {
            'total_last_24h': ActivityLog.objects.filter(timestamp__gte=last_24h).count(),
            'total_last_7d': ActivityLog.objects.filter(timestamp__gte=last_7d).count(),
            'by_level': dict(ActivityLog.objects.filter(timestamp__gte=last_7d).values('level').annotate(count=Count('id')).values_list('level', 'count')),
        }
        
        # Security event stats
        security_stats = {
            'total_last_24h': SecurityEvent.objects.filter(detected_at__gte=last_24h).count(),
            'total_last_7d': SecurityEvent.objects.filter(detected_at__gte=last_7d).count(),
            'open_events': SecurityEvent.objects.filter(status__in=['OPEN', 'INVESTIGATING']).count(),
        }
        
        dashboard_data = {
            'activity_logs': activity_stats,
            'security_events': security_stats,
            'generated_at': now.isoformat()
        }
        
        return Response(dashboard_data)

