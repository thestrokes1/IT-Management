"""
Asset serializers for IT Management Platform.
Handles serialization and validation for asset-related operations.
"""

from rest_framework import serializers
from apps.assets.models import (
    AssetCategory, Asset, HardwareAsset, SoftwareAsset,
    AssetAssignment, AssetMaintenance, AssetAuditLog, AssetReport
)
from apps.users.models import User

class AssetCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for asset categories.
    """
    class Meta:
        model = AssetCategory
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class AssetListSerializer(serializers.ModelSerializer):
    """
    Serializer for asset list view.
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    assigned_to_id = serializers.IntegerField(source='assigned_to.id', read_only=True, allow_null=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    can_self_assign = serializers.SerializerMethodField()
    
    class Meta:
        model = Asset
        fields = [
            'id', 'asset_id', 'name', 'description', 'asset_type', 'category_name',
            'serial_number', 'model', 'manufacturer', 'status', 'location',
            'assigned_to_username', 'assigned_to_id', 'assigned_date', 'assignment_status',
            'purchase_date', 'warranty_expiry', 'created_at', 'created_by_username',
            'can_self_assign'
        ]
        read_only_fields = ['id', 'asset_id', 'created_at']
    
    def get_can_self_assign(self, obj):
        """Check if current user can self-assign this asset."""
        from apps.assets.domain.services.asset_authority import can_self_assign_asset
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return can_self_assign_asset(request.user, obj)
        return False

class AssetDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for asset detail view.
    """
    category = AssetCategorySerializer(read_only=True)
    assigned_to = serializers.StringRelatedField(read_only=True)
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    is_assigned = serializers.ReadOnlyField()
    is_under_warranty = serializers.ReadOnlyField()
    days_since_purchase = serializers.ReadOnlyField()
    
    class Meta:
        model = Asset
        fields = [
            'id', 'asset_id', 'name', 'description', 'asset_type', 'category',
            'serial_number', 'model', 'manufacturer', 'version', 'status',
            'purchase_date', 'purchase_cost', 'warranty_expiry', 'end_of_life',
            'location', 'assigned_to', 'assigned_date', 'specifications', 'tags',
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'is_assigned', 'is_under_warranty', 'days_since_purchase'
        ]
        read_only_fields = [
            'id', 'asset_id', 'created_at', 'updated_at', 'is_assigned',
            'is_under_warranty', 'days_since_purchase'
        ]

class AssetCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating assets.
    """
    class Meta:
        model = Asset
        fields = [
            'name', 'description', 'asset_type', 'category', 'serial_number',
            'model', 'manufacturer', 'version', 'status', 'purchase_date',
            'purchase_cost', 'warranty_expiry', 'end_of_life', 'location',
            'specifications', 'tags'
        ]
    
    def validate(self, attrs):
        # Ensure serial_number is unique if provided
        serial_number = attrs.get('serial_number')
        if serial_number:
            existing_asset = Asset.objects.filter(serial_number=serial_number).exclude(
                pk=self.instance.pk if self.instance else None
            ).first()
            if existing_asset:
                raise serializers.ValidationError({
                    'serial_number': 'Asset with this serial number already exists.'
                })
        
        return attrs

class AssetUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating assets.
    """
    class Meta:
        model = Asset
        fields = [
            'name', 'description', 'status', 'location', 'specifications', 'tags',
            'end_of_life'
        ]

class HardwareAssetSerializer(serializers.ModelSerializer):
    """
    Serializer for hardware assets.
    """
    asset = AssetDetailSerializer(read_only=True)
    
    class Meta:
        model = HardwareAsset
        fields = [
            'id', 'hardware_type', 'cpu', 'memory', 'storage', 'operating_system',
            'mac_address', 'ip_address', 'asset'
        ]
        read_only_fields = ['id', 'asset']

class HardwareAssetCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating hardware assets.
    """
    class Meta:
        model = HardwareAsset
        fields = [
            'name', 'description', 'category', 'serial_number', 'model',
            'manufacturer', 'version', 'status', 'purchase_date', 'purchase_cost',
            'warranty_expiry', 'end_of_life', 'location', 'specifications', 'tags',
            'hardware_type', 'cpu', 'memory', 'storage', 'operating_system',
            'mac_address', 'ip_address'
        ]
    
    def create(self, validated_data):
        # Create hardware asset
        asset_data = {
            'name': validated_data.pop('name'),
            'description': validated_data.pop('description'),
            'asset_type': 'HARDWARE',
            'category': validated_data.pop('category'),
            'serial_number': validated_data.pop('serial_number', ''),
            'model': validated_data.pop('model', ''),
            'manufacturer': validated_data.pop('manufacturer', ''),
            'version': validated_data.pop('version', ''),
            'status': validated_data.pop('status', 'ACTIVE'),
            'purchase_date': validated_data.pop('purchase_date', None),
            'purchase_cost': validated_data.pop('purchase_cost', None),
            'warranty_expiry': validated_data.pop('warranty_expiry', None),
            'end_of_life': validated_data.pop('end_of_life', None),
            'location': validated_data.pop('location', ''),
            'specifications': validated_data.pop('specifications', {}),
            'tags': validated_data.pop('tags', []),
            'created_by': self.context['request'].user,
        }
        
        asset = Asset.objects.create(**asset_data)
        hardware_asset = HardwareAsset.objects.create(asset=asset, **validated_data)
        return hardware_asset

class SoftwareAssetSerializer(serializers.ModelSerializer):
    """
    Serializer for software assets.
    """
    asset = AssetDetailSerializer(read_only=True)
    seats_available = serializers.ReadOnlyField()
    license_utilization = serializers.ReadOnlyField()
    
    class Meta:
        model = SoftwareAsset
        fields = [
            'id', 'software_type', 'license_type', 'license_key', 'license_seats',
            'seats_used', 'vendor', 'support_end_date', 'download_url',
            'installation_guide', 'asset', 'seats_available', 'license_utilization'
        ]
        read_only_fields = ['id', 'asset', 'seats_available', 'license_utilization']

class SoftwareAssetCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating software assets.
    """
    class Meta:
        model = SoftwareAsset
        fields = [
            'name', 'description', 'category', 'serial_number', 'model',
            'manufacturer', 'version', 'status', 'purchase_date', 'purchase_cost',
            'warranty_expiry', 'end_of_life', 'location', 'specifications', 'tags',
            'software_type', 'license_type', 'license_key', 'license_seats',
            'seats_used', 'vendor', 'support_end_date', 'download_url',
            'installation_guide'
        ]
    
    def create(self, validated_data):
        # Create software asset
        asset_data = {
            'name': validated_data.pop('name'),
            'description': validated_data.pop('description'),
            'asset_type': 'SOFTWARE',
            'category': validated_data.pop('category'),
            'serial_number': validated_data.pop('serial_number', ''),
            'model': validated_data.pop('model', ''),
            'manufacturer': validated_data.pop('manufacturer', ''),
            'version': validated_data.pop('version', ''),
            'status': validated_data.pop('status', 'ACTIVE'),
            'purchase_date': validated_data.pop('purchase_date', None),
            'purchase_cost': validated_data.pop('purchase_cost', None),
            'warranty_expiry': validated_data.pop('warranty_expiry', None),
            'end_of_life': validated_data.pop('end_of_life', None),
            'location': validated_data.pop('location', ''),
            'specifications': validated_data.pop('specifications', {}),
            'tags': validated_data.pop('tags', []),
            'created_by': self.context['request'].user,
        }
        
        asset = Asset.objects.create(**asset_data)
        software_asset = SoftwareAsset.objects.create(asset=asset, **validated_data)
        return software_asset

class AssetAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer for asset assignments.
    """
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)
    
    class Meta:
        model = AssetAssignment
        fields = [
            'id', 'asset', 'asset_name', 'user', 'user_username', 'assignment_type',
            'assigned_by', 'assigned_by_username', 'assigned_date', 'return_date',
            'notes', 'is_active'
        ]
        read_only_fields = ['id', 'assigned_date', 'assigned_by_username']

