"""
Asset views for IT Management Platform.
API endpoints for asset management with role-based access control.
"""

from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime, timedelta

from apps.assets.models import (
    AssetCategory, Asset, HardwareAsset, SoftwareAsset,
    AssetAssignment, AssetMaintenance, AssetAuditLog, AssetReport
)
from apps.assets.serializers import (
    AssetCategorySerializer, AssetListSerializer, AssetDetailSerializer,
    AssetCreateSerializer, AssetUpdateSerializer, HardwareAssetSerializer,
    HardwareAssetCreateSerializer, SoftwareAssetSerializer,
    SoftwareAssetCreateSerializer, AssetAssignmentSerializer,
    AssetAssignmentCreateSerializer, AssetMaintenanceSerializer,
    AssetAuditLogSerializer, AssetReportSerializer, AssetStatisticsSerializer,
    AssetSearchSerializer
)
from apps.assets.permissions import (
    CanManageAssets, IsAssetOwnerOrReadOnly, CanAssignAssets,
    CanViewMaintenanceRecords, CanManageMaintenance, CanViewAuditLogs,
    CanGenerateReports, CanManageCategories
)
from apps.users.models import User

class AssetCategoryViewSet(viewsets.ModelViewSet):
    """
    Asset category management viewset.
    """
    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    permission_classes = [CanManageCategories]
    
    def get_queryset(self):
        queryset = AssetCategory.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('name')

