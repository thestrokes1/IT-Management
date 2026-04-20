"""
Unit tests for ticket authority (permission) functions.

These tests exercise pure domain logic — no DB required.
Users and tickets are mocked via SimpleNamespace.
"""

from types import SimpleNamespace
import pytest

from apps.tickets.domain.services.ticket_authority import (
    can_create,
    can_view,
    can_edit,
    can_delete,
    can_assign,
    can_self_assign,
    assert_can_edit,
    assert_can_delete,
)
from apps.core.domain.authorization import AuthorizationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def user(role, uid=1):
    return SimpleNamespace(role=role, id=uid, username=f'user_{role.lower()}')


def ticket(assigned_to_id=None):
    return SimpleNamespace(assigned_to_id=assigned_to_id)


VIEWER = 'VIEWER'
TECHNICIAN = 'TECHNICIAN'
MANAGER = 'MANAGER'
IT_ADMIN = 'IT_ADMIN'
SUPERADMIN = 'SUPERADMIN'

ALL_ROLES = [VIEWER, TECHNICIAN, MANAGER, IT_ADMIN, SUPERADMIN]
CAN_CREATE_ROLES = [TECHNICIAN, MANAGER, IT_ADMIN, SUPERADMIN]


# ---------------------------------------------------------------------------
# can_create
# ---------------------------------------------------------------------------

class TestCanCreate:
    def test_viewer_denied(self):
        assert can_create(user(VIEWER)) is False

    @pytest.mark.parametrize('role', CAN_CREATE_ROLES)
    def test_non_viewer_allowed(self, role):
        assert can_create(user(role)) is True


# ---------------------------------------------------------------------------
# can_view
# ---------------------------------------------------------------------------

class TestCanView:
    def test_viewer_denied(self):
        t = ticket()
        assert can_view(user(VIEWER), t) is False

    @pytest.mark.parametrize('role', CAN_CREATE_ROLES)
    def test_non_viewer_allowed(self, role):
        t = ticket()
        assert can_view(user(role), t) is True


# ---------------------------------------------------------------------------
# can_edit
# ---------------------------------------------------------------------------

class TestCanEdit:
    def test_viewer_denied(self):
        assert can_edit(user(VIEWER), ticket()) is False

    @pytest.mark.parametrize('role', [MANAGER, IT_ADMIN, SUPERADMIN])
    def test_admin_roles_can_edit_any(self, role):
        t = ticket(assigned_to_id=99)  # assigned to someone else
        assert can_edit(user(role, uid=1), t) is True

    def test_technician_can_edit_own_ticket(self):
        t = ticket(assigned_to_id=42)
        assert can_edit(user(TECHNICIAN, uid=42), t) is True

    def test_technician_denied_on_others_ticket(self):
        t = ticket(assigned_to_id=99)
        assert can_edit(user(TECHNICIAN, uid=42), t) is False

    def test_technician_denied_on_unassigned_ticket(self):
        t = ticket(assigned_to_id=None)
        assert can_edit(user(TECHNICIAN, uid=42), t) is False


# ---------------------------------------------------------------------------
# can_delete
# ---------------------------------------------------------------------------

class TestCanDelete:
    def test_viewer_denied(self):
        assert can_delete(user(VIEWER), ticket()) is False

    @pytest.mark.parametrize('role', [MANAGER, IT_ADMIN, SUPERADMIN])
    def test_admin_roles_can_delete_any(self, role):
        t = ticket(assigned_to_id=99)
        assert can_delete(user(role, uid=1), t) is True

    def test_technician_can_delete_own_ticket(self):
        t = ticket(assigned_to_id=42)
        assert can_delete(user(TECHNICIAN, uid=42), t) is True

    def test_technician_denied_on_others_ticket(self):
        t = ticket(assigned_to_id=99)
        assert can_delete(user(TECHNICIAN, uid=42), t) is False


# ---------------------------------------------------------------------------
# can_assign
# ---------------------------------------------------------------------------

class TestCanAssign:
    def test_viewer_denied(self):
        t = ticket()
        assert can_assign(user(VIEWER), t, assignee=None) is False

    def test_technician_cannot_assign_to_others(self):
        t = ticket()
        assert can_assign(user(TECHNICIAN), t, assignee=None) is False

    @pytest.mark.parametrize('role', [MANAGER, IT_ADMIN, SUPERADMIN])
    def test_admin_roles_can_assign(self, role):
        t = ticket()
        assert can_assign(user(role), t, assignee=None) is True


# ---------------------------------------------------------------------------
# can_self_assign
# ---------------------------------------------------------------------------

class TestCanSelfAssign:
    def test_viewer_denied(self):
        t = ticket(assigned_to_id=None)
        assert can_self_assign(user(VIEWER), t) is False

    def test_technician_can_self_assign_unassigned(self):
        t = ticket(assigned_to_id=None)
        assert can_self_assign(user(TECHNICIAN, uid=42), t) is True

    def test_technician_cannot_self_assign_already_assigned(self):
        t = ticket(assigned_to_id=99)
        assert can_self_assign(user(TECHNICIAN, uid=42), t) is False

    @pytest.mark.parametrize('role', [MANAGER, IT_ADMIN, SUPERADMIN])
    def test_admin_can_self_assign_unassigned(self, role):
        t = ticket(assigned_to_id=None)
        assert can_self_assign(user(role, uid=1), t) is True


# ---------------------------------------------------------------------------
# assert_can_edit (raises AuthorizationError on failure)
# ---------------------------------------------------------------------------

class TestAssertCanEdit:
    def test_raises_for_viewer(self):
        with pytest.raises(AuthorizationError):
            assert_can_edit(user(VIEWER), ticket())

    def test_raises_for_unassigned_technician(self):
        t = ticket(assigned_to_id=99)
        with pytest.raises(AuthorizationError):
            assert_can_edit(user(TECHNICIAN, uid=42), t)

    def test_no_raise_for_manager(self):
        assert_can_edit(user(MANAGER), ticket())  # must not raise


# ---------------------------------------------------------------------------
# assert_can_delete (raises AuthorizationError on failure)
# ---------------------------------------------------------------------------

class TestAssertCanDelete:
    def test_raises_for_viewer(self):
        with pytest.raises(AuthorizationError):
            assert_can_delete(user(VIEWER), ticket())

    def test_no_raise_for_superadmin(self):
        assert_can_delete(user(SUPERADMIN), ticket())  # must not raise