class AssetAssignmentCreateSerializer(serializers.Serializer):
    """
    Serializer for creating asset assignments.
    """
    asset_id = serializers.UUIDField()
    user_id = serializers.IntegerField()
    assignment_type = serializers.ChoiceField(choices=AssetAssignment.ASSIGNMENT_TYPE_CHOICES)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_asset_id(self, value):
        try:
            asset = Asset.objects.get(asset_id=value)
            return asset
        except Asset.DoesNotExist:
            raise serializers.ValidationError("Asset not found.")
    
    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
    
    def validate(self, attrs):
        asset = attrs['asset_id']
        user = attrs['user_id']
        assignment_type = attrs['assignment_type']
        
        # Check if asset is available for assignment
        if assignment_type == 'ASSIGNMENT':
            if asset.status != 'ACTIVE':
                raise serializers.ValidationError("Asset must be active to be assigned.")
            
            if asset.assigned_to and asset.assigned_to != user:
                raise serializers.ValidationError("Asset is already assigned to another user.")
        
        return attrs

class AssetMaintenanceSerializer(serializers.ModelSerializer):
    """
    Serializer for asset maintenance records.
    """
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = AssetMaintenance
        fields = [
            'id', 'asset', 'asset_name', 'maintenance_type', 'status', 'scheduled_date',
            'completed_date', 'performed_by', 'cost', 'description', 'notes',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_username']

class AssetAuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for asset audit logs.
    """
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AssetAuditLog
        fields = [
            'id', 'asset', 'asset_name', 'user', 'user_username', 'action',
            'description', 'old_values', 'new_values', 'ip_address', 'user_agent',
            'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']

class AssetReportSerializer(serializers.ModelSerializer):
    """
    Serializer for asset reports.
    """
    generated_by_username = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = AssetReport
        fields = [
            'id', 'report_type', 'title', 'description', 'parameters',
            'generated_by', 'generated_by_username', 'generated_at', 'file_path',
            'is_scheduled', 'schedule_frequency'
        ]
        read_only_fields = ['id', 'generated_at', 'generated_by_username']

class AssetStatisticsSerializer(serializers.Serializer):
    """
    Serializer for asset statistics.
    """
    total_assets = serializers.IntegerField()
    hardware_assets = serializers.IntegerField()
    software_assets = serializers.IntegerField()
    assigned_assets = serializers.IntegerField()
    unassigned_assets = serializers.IntegerField()
    assets_by_status = serializers.DictField()
    assets_by_category = serializers.DictField()
    assets_by_type = serializers.DictField()
    assets_under_warranty = serializers.IntegerField()
    recent_assignments = AssetAssignmentSerializer(many=True)
    upcoming_maintenance = AssetMaintenanceSerializer(many=True)

class AssetSearchSerializer(serializers.Serializer):
    """
    Serializer for asset search functionality.
    """
    search = serializers.CharField(required=False)
    asset_type = serializers.ChoiceField(choices=Asset.TYPE_CHOICES, required=False)
    status = serializers.ChoiceField(choices=Asset.STATUS_CHOICES, required=False)
    category = serializers.IntegerField(required=False)
    assigned_to = serializers.IntegerField(required=False)
    location = serializers.CharField(required=False)
    manufacturer = serializers.CharField(required=False)
    warranty_expiring = serializers.BooleanField(required=False)
