# Asset query class for read-only database operations.
# This class follows CQRS principles - only reads data, never mutates state.

from django.db.models import QuerySet
from typing import List, Dict, Any, Optional
from django.db.models import Q
from apps.assets.models import Asset

class AssetQuery:
    """
    Query class for Asset model.
    All methods are read-only - they NEVER mutate state.
    Returns querysets/dictionaries, never HttpResponse.
    """
    
    @staticmethod
    def get_all() -> QuerySet:
        """
        Get all assets with related data.
        Returns: QuerySet of Asset objects
        """
        from apps.assets.models import Asset
        return Asset.objects.select_related(
            'assigned_to', 'category', 'created_by'
        ).order_by('-created_at')[:50]
    
    @staticmethod
    def get_by_id(asset_id: int) -> Optional['Asset']:
        """
        Get a single asset by ID.
        Args:
            asset_id: The ID of the asset to retrieve
        Returns: Asset object or None
        """
        from apps.assets.models import Asset
        from django.shortcuts import get_object_or_404
        try:
            return get_object_or_404(
                Asset.objects.select_related('created_by'),
                id=asset_id
            )
        except (Asset.DoesNotExist, ValueError):
            return None
    
    @staticmethod
    def get_with_details(asset_id: int) -> Optional['Asset']:
        """
        Get an asset with all details (category, assigned_to, created_by).
        Args:
            asset_id: The ID of the asset to retrieve
        Returns: Asset object with prefetched relations or None
        """
        from apps.assets.models import Asset
        from django.shortcuts import get_object_or_404
        try:
            return get_object_or_404(
                Asset.objects.select_related('category', 'assigned_to', 'created_by'),
                id=asset_id
            )
        except (Asset.DoesNotExist, ValueError):
            return None
    
    @staticmethod
    def get_categories() -> QuerySet:
        """
        Get all active asset categories.
        Returns: QuerySet of AssetCategory objects
        """
        from apps.assets.models import AssetCategory
        return AssetCategory.objects.filter(is_active=True)
    
    @staticmethod
    def get_status_choices() -> List[tuple]:
        """
        Get asset status choices.
        Returns: List of (value, display_name) tuples
        """
        from apps.assets.models import Asset
        return Asset.STATUS_CHOICES
    
    @staticmethod
    def get_active_users() -> QuerySet:
        """
        Get all active users (for assignment selection).
        Returns: QuerySet of User objects
        """
        from apps.users.models import User
        return User.objects.filter(is_active=True)
    
    @staticmethod
    def get_for_dashboard() -> Dict[str, Any]:
        """
        Get asset statistics for dashboard.
        Returns: Dictionary with asset counts by status
        """
        from apps.assets.models import Asset
        return {
            'total': Asset.objects.count(),
            'active': Asset.objects.filter(status='ACTIVE').count(),
            'assigned': Asset.objects.filter(status='ASSIGNED').count(),
            'maintenance': Asset.objects.filter(status='MAINTENANCE').count(),
            'retired': Asset.objects.filter(status='RETIRED').count(),
        }
    
    @staticmethod
    def get_active() -> QuerySet:
        """
        Get all active (non-retired) assets.
        Returns: QuerySet of Asset objects
        """
        from apps.assets.models import Asset
        return Asset.objects.filter(status='ACTIVE').select_related(
            'category', 'assigned_to'
        ).order_by('name')

    @staticmethod
    def get_unassigned_or_assigned_to(user):
        """
        Assets visible to a technician:
        - unassigned assets
        - assets assigned to that technician
        """
        return Asset.objects.filter(
            Q(assigned_to__isnull=True) |
            Q(assigned_to=user)
        )