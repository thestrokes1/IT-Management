"""
Log views for IT Management Platform.
Comprehensive activity logging and audit trail management.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator

import csv
import io

from apps.logs.models import (
    LogCategory, ActivityLog, AuditLog, SystemLog, SecurityEvent,
    LogAlert, LogAlertTrigger, LogReport, LogRetention, LogStatistics
)

from apps.logs.serializers import (
    LogCategorySerializer,
    ActivityLogSerializer, ActivityLogListSerializer,
    AuditLogSerializer, AuditLogListSerializer,
    SystemLogSerializer, SystemLogListSerializer,
    SecurityEventSerializer, SecurityEventListSerializer,
    LogAlertSerializer, LogAlertTriggerSerializer,
    LogReportSerializer, LogRetentionSerializer,
    LogStatisticsSerializer,
    LogSearchSerializer, LogExportSerializer,
    LogAlertCreateSerializer, LogReportCreateSerializer,
    SecurityEventUpdateSerializer
)

from apps.logs.permissions import *


# --------------------
# CATEGORY
# --------------------
class LogCategoryViewSet(viewsets.ModelViewSet):
    queryset = LogCategory.objects.all()
    serializer_class = LogCategorySerializer
    permission_classes = [permissions.IsAuthenticated, CanManageLogCategories]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'name']


# --------------------
# ACTIVITY LOGS
# --------------------
class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.select_related('user', 'category')
    permission_classes = [permissions.IsAuthenticated, CanViewLogs]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['action', 'level', 'category', 'user']
    ordering = ['-timestamp']

    def get_serializer_class(self):
        return ActivityLogSerializer if self.action == 'retrieve' else ActivityLogListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        if params.get('date_from'):
            qs = qs.filter(timestamp__date__gte=params['date_from'])
        if params.get('date_to'):
            qs = qs.filter(timestamp__date__lte=params['date_to'])
        if params.get('ip_address'):
            qs = qs.filter(ip_address=params['ip_address'])

        return qs

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        qs = self.get_queryset()
        return Response({
            'total': qs.count(),
            'by_level': dict(qs.values('level').annotate(c=Count('id')).values_list('level', 'c')),
            'by_action': dict(qs.values('action').annotate(c=Count('id')).values_list('action', 'c')),
        })

    @action(detail=False, methods=['post'], permission_classes=[CanCreateCustomLogs])
    def create_custom_log(self, request):
        serializer = ActivityLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# --------------------
# AUDIT LOGS
# --------------------
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.select_related('user', 'approved_by')
    permission_classes = [permissions.IsAuthenticated, CanViewAuditLogs]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['action', 'risk_level', 'approval_status']
    ordering = ['-timestamp']

    def get_serializer_class(self):
        return AuditLogSerializer if self.action == 'retrieve' else AuditLogListSerializer


# --------------------
# SYSTEM LOGS
# --------------------
class SystemLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SystemLog.objects.all()
    permission_classes = [permissions.IsAuthenticated, CanViewSystemLogs]
    ordering = ['-timestamp']

    def get_serializer_class(self):
        return SystemLogSerializer if self.action == 'retrieve' else SystemLogListSerializer


# --------------------
# SECURITY EVENTS
# --------------------
class SecurityEventViewSet(viewsets.ModelViewSet):
    queryset = SecurityEvent.objects.select_related('affected_user', 'assigned_to')
    permission_classes = [permissions.IsAuthenticated, CanViewSecurityEvents]
    ordering = ['-detected_at']

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return SecurityEventUpdateSerializer
        return SecurityEventSerializer if self.action == 'retrieve' else SecurityEventListSerializer


# --------------------
# ALERTS
# --------------------
class LogAlertViewSet(viewsets.ModelViewSet):
    queryset = LogAlert.objects.select_related('created_by')
    permission_classes = [permissions.IsAuthenticated, CanManageLogAlerts]

    def get_serializer_class(self):
        return LogAlertCreateSerializer if self.action == 'create' else LogAlertSerializer


class LogAlertTriggerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LogAlertTrigger.objects.select_related('alert')
    serializer_class = LogAlertTriggerSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewLogAlerts]


# --------------------
# REPORTS
# --------------------
class LogReportViewSet(viewsets.ModelViewSet):
    queryset = LogReport.objects.select_related('created_by')
    permission_classes = [permissions.IsAuthenticated, CanManageLogReports]

    def get_serializer_class(self):
        return LogReportCreateSerializer if self.action == 'create' else LogReportSerializer


# --------------------
# RETENTION
# --------------------
class LogRetentionViewSet(viewsets.ModelViewSet):
    queryset = LogRetention.objects.all()
    serializer_class = LogRetentionSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageLogRetention]


# --------------------
# STATISTICS
# --------------------
class LogStatisticsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = LogStatistics.objects.order_by('-date')
    serializer_class = LogStatisticsSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewLogStatistics]


# --------------------
# SEARCH
# --------------------
class LogSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanViewLogs]

    def get(self, request):
        serializer = LogSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        qs = ActivityLog.objects.select_related('user', 'category')

        if data.get('search'):
            qs = qs.filter(
                Q(title__icontains=data['search']) |
                Q(description__icontains=data['search'])
            )

        page = int(request.query_params.get('page', 1))
        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(page)

        return Response({
            'results': ActivityLogListSerializer(page_obj, many=True).data,
            'count': paginator.count
        })


# --------------------
# EXPORT
# --------------------
class LogExportView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanExportLogs]

    def post(self, request):
        serializer = LogExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        queryset_map = {
            'ACTIVITY': (ActivityLog.objects.all(), ActivityLogSerializer),
            'AUDIT': (AuditLog.objects.all(), AuditLogSerializer),
            'SYSTEM': (SystemLog.objects.all(), SystemLogSerializer),
            'SECURITY': (SecurityEvent.objects.all(), SecurityEventSerializer),
        }

        qs, ser = queryset_map[data['log_type']]
        qs = qs[:10000]

        if data['format'] == 'CSV':
            return self._csv(qs, ser, data['log_type'])
        return JsonResponse(ser(qs, many=True).data, safe=False)

    def _csv(self, qs, serializer_class, name):
        output = io.StringIO()
        writer = csv.writer(output)

        if qs.exists():
            headers = serializer_class(qs.first()).data.keys()
            writer.writerow(headers)

            for obj in qs:
                writer.writerow(serializer_class(obj).data.values())

        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{name.lower()}_logs.csv"'
        return response


# --------------------
# DASHBOARD
# --------------------
class LogDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated, CanAccessLogDashboard]

    def get(self, request):
        now = timezone.now()
        last_24h = now - timedelta(hours=24)

        return Response({
            'activity_24h': ActivityLog.objects.filter(timestamp__gte=last_24h).count(),
            'security_open': SecurityEvent.objects.filter(status__in=['OPEN', 'INVESTIGATING']).count(),
            'generated_at': now.isoformat()
        })
