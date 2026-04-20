"""
Unit tests for asset authority (permission) functions.

Pure domain logic — no DB required.
Users and assets are mocked via SimpleNamespace.
"""

from types import SimpleNamespace
import pytest

from apps.assets.domain.services.asset_authority import (
    can_create,
    can_view,
    can_edit,
    can_delete,
    can_assign,
    can_view_logs,
    assert_can_edit,
    assert_can_delete,
)
from apps.core.domain.authorization import AuthorizationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def user(role, uid=1):
    return SimpleNamespace(role=role, id=uid, username=f'user_{role.lower()}')


def asset(assigned_to_id=None, created_by_id=1):
    return SimpleNamespace(assigned_to_id=assigned_to_id, created_by_id=created_by_id)


VIEWER = 'VIEWER'
TECHNICIAN = 'TECHNICIAN'
MANAGER = 'MANAGER'
IT_ADMIN = 'IT_ADMIN'
SUPERADMIN = 'SUPERADMIN'

NON_VIEWER_ROLES = [TECHNICIAN, MANAGER, IT_ADMIN, SUPERADMIN]


# ---------------------------------------------------------------------------
# can_create
# ---------------------------------------------------------------------------

class TestCanCreate:
    def test_viewer_denied(self):
        assert can_create(user(VIEWER)) is False

    @pytest.mark.parametrize('role', NON_VIEWER_ROLES)
    def test_non_viewer_allowed(self, role):
        assert can_create(user(role)) is True


# ---------------------------------------------------------------------------
# can_view
# ---------------------------------------------------------------------------

class TestCanView:
    def test_viewer_denied(self):
        assert can_view(user(VIEWER), asset()) is False

    @pytest.mark.parametrize('role', NON_VIEWER_ROLES)
    def test_non_viewer_can_view(self, role):
        assert can_view(user(role), asset()) is True


# ---------------------------------------------------------------------------
# can_edit
# ---------------------------------------------------------------------------

class TestCanEdit:
    def test_viewer_denied(self):
        assert can_edit(user(VIEWER), asset()) is False

    @pytest.mark.parametrize('role', [MANAGER, IT_ADMIN, SUPERADMIN])
    def test_admin_roles_can_edit_any(self, role):
        a = asset(assigned_to_id=99)
        assert can_edit(user(role, uid=1), a) is True

    def test_technician_can_edit_own_asset(self):
        a = asset(assigned_to_id=42)
        assert can_edit(user(TECHNICIAN, uid=42), a) is True

    def test_technician_denied_on_others_asset(self):
        a = asset(assigned_to_id=99)
        assert can_edit(user(TECHNICIAN, uid=42), a) is False

    def test_technician_denied_on_unassigned_asset(self):
        a = asset(assigned_to_id=None)
        assert can_edit(user(TECHNICIAN, uid=42), a) is False


# ---------------------------------------------------------------------------
# can_delete
# ---------------------------------------------------------------------------

class TestCanDelete:
    def test_viewer_denied(self):
        assert can_delete(user(VIEWER), asset()) is False

    @pytest.mark.parametrize('role', [MANAGER, IT_ADMIN, SUPERADMIN])
    def test_admin_roles_can_delete_any(self, role):
        a = asset(assigned_to_id=99)
        assert can_delete(user(role, uid=1), a) is True

    def test_technician_can_delete_own_assigned_asset(self):
        a = asset(assigned_to_id=42)
        assert can_delete(user(TECHNICIAN, uid=42), a) is True

    def test_technician_denied_on_others_asset(self):
        a = asset(assigned_to_id=99)
        assert can_delete(user(TECHNICIAN, uid=42), a) is False


# ---------------------------------------------------------------------------
# can_assign
# ---------------------------------------------------------------------------

class TestCanAssign:
    def test_viewer_denied(self):
        assert can_assign(user(VIEWER), asset(), assignee=None) is False

    def test_technician_cannot_assign(self):
        assert can_assign(user(TECHNICIAN), asset(), assignee=None) is False

    @pytest.mark.parametrize('role', [MANAGER, IT_ADMIN, SUPERADMIN])
    def test_admin_roles_can_assign(self, role):
        assert can_assign(user(role), asset(), assignee=None) is True


# ---------------------------------------------------------------------------
# can_view_logs
# ---------------------------------------------------------------------------

class TestCanViewLogs:
    # ROLE_RANKS in core/domain/roles.py: MANAGER=4, IT_ADMIN=3, TECHNICIAN=2, VIEWER=1
    # has_higher_role(role, IT_ADMIN) is True for rank >= 3: IT_ADMIN, MANAGER, SUPERADMIN
    @pytest.mark.parametrize('role', [VIEWER, TECHNICIAN])
    def test_viewer_and_technician_denied(self, role):
        assert can_view_logs(user(role), asset()) is False

    @pytest.mark.parametrize('role', [IT_ADMIN, MANAGER, SUPERADMIN])
    def test_it_admin_and_above_allowed(self, role):
        assert can_view_logs(user(role), asset()) is True


# ---------------------------------------------------------------------------
# assert helpers
# ---------------------------------------------------------------------------

class TestAssertHelpers:
    def test_assert_can_edit_raises_for_viewer(self):
        with pytest.raises(AuthorizationError):
            assert_can_edit(user(VIEWER), asset())

    def test_assert_can_edit_no_raise_for_manager(self):
        assert_can_edit(user(MANAGER), asset())

    def test_assert_can_delete_raises_for_viewer(self):
        with pytest.raises(AuthorizationError):
            assert_can_delete(user(VIEWER), asset())

    def test_assert_can_delete_no_raise_for_superadmin(self):
        assert_can_delete(user(SUPERADMIN), asset())
