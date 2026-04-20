"""
Unit tests for project authority (permission) functions.

Pure domain logic — no DB required except where noted.
Users and projects are mocked via SimpleNamespace.

Key project rule: Only MANAGER and SUPERADMIN can create/edit projects.
IT_ADMIN is explicitly excluded from project management (read-only at best).
Only SUPERADMIN can delete projects.
"""

from types import SimpleNamespace
import pytest

from apps.projects.domain.services.project_authority import (
    can_create,
    can_view_list,
    can_edit,
    can_delete,
    can_assign,
    can_manage_members,
    assert_can_create,
    assert_can_edit,
    assert_can_delete,
)
from apps.core.domain.authorization import AuthorizationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def user(role, uid=1):
    return SimpleNamespace(role=role, id=uid, username=f'user_{role.lower()}')


def project(manager_id=1):
    return SimpleNamespace(manager_id=manager_id, id=1)


VIEWER = 'VIEWER'
TECHNICIAN = 'TECHNICIAN'
MANAGER = 'MANAGER'
IT_ADMIN = 'IT_ADMIN'
SUPERADMIN = 'SUPERADMIN'


# ---------------------------------------------------------------------------
# can_create — only MANAGER and SUPERADMIN (rank >= 4)
# ---------------------------------------------------------------------------

class TestCanCreate:
    @pytest.mark.parametrize('role', [VIEWER, TECHNICIAN, IT_ADMIN])
    def test_below_manager_denied(self, role):
        assert can_create(user(role)) is False

    @pytest.mark.parametrize('role', [MANAGER, SUPERADMIN])
    def test_manager_and_superadmin_allowed(self, role):
        assert can_create(user(role)) is True


# ---------------------------------------------------------------------------
# can_view_list — all non-VIEWER roles
# ---------------------------------------------------------------------------

class TestCanViewList:
    def test_viewer_denied(self):
        assert can_view_list(user(VIEWER)) is False

    @pytest.mark.parametrize('role', [TECHNICIAN, MANAGER, IT_ADMIN, SUPERADMIN])
    def test_non_viewer_allowed(self, role):
        assert can_view_list(user(role)) is True


# ---------------------------------------------------------------------------
# can_edit — only MANAGER and SUPERADMIN; IT_ADMIN explicitly excluded
# ---------------------------------------------------------------------------

class TestCanEdit:
    @pytest.mark.parametrize('role', [VIEWER, TECHNICIAN, IT_ADMIN])
    def test_non_manager_denied(self, role):
        p = project()
        assert can_edit(user(role), p) is False

    @pytest.mark.parametrize('role', [MANAGER, SUPERADMIN])
    def test_manager_and_superadmin_allowed(self, role):
        p = project()
        assert can_edit(user(role), p) is True

    def test_it_admin_explicitly_excluded(self):
        # IT_ADMIN has rank 3 which is admin-level, but project management is MANAGER+ only
        p = project()
        assert can_edit(user(IT_ADMIN), p) is False


# ---------------------------------------------------------------------------
# can_delete — only SUPERADMIN
# ---------------------------------------------------------------------------

class TestCanDelete:
    @pytest.mark.parametrize('role', [VIEWER, TECHNICIAN, IT_ADMIN, MANAGER])
    def test_non_superadmin_denied(self, role):
        p = project()
        assert can_delete(user(role), p) is False

    def test_superadmin_allowed(self):
        p = project()
        assert can_delete(user(SUPERADMIN), p) is True


# ---------------------------------------------------------------------------
# can_assign / can_manage_members — MANAGER and SUPERADMIN only
# ---------------------------------------------------------------------------

class TestCanAssign:
    @pytest.mark.parametrize('role', [VIEWER, TECHNICIAN, IT_ADMIN])
    def test_non_manager_denied(self, role):
        p = project()
        assert can_assign(user(role), p, assignee=None) is False

    @pytest.mark.parametrize('role', [MANAGER, SUPERADMIN])
    def test_manager_and_superadmin_allowed(self, role):
        p = project()
        assert can_assign(user(role), p, assignee=None) is True


class TestCanManageMembers:
    @pytest.mark.parametrize('role', [VIEWER, TECHNICIAN, IT_ADMIN])
    def test_non_manager_denied(self, role):
        p = project()
        assert can_manage_members(user(role), p) is False

    @pytest.mark.parametrize('role', [MANAGER, SUPERADMIN])
    def test_manager_and_superadmin_allowed(self, role):
        p = project()
        assert can_manage_members(user(role), p) is True


# ---------------------------------------------------------------------------
# assert helpers — raise AuthorizationError on failure
# ---------------------------------------------------------------------------

class TestAssertHelpers:
    def test_assert_can_create_raises_for_viewer(self):
        with pytest.raises(AuthorizationError):
            assert_can_create(user(VIEWER))

    def test_assert_can_create_raises_for_it_admin(self):
        with pytest.raises(AuthorizationError):
            assert_can_create(user(IT_ADMIN))

    def test_assert_can_create_no_raise_for_manager(self):
        assert_can_create(user(MANAGER))

    def test_assert_can_edit_raises_for_it_admin(self):
        with pytest.raises(AuthorizationError):
            assert_can_edit(user(IT_ADMIN), project())

    def test_assert_can_edit_no_raise_for_superadmin(self):
        assert_can_edit(user(SUPERADMIN), project())

    def test_assert_can_delete_raises_for_manager(self):
        with pytest.raises(AuthorizationError):
            assert_can_delete(user(MANAGER), project())

    def test_assert_can_delete_no_raise_for_superadmin(self):
        assert_can_delete(user(SUPERADMIN), project())