class AssetViewSet(viewsets.ModelViewSet):
    """
    Asset management viewset with comprehensive filtering and actions.
    """
    permission_classes = [CanManageAssets, IsAssetOwnerOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AssetListSerializer
        elif self.action == 'retrieve':
            return AssetDetailSerializer
        elif self.action == 'create':
            return AssetCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return AssetUpdateSerializer
        return AssetDetailSerializer
    
    def get_queryset(self):
        queryset = Asset.objects.select_related(
            'category', 'assigned_to', 'created_by', 'updated_by'
        ).prefetch_related('assignments', 'maintenance_records')
        
        # Filter by asset type
        asset_type = self.request.query_params.get('asset_type')
        if asset_type:
            queryset = queryset.filter(asset_type=asset_type)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by assigned user
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        
        # Filter by location
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Filter by manufacturer
        manufacturer = self.request.query_params.get('manufacturer')
        if manufacturer:
            queryset = queryset.filter(manufacturer__icontains=manufacturer)
        
        # Filter by warranty status
        warranty_expiring = self.request.query_params.get('warranty_expiring')
        if warranty_expiring and warranty_expiring.lower() == 'true':
            thirty_days_from_now = timezone.now().date() + timedelta(days=30)
            queryset = queryset.filter(
                warranty_expiry__isnull=False,
                warranty_expiry__lte=thirty_days_from_now,
                warranty_expiry__gte=timezone.now().date()
            )
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(serial_number__icontains=search) |
                Q(model__icontains=search) |
                Q(manufacturer__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to properly handle signal disconnection and cascade deletion.
        """
        from django.db.models.signals import pre_delete
        from django.db import transaction
        
        instance = self.get_object()
        
        # Temporarily disconnect the pre_delete signal to prevent
        # creating an AssetAuditLog while the asset is being deleted
        try:
            from apps.assets.signals import create_asset_deletion_log
            pre_delete.disconnect(create_asset_deletion_log, sender=Asset)
            signal_disconnected = True
        except Exception:
            signal_disconnected = False
        
        try:
            with transaction.atomic():
                # Delete related records first
                AssetMaintenance.objects.filter(asset=instance).delete()
                AssetAuditLog.objects.filter(asset=instance).delete()
                AssetAssignment.objects.filter(asset=instance).delete()
                
                # Delete the asset (CASCADE handles any remaining references)
                instance.delete()
                
                return Response(
                    {'message': f'Asset "{instance.name}" deleted successfully.'},
                    status=status.HTTP_200_OK
                )
        finally:
            # Reconnect the signal if it was disconnected
            if signal_disconnected:
                try:
                    pre_delete.connect(create_asset_deletion_log, sender=Asset)
                except Exception:
                    pass
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign asset to a user."""
        asset = self.get_object()
        serializer = AssetAssignmentCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user_id']
            assignment_type = serializer.validated_data['assignment_type']
            notes = serializer.validated_data.get('notes', '')
            
            if assignment_type == 'ASSIGNMENT':
                # Check if asset is already assigned
                if asset.assigned_to and asset.assigned_to != user:
                    return Response({
                        'error': 'Asset is already assigned to another user.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                asset.assign_to_user(user, request.user)
                
                # Create assignment record
                AssetAssignment.objects.create(
                    asset=asset,
                    user=user,
                    assignment_type='ASSIGNMENT',
                    assigned_by=request.user,
                    notes=notes
                )
                
                # Create audit log
                AssetAuditLog.objects.create(
                    asset=asset,
                    user=request.user,
                    action='ASSIGNED',
                    description=f'Asset assigned to {user.username}',
                    new_values={'assigned_to': user.username}
                )
                
                return Response({'message': 'Asset assigned successfully'})
            
            elif assignment_type == 'UNASSIGNMENT':
                if not asset.assigned_to:
                    return Response({
                        'error': 'Asset is not currently assigned.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                old_assignee = asset.assigned_to
                asset.unassign(request.user)
                
                # Create assignment record
                AssetAssignment.objects.create(
                    asset=asset,
                    user=old_assignee,
                    assignment_type='UNASSIGNMENT',
                    assigned_by=request.user,
                    notes=notes
                )
                
                # Create audit log
                AssetAuditLog.objects.create(
                    asset=asset,
                    user=request.user,
                    action='UNASSIGNED',
                    description=f'Asset unassigned from {old_assignee.username}',
                    old_values={'assigned_to': old_assignee.username}
                )
                
                return Response({'message': 'Asset unassigned successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change asset status."""
        asset = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response({
                'error': 'Status is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = asset.status
        asset.update_status(new_status, request.user)
        
        # Create audit log
        AssetAuditLog.objects.create(
            asset=asset,
            user=request.user,
            action='STATUS_CHANGED',
            description=f'Status changed from {old_status} to {new_status}',
            old_values={'status': old_status},
            new_values={'status': new_status}
        )
        
        return Response({'message': f'Status changed to {new_status}'})
    
    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        """Get asset assignment history."""
        asset = self.get_object()
        assignments = asset.assignments.select_related('user', 'assigned_by').all()
        serializer = AssetAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def maintenance(self, request, pk=None):
        """Get asset maintenance records."""
        asset = self.get_object()
        maintenance_records = asset.maintenance_records.select_related('created_by').all()
        serializer = AssetMaintenanceSerializer(maintenance_records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def audit_logs(self, request, pk=None):
        """Get asset audit logs."""
        asset = self.get_object()
        audit_logs = asset.audit_logs.select_related('user').all()
        serializer = AssetAuditLogSerializer(audit_logs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def hardware(self, request):
        """Get hardware assets only."""
        queryset = self.get_queryset().filter(asset_type='HARDWARE')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AssetListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AssetListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def software(self, request):
        """Get software assets only."""
        queryset = self.get_queryset().filter(asset_type='SOFTWARE')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AssetListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AssetListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def assigned(self, request):
        """Get assigned assets only."""
        queryset = self.get_queryset().filter(assigned_to__isnull=False)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AssetListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AssetListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unassigned(self, request):
        """Get unassigned assets only."""
        queryset = self.get_queryset().filter(assigned_to__isnull=True)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AssetListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AssetListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def warranty_expiring(self, request):
        """Get assets with expiring warranties."""
        thirty_days_from_now = timezone.now().date() + timedelta(days=30)
        queryset = self.get_queryset().filter(
            warranty_expiry__isnull=False,
            warranty_expiry__lte=thirty_days_from_now,
            warranty_expiry__gte=timezone.now().date()
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AssetListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AssetListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get asset statistics."""
        # Cache statistics for 5 minutes
        cache_key = f'asset_statistics_{request.user.id}'
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            return Response(cached_stats)
        
        total_assets = Asset.objects.count()
        hardware_assets = Asset.objects.filter(asset_type='HARDWARE').count()
        software_assets = Asset.objects.filter(asset_type='SOFTWARE').count()
        assigned_assets = Asset.objects.filter(assigned_to__isnull=False).count()
        unassigned_assets = total_assets - assigned_assets
        
        assets_by_status = dict(
            Asset.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        
        assets_by_category = dict(
            Asset.objects.values('category__name').annotate(count=Count('id')).values_list('category__name', 'count')
        )
        
        assets_by_type = dict(
            Asset.objects.values('asset_type').annotate(count=Count('id')).values_list('asset_type', 'count')
        )
        
        assets_under_warranty = Asset.objects.filter(
            warranty_expiry__isnull=False,
            warranty_expiry__gte=timezone.now().date()
        ).count()
        
        recent_assignments = AssetAssignment.objects.filter(
            is_active=True
        ).select_related('asset', 'user')[:10]
        
        upcoming_maintenance = AssetMaintenance.objects.filter(
            status__in=['SCHEDULED', 'IN_PROGRESS'],
            scheduled_date__gte=timezone.now()
        ).select_related('asset')[:10]
        
        stats = {
            'total_assets': total_assets,
            'hardware_assets': hardware_assets,
            'software_assets': software_assets,
            'assigned_assets': assigned_assets,
            'unassigned_assets': unassigned_assets,
            'assets_by_status': assets_by_status,
            'assets_by_category': assets_by_category,
            'assets_by_type': assets_by_type,
            'assets_under_warranty': assets_under_warranty,
            'recent_assignments': AssetAssignmentSerializer(recent_assignments, many=True).data,
            'upcoming_maintenance': AssetMaintenanceSerializer(upcoming_maintenance, many=True).data
        }
        
        cache.set(cache_key, stats, 300)  # Cache for 5 minutes
        return Response(stats)

class HardwareAssetViewSet(viewsets.ModelViewSet):
    """
    Hardware asset management viewset.
    """
    permission_classes = [CanManageAssets]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return HardwareAssetCreateSerializer
        return HardwareAssetSerializer
    
    def get_queryset(self):
        return HardwareAsset.objects.select_related('asset__category', 'asset__assigned_to').all()
    
    def perform_create(self, serializer):
        serializer.save()

class SoftwareAssetViewSet(viewsets.ModelViewSet):
    """
    Software asset management viewset.
    """
    permission_classes = [CanManageAssets]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SoftwareAssetCreateSerializer
        return SoftwareAssetSerializer
    
    def get_queryset(self):
        return SoftwareAsset.objects.select_related('asset__category', 'asset__assigned_to').all()
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def allocate_license(self, request, pk=None):
        """Allocate a license seat for a user."""
        software_asset = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if software_asset.seats_available <= 0:
            return Response({'error': 'No available license seats'}, status=status.HTTP_400_BAD_REQUEST)
        
        software_asset.seats_used += 1
        software_asset.save()
        
        return Response({'message': 'License allocated successfully'})

class AssetAssignmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Asset assignment history viewset.
    """
    serializer_class = AssetAssignmentSerializer
    permission_classes = [CanManageAssets]
    
    def get_queryset(self):
        queryset = AssetAssignment.objects.select_related('asset', 'user', 'assigned_by')
        
        # Filter by user
        user = self.request.query_params.get('user')
        if user:
            queryset = queryset.filter(user_id=user)
        
        # Filter by asset
        asset = self.request.query_params.get('asset')
        if asset:
            queryset = queryset.filter(asset_id=asset)
        
        # Filter by active assignments
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('-assigned_date')

class AssetMaintenanceViewSet(viewsets.ModelViewSet):
    """
    Asset maintenance management viewset.
    """
    serializer_class = AssetMaintenanceSerializer
    permission_classes = [CanManageMaintenance]
    
    def get_queryset(self):
        queryset = AssetMaintenance.objects.select_related('asset', 'created_by')
        
        # Filter by asset
        asset = self.request.query_params.get('asset')
        if asset:
            queryset = queryset.filter(asset_id=asset)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by maintenance type
        maintenance_type = self.request.query_params.get('maintenance_type')
        if maintenance_type:
            queryset = queryset.filter(maintenance_type=maintenance_type)
        
        return queryset.order_by('-scheduled_date')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark maintenance as completed."""
        maintenance = self.get_object()
        maintenance.status = 'COMPLETED'
        maintenance.completed_date = timezone.now()
        maintenance.save()
        
        return Response({'message': 'Maintenance marked as completed'})

class AssetAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Asset audit log viewset.
    """
    serializer_class = AssetAuditLogSerializer
    permission_classes = [CanViewAuditLogs]
    
    def get_queryset(self):
        queryset = AssetAuditLog.objects.select_related('asset', 'user')
        
        # Filter by asset
        asset = self.request.query_params.get('asset')
        if asset:
            queryset = queryset.filter(asset_id=asset)
        
        # Filter by user
        user = self.request.query_params.get('user')
        if user:
            queryset = queryset.filter(user_id=user)
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Date range filtering
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        
        if date_from:
            queryset = queryset.filter(timestamp__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__date__lte=date_to)
        
        return queryset.order_by('-timestamp')[:1000]  # Limit to recent 1000 records

class AssetSearchView(APIView):
    """
    Advanced asset search endpoint.
    """
    permission_classes = [CanManageAssets]
    
    def post(self, request):
        serializer = AssetSearchSerializer(data=request.data)
        
        if serializer.is_valid():
            queryset = Asset.objects.select_related('category', 'assigned_to')
            
            # Apply filters
            search = serializer.validated_data.get('search')
            asset_type = serializer.validated_data.get('asset_type')
            status = serializer.validated_data.get('status')
            category = serializer.validated_data.get('category')
            assigned_to = serializer.validated_data.get('assigned_to')
            location = serializer.validated_data.get('location')
            manufacturer = serializer.validated_data.get('manufacturer')
            warranty_expiring = serializer.validated_data.get('warranty_expiring')
            
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(description__icontains=search) |
                    Q(serial_number__icontains=search) |
                    Q(model__icontains=search) |
                    Q(manufacturer__icontains=search)
                )
            
            if asset_type:
                queryset = queryset.filter(asset_type=asset_type)
            
            if status:
                queryset = queryset.filter(status=status)
            
            if category:
                queryset = queryset.filter(category_id=category)
            
            if assigned_to:
                queryset = queryset.filter(assigned_to_id=assigned_to)
            
            if location:
                queryset = queryset.filter(location__icontains=location)
            
            if manufacturer:
                queryset = queryset.filter(manufacturer__icontains=manufacturer)
            
            if warranty_expiring:
                thirty_days_from_now = timezone.now().date() + timedelta(days=30)
                queryset = queryset.filter(
                    warranty_expiry__isnull=False,
                    warranty_expiry__lte=thirty_days_from_now,
                    warranty_expiry__gte=timezone.now().date()
                )
            
            # Paginate results
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            start = (page - 1) * page_size
            end = start + page_size
            
            results = queryset.order_by('-created_at')[start:end]
            total_count = queryset.count()
            
            response_data = {
                'results': AssetListSerializer(results, many=True).data,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            }
            
            return Response(response_data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
