"""
Use case for creating an asset.

Authorization is enforced via domain service with strict RBAC.
Activity logging is handled via transaction.on_commit to ensure logging
never breaks the business operation.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from django.db import transaction

from apps.assets.domain.services.asset_authority import (
    can_create_asset,
    assert_can_create_asset,
)
from apps.core.domain.authorization import AuthorizationError


@dataclass
class CreateAssetResult:
    """Result of asset creation use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Dict) -> 'CreateAssetResult':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'CreateAssetResult':
        return cls(success=False, error=error)


class CreateAsset:
    """
    Use case for creating an asset.
    
    Business Rules:
    - Only users with can_create permission can create assets
    - SUPERADMIN, MANAGER, IT_ADMIN can create any asset
    - TECHNICIAN can create assets
    - Name is required
    - Category must exist
    
    Input (via execute):
        user: User - User performing the creation
        name: str - Asset name
        description: str - Asset description
        category_id: int - Category ID
        serial_number: str - Optional serial number
        status: str - Asset status
        location: str - Asset location
        purchase_date: str - Optional purchase date
        purchase_price: str - Optional purchase price
        warranty_expiry: str - Optional warranty expiry
        assigned_to_id: int - Optional assigned user ID
        
    Output:
        CreateAssetResult with creation confirmation or error
        
    Usage:
        result = CreateAsset().execute(
            user=request.user,
            name="Laptop Dell XPS 15",
            description="Developer laptop",
            category_id=1,
            serial_number="Dell123456"
        )
        
        if result.success:
            print(f"Created asset: {result.data['name']}")
        else:
            print(f"Error: {result.error}")
    """

    @transaction.atomic
    def execute(
        self,
        user: Any,
        name: str,
        description: str = '',
        category_id: Optional[int] = None,
        serial_number: str = '',
        status: str = 'ACTIVE',
        location: str = '',
        purchase_date: str = '',
        purchase_price: str = '',
        warranty_expiry: str = '',
        assigned_to_id: Optional[int] = None,
    ) -> CreateAssetResult:
        """
        Execute asset creation use case.

        Args:
            user: User performing the creation
            name: Asset name
            description: Asset description
            category_id: Category ID
            serial_number: Optional serial number
            status: Asset status
            location: Asset location
            purchase_date: Optional purchase date (YYYY-MM-DD)
            purchase_price: Optional purchase price
            warranty_expiry: Optional warranty expiry (YYYY-MM-DD)
            assigned_to_id: Optional assigned user ID

        Returns:
            CreateAssetResult with creation confirmation or error
        """
        from apps.assets.models import Asset, AssetCategory
        from apps.users.models import User
        from datetime import datetime
        
        # Authorization check - raises AuthorizationError if not authorized
        try:
            assert_can_create_asset(user)
        except AuthorizationError as e:
            return CreateAssetResult.fail(str(e))

        # Validate required fields
        if not name or not name.strip():
            return CreateAssetResult.fail("Asset name is required")

        # Get category
        category = None
        if category_id:
            try:
                category = AssetCategory.objects.get(id=category_id)
            except AssetCategory.DoesNotExist:
                return CreateAssetResult.fail(f"Category with ID {category_id} not found")

        # Determine asset type (default to HARDWARE)
        asset_type = 'HARDWARE'

        # Parse dates
        purchase_date_obj = None
        if purchase_date:
            try:
                purchase_date_obj = datetime.strptime(purchase_date, '%Y-%m-%d').date()
            except ValueError:
                pass

        warranty_expiry_obj = None
        if warranty_expiry:
            try:
                warranty_expiry_obj = datetime.strptime(warranty_expiry, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Parse purchase price
        purchase_cost = None
        if purchase_price:
            try:
                purchase_cost = float(purchase_price)
            except (ValueError, TypeError):
                pass

        # Get assigned user
        assigned_to = None
        if assigned_to_id:
            try:
                assigned_to = User.objects.get(id=assigned_to_id)
            except User.DoesNotExist:
                pass

        # Create asset
        asset = Asset.objects.create(
            name=name.strip(),
            description=description.strip(),
            asset_type=asset_type,
            category=category,
            serial_number=serial_number.strip() if serial_number else '',
            status=status,
            location=location.strip(),
            purchase_date=purchase_date_obj,
            purchase_cost=purchase_cost,
            warranty_expiry=warranty_expiry_obj,
            assigned_to=assigned_to,
            created_by=user
        )

        # Activity logging - runs after transaction commits, never breaks command
        transaction.on_commit(lambda: self._log_asset_created(asset, user))

        return CreateAssetResult.ok(
            data={
                'asset_id': str(asset.asset_id),
                'name': asset.name,
                'description': asset.description,
                'category': asset.category.name if asset.category else None,
                'serial_number': asset.serial_number,
                'status': asset.status,
                'location': asset.location,
                'assigned_to': assigned_to.username if assigned_to else None,
                'message': f"Asset '{asset.name}' created successfully",
            }
        )

    def _log_asset_created(self, asset, user):
        """Log asset creation activity."""
        try:
            from apps.logs.services.activity_service import ActivityService
            ActivityService().log_asset_created(asset, user, None)
        except Exception:
            pass  # Logging must never break the command
