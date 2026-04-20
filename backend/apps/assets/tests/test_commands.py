"""
Integration tests for asset CQRS commands.

Hits real DB (SQLite). transaction.on_commit() callbacks don't fire
in non-transactional test mode so activity logging is not exercised here.
"""

import pytest

from apps.assets.application.create_asset import CreateAsset
from apps.assets.application.update_asset import UpdateAsset
from apps.core.domain.authorization import AuthorizationError


# ---------------------------------------------------------------------------
# CreateAsset
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCreateAsset:
    def test_viewer_cannot_create(self, viewer, asset_category):
        result = CreateAsset().execute(user=viewer, name='Laptop', category_id=asset_category.id)
        assert result.success is False
        assert 'authorized' in result.error.lower()

    def test_technician_can_create(self, technician, asset_category):
        result = CreateAsset().execute(user=technician, name='Laptop XPS', category_id=asset_category.id)
        assert result.success is True
        assert result.data['name'] == 'Laptop XPS'

    def test_manager_can_create(self, manager, asset_category):
        result = CreateAsset().execute(user=manager, name='Server Rack', category_id=asset_category.id)
        assert result.success is True

    def test_superadmin_can_create(self, superadmin, asset_category):
        result = CreateAsset().execute(user=superadmin, name='Switch', category_id=asset_category.id)
        assert result.success is True

    def test_name_is_required(self, manager, asset_category):
        result = CreateAsset().execute(user=manager, name='', category_id=asset_category.id)
        assert result.success is False
        assert 'required' in result.error.lower()

    def test_name_is_trimmed(self, technician, asset_category):
        result = CreateAsset().execute(user=technician, name='  Router  ', category_id=asset_category.id)
        assert result.success is True
        assert result.data['name'] == 'Router'

    def test_category_name_in_result(self, manager, asset_category):
        result = CreateAsset().execute(
            user=manager,
            name='Desktop PC',
            category_id=asset_category.id,
        )
        assert result.success is True
        assert result.data['category'] == 'Hardware'

    def test_invalid_category_returns_failure(self, manager):
        result = CreateAsset().execute(
            user=manager,
            name='Desktop PC',
            category_id=99999,
        )
        assert result.success is False

    def test_returns_asset_id(self, technician, asset_category):
        result = CreateAsset().execute(user=technician, name='Monitor', category_id=asset_category.id)
        assert 'asset_id' in result.data
        assert len(result.data['asset_id']) == 36  # UUID string


# ---------------------------------------------------------------------------
# UpdateAsset — basic authorization checks
# ---------------------------------------------------------------------------

@pytest.fixture
def active_asset(db, manager, asset_category):
    from apps.assets.models import Asset
    return Asset.objects.create(
        name='Test Asset',
        asset_type='HARDWARE',
        status='ACTIVE',
        category=asset_category,
        created_by=manager,
    )


@pytest.fixture
def assigned_asset(db, manager, technician, asset_category):
    from apps.assets.models import Asset
    return Asset.objects.create(
        name='Assigned Asset',
        asset_type='HARDWARE',
        status='ACTIVE',
        category=asset_category,
        created_by=manager,
        assigned_to=technician,
        assignment_status='ASSIGNED',
    )


@pytest.mark.django_db
class TestUpdateAsset:
    def test_manager_can_update(self, manager, active_asset):
        result = UpdateAsset().execute(
            user=manager,
            asset_id=str(active_asset.asset_id),
            asset_data={'status': 'INACTIVE'},
        )
        assert result.success is True

    def test_viewer_cannot_update(self, viewer, active_asset):
        result = UpdateAsset().execute(
            user=viewer,
            asset_id=str(active_asset.asset_id),
            asset_data={'status': 'INACTIVE'},
        )
        assert result.success is False

    def test_technician_can_update_assigned_asset(self, technician, assigned_asset):
        result = UpdateAsset().execute(
            user=technician,
            asset_id=str(assigned_asset.asset_id),
            asset_data={'location': 'Office A'},
        )
        assert result.success is True

    def test_technician_denied_on_unassigned_asset(self, technician, active_asset):
        result = UpdateAsset().execute(
            user=technician,
            asset_id=str(active_asset.asset_id),
            asset_data={'location': 'Office A'},
        )
        assert result.success is False

    def test_nonexistent_asset_returns_failure(self, manager):
        result = UpdateAsset().execute(
            user=manager,
            asset_id='00000000-0000-0000-0000-000000000000',
            asset_data={'status': 'INACTIVE'},
        )
        assert result.success is False
