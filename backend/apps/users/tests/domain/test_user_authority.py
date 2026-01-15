"""
Tests for user authority domain service.
"""

import unittest
import sys

sys.path.insert(0, '.')

from apps.users.domain.services.user_authority import (
    can_view_user,
    can_update_user,
    can_change_role,
    can_deactivate_user,
    can_delete_user,
    get_user_permissions,
    assert_can_update_user,
    assert_can_change_role,
    assert_can_deactivate_user,
    assert_can_delete_user,
)
from apps.core.domain.authorization import AuthorizationError


class FakeUser:
    """Fake user for testing without Django dependencies."""
    
    def __init__(self, username, role):
        self.username = username
        self.role = role
    
    def __eq__(self, other):
        return isinstance(other, FakeUser) and self.username == other.username
    
    def __hash__(self):
        return hash(self.username)
    
    def __repr__(self):
        return f"FakeUser({self.username!r}, {self.role!r})"


class TestCanViewUser(unittest.TestCase):
    """Tests for can_view_user function."""
    
    def setUp(self):
        # Create test users
        self.superadmin = FakeUser('superadmin', 'SUPERADMIN')
        self.manager = FakeUser('manager', 'MANAGER')
        self.it_admin = FakeUser('it_admin', 'IT_ADMIN')
        self.technician = FakeUser('technician', 'TECHNICIAN')
        self.viewer = FakeUser('viewer', 'VIEWER')
    
    def test_user_can_view_own_profile(self):
        """Users can always view their own profile."""
        self.assertTrue(can_view_user(self.superadmin, self.superadmin))
        self.assertTrue(can_view_user(self.manager, self.manager))
        self.assertTrue(can_view_user(self.it_admin, self.it_admin))
        self.assertTrue(can_view_user(self.technician, self.technician))
        self.assertTrue(can_view_user(self.viewer, self.viewer))
    
    def test_superadmin_can_view_any_user(self):
        """SUPERADMIN can view any user profile."""
        self.assertTrue(can_view_user(self.superadmin, self.manager))
        self.assertTrue(can_view_user(self.superadmin, self.it_admin))
        self.assertTrue(can_view_user(self.superadmin, self.technician))
        self.assertTrue(can_view_user(self.superadmin, self.viewer))
    
    def test_manager_can_view_any_user(self):
        """MANAGER can view any user profile."""
        self.assertTrue(can_view_user(self.manager, self.superadmin))
        self.assertTrue(can_view_user(self.manager, self.it_admin))
        self.assertTrue(can_view_user(self.manager, self.technician))
        self.assertTrue(can_view_user(self.manager, self.viewer))
    
    def test_it_admin_can_view_any_user(self):
        """IT_ADMIN can view any user profile (read access is permissive)."""
        self.assertTrue(can_view_user(self.it_admin, self.superadmin))
        self.assertTrue(can_view_user(self.it_admin, self.manager))
        self.assertTrue(can_view_user(self.it_admin, self.technician))
        self.assertTrue(can_view_user(self.it_admin, self.viewer))
    
    def test_technician_can_view_any_user(self):
        """TECHNICIAN can view any user profile (read access is permissive)."""
        self.assertTrue(can_view_user(self.technician, self.superadmin))
        self.assertTrue(can_view_user(self.technician, self.manager))
        self.assertTrue(can_view_user(self.technician, self.it_admin))
        self.assertTrue(can_view_user(self.technician, self.viewer))
    
    def test_viewer_can_view_any_user(self):
        """VIEWER can view any user profile (read access is permissive)."""
        self.assertTrue(can_view_user(self.viewer, self.superadmin))
        self.assertTrue(can_view_user(self.viewer, self.manager))
        self.assertTrue(can_view_user(self.viewer, self.it_admin))
        self.assertTrue(can_view_user(self.viewer, self.technician))


class TestCanUpdateUser(unittest.TestCase):
    """Tests for can_update_user function."""
    
    def setUp(self):
        self.superadmin = FakeUser('superadmin', 'SUPERADMIN')
        self.manager = FakeUser('manager', 'MANAGER')
        self.it_admin = FakeUser('it_admin', 'IT_ADMIN')
        self.technician = FakeUser('technician', 'TECHNICIAN')
        self.technician2 = FakeUser('technician2', 'TECHNICIAN')
        self.viewer = FakeUser('viewer', 'VIEWER')
    
    def test_user_can_update_own_profile(self):
        """Users can always update their own profile."""
        self.assertTrue(can_update_user(self.superadmin, self.superadmin))
        self.assertTrue(can_update_user(self.manager, self.manager))
        self.assertTrue(can_update_user(self.it_admin, self.it_admin))
        self.assertTrue(can_update_user(self.technician, self.technician))
        self.assertTrue(can_update_user(self.viewer, self.viewer))
    
    def test_superadmin_can_update_any_user(self):
        """SUPERADMIN can update any user profile."""
        self.assertTrue(can_update_user(self.superadmin, self.manager))
        self.assertTrue(can_update_user(self.superadmin, self.it_admin))
        self.assertTrue(can_update_user(self.superadmin, self.technician))
        self.assertTrue(can_update_user(self.superadmin, self.viewer))
    
    def test_manager_can_update_except_superadmin(self):
        """MANAGER can update any user except SUPERADMIN."""
        self.assertFalse(can_update_user(self.manager, self.superadmin))
        self.assertTrue(can_update_user(self.manager, self.it_admin))
        self.assertTrue(can_update_user(self.manager, self.technician))
        self.assertTrue(can_update_user(self.manager, self.viewer))
    
    def test_it_admin_can_update_technician_or_viewer(self):
        """IT_ADMIN can update TECHNICIAN or VIEWER only."""
        self.assertFalse(can_update_user(self.it_admin, self.superadmin))
        self.assertFalse(can_update_user(self.it_admin, self.manager))
        self.assertFalse(can_update_user(self.it_admin, self.it_admin))
        self.assertTrue(can_update_user(self.it_admin, self.technician))
        self.assertTrue(can_update_user(self.it_admin, self.viewer))
    
    def test_technician_can_only_update_self(self):
        """TECHNICIAN can only update their own profile."""
        self.assertFalse(can_update_user(self.technician, self.superadmin))
        self.assertFalse(can_update_user(self.technician, self.manager))
        self.assertFalse(can_update_user(self.technician, self.it_admin))
        self.assertFalse(can_update_user(self.technician, self.technician2))
        self.assertTrue(can_update_user(self.technician, self.technician))
        self.assertFalse(can_update_user(self.technician, self.viewer))
    
    def test_viewer_can_only_update_self(self):
        """VIEWER can only update their own profile."""
        self.assertFalse(can_update_user(self.viewer, self.superadmin))
        self.assertFalse(can_update_user(self.viewer, self.manager))
        self.assertFalse(can_update_user(self.viewer, self.it_admin))
        self.assertFalse(can_update_user(self.viewer, self.technician))
        self.assertTrue(can_update_user(self.viewer, self.viewer))


class TestCanChangeRole(unittest.TestCase):
    """Tests for can_change_role function."""
    
    def setUp(self):
        self.superadmin = FakeUser('superadmin', 'SUPERADMIN')
        self.manager = FakeUser('manager', 'MANAGER')
        self.it_admin = FakeUser('it_admin', 'IT_ADMIN')
        self.technician = FakeUser('technician', 'TECHNICIAN')
        self.viewer = FakeUser('viewer', 'VIEWER')
    
    def test_cannot_change_own_role(self):
        """Users cannot change their own role."""
        self.assertFalse(can_change_role(self.superadmin, self.superadmin, 'MANAGER'))
        self.assertFalse(can_change_role(self.manager, self.manager, 'IT_ADMIN'))
        self.assertFalse(can_change_role(self.it_admin, self.it_admin, 'TECHNICIAN'))
        self.assertFalse(can_change_role(self.technician, self.technician, 'VIEWER'))
    
    def test_cannot_assign_role_equal_or_higher(self):
        """Cannot assign a role >= actor's role (prevents privilege escalation)."""
        # Manager trying to assign MANAGER role
        self.assertFalse(can_change_role(self.manager, self.it_admin, 'MANAGER'))
        self.assertFalse(can_change_role(self.manager, self.technician, 'MANAGER'))
        # Manager trying to assign SUPERADMIN role
        self.assertFalse(can_change_role(self.manager, self.it_admin, 'SUPERADMIN'))
        # IT_ADMIN trying to assign IT_ADMIN role
        self.assertFalse(can_change_role(self.it_admin, self.technician, 'IT_ADMIN'))
    
    def test_superadmin_can_assign_any_role(self):
        """SUPERADMIN can assign any role."""
        self.assertTrue(can_change_role(self.superadmin, self.manager, 'VIEWER'))
        self.assertTrue(can_change_role(self.superadmin, self.it_admin, 'MANAGER'))
        self.assertTrue(can_change_role(self.superadmin, self.technician, 'IT_ADMIN'))
        self.assertTrue(can_change_role(self.superadmin, self.viewer, 'TECHNICIAN'))
    
    def test_manager_can_assign_it_admin_technician_or_viewer(self):
        """MANAGER can assign IT_ADMIN, TECHNICIAN, or VIEWER."""
        self.assertTrue(can_change_role(self.manager, self.it_admin, 'IT_ADMIN'))
        self.assertTrue(can_change_role(self.manager, self.technician, 'TECHNICIAN'))
        self.assertTrue(can_change_role(self.manager, self.viewer, 'VIEWER'))
        # But not MANAGER or SUPERADMIN
        self.assertFalse(can_change_role(self.manager, self.it_admin, 'MANAGER'))
        self.assertFalse(can_change_role(self.manager, self.technician, 'SUPERADMIN'))
    
    def test_it_admin_can_assign_technician_or_viewer_only(self):
        """IT_ADMIN can assign TECHNICIAN or VIEWER only."""
        self.assertTrue(can_change_role(self.it_admin, self.technician, 'TECHNICIAN'))
        self.assertTrue(can_change_role(self.it_admin, self.viewer, 'VIEWER'))
        # But not IT_ADMIN or higher
        self.assertFalse(can_change_role(self.it_admin, self.technician, 'IT_ADMIN'))
        self.assertFalse(can_change_role(self.it_admin, self.viewer, 'MANAGER'))
        self.assertFalse(can_change_role(self.it_admin, self.viewer, 'SUPERADMIN'))
    
    def test_technician_cannot_change_any_role(self):
        """TECHNICIAN cannot change any role."""
        self.assertFalse(can_change_role(self.technician, self.viewer, 'TECHNICIAN'))
        self.assertFalse(can_change_role(self.technician, self.viewer, 'VIEWER'))
    
    def test_viewer_cannot_change_any_role(self):
        """VIEWER cannot change any role."""
        self.assertFalse(can_change_role(self.viewer, self.technician, 'VIEWER'))


class TestCanDeactivateUser(unittest.TestCase):
    """Tests for can_deactivate_user function."""
    
    def setUp(self):
        self.superadmin = FakeUser('superadmin', 'SUPERADMIN')
        self.manager = FakeUser('manager', 'MANAGER')
        self.it_admin = FakeUser('it_admin', 'IT_ADMIN')
        self.technician = FakeUser('technician', 'TECHNICIAN')
        self.viewer = FakeUser('viewer', 'VIEWER')
    
    def test_cannot_deactivate_self(self):
        """Users cannot deactivate their own account."""
        self.assertFalse(can_deactivate_user(self.superadmin, self.superadmin))
        self.assertFalse(can_deactivate_user(self.manager, self.manager))
        self.assertFalse(can_deactivate_user(self.it_admin, self.it_admin))
        self.assertFalse(can_deactivate_user(self.technician, self.technician))
        self.assertFalse(can_deactivate_user(self.viewer, self.viewer))
    
    def test_superadmin_can_deactivate_any_user_except_self(self):
        """SUPERADMIN can deactivate any user except self."""
        self.assertTrue(can_deactivate_user(self.superadmin, self.manager))
        self.assertTrue(can_deactivate_user(self.superadmin, self.it_admin))
        self.assertTrue(can_deactivate_user(self.superadmin, self.technician))
        self.assertTrue(can_deactivate_user(self.superadmin, self.viewer))
    
    def test_manager_can_deactivate_it_admin_and_below(self):
        """MANAGER can deactivate IT_ADMIN and below."""
        self.assertFalse(can_deactivate_user(self.manager, self.superadmin))
        self.assertTrue(can_deactivate_user(self.manager, self.it_admin))
        self.assertTrue(can_deactivate_user(self.manager, self.technician))
        self.assertTrue(can_deactivate_user(self.manager, self.viewer))
    
    def test_it_admin_can_deactivate_technician_or_viewer_only(self):
        """IT_ADMIN can deactivate TECHNICIAN or VIEWER only."""
        self.assertFalse(can_deactivate_user(self.it_admin, self.superadmin))
        self.assertFalse(can_deactivate_user(self.it_admin, self.manager))
        self.assertFalse(can_deactivate_user(self.it_admin, self.it_admin))
        self.assertTrue(can_deactivate_user(self.it_admin, self.technician))
        self.assertTrue(can_deactivate_user(self.it_admin, self.viewer))
    
    def test_technician_cannot_deactivate_any_user(self):
        """TECHNICIAN cannot deactivate any user."""
        self.assertFalse(can_deactivate_user(self.technician, self.superadmin))
        self.assertFalse(can_deactivate_user(self.technician, self.manager))
        self.assertFalse(can_deactivate_user(self.technician, self.it_admin))
        self.assertFalse(can_deactivate_user(self.technician, self.technician))
        self.assertFalse(can_deactivate_user(self.technician, self.viewer))
    
    def test_viewer_cannot_deactivate_any_user(self):
        """VIEWER cannot deactivate any user."""
        self.assertFalse(can_deactivate_user(self.viewer, self.technician))


class TestCanDeleteUser(unittest.TestCase):
    """Tests for can_delete_user function."""
    
    def setUp(self):
        self.superadmin = FakeUser('superadmin', 'SUPERADMIN')
        self.manager = FakeUser('manager', 'MANAGER')
        self.it_admin = FakeUser('it_admin', 'IT_ADMIN')
        self.technician = FakeUser('technician', 'TECHNICIAN')
        self.viewer = FakeUser('viewer', 'VIEWER')
    
    def test_cannot_delete_self(self):
        """Users cannot delete their own account."""
        self.assertFalse(can_delete_user(self.superadmin, self.superadmin))
        self.assertFalse(can_delete_user(self.manager, self.manager))
        self.assertFalse(can_delete_user(self.it_admin, self.it_admin))
        self.assertFalse(can_delete_user(self.technician, self.technician))
        self.assertFalse(can_delete_user(self.viewer, self.viewer))
    
    def test_only_superadmin_can_delete_other_users(self):
        """Only SUPERADMIN can delete other users."""
        # SUPERADMIN can delete
        self.assertTrue(can_delete_user(self.superadmin, self.manager))
        self.assertTrue(can_delete_user(self.superadmin, self.it_admin))
        self.assertTrue(can_delete_user(self.superadmin, self.technician))
        self.assertTrue(can_delete_user(self.superadmin, self.viewer))
        
        # Others cannot delete
        self.assertFalse(can_delete_user(self.manager, self.it_admin))
        self.assertFalse(can_delete_user(self.manager, self.technician))
        self.assertFalse(can_delete_user(self.it_admin, self.technician))
        self.assertFalse(can_delete_user(self.technician, self.viewer))


class TestGetUserPermissions(unittest.TestCase):
    """Tests for get_user_permissions function."""
    
    def setUp(self):
        self.superadmin = FakeUser('superadmin', 'SUPERADMIN')
        self.manager = FakeUser('manager', 'MANAGER')
        self.it_admin = FakeUser('it_admin', 'IT_ADMIN')
        self.technician = FakeUser('technician', 'TECHNICIAN')
        self.viewer = FakeUser('viewer', 'VIEWER')
    
    def test_manager_permissions_on_other_user(self):
        """MANAGER has correct permissions on another user."""
        perms = get_user_permissions(self.manager, self.it_admin)
        
        self.assertTrue(perms['can_view'])
        self.assertTrue(perms['can_update'])
        self.assertTrue(perms['can_change_role'])
        self.assertTrue(perms['can_deactivate'])
        self.assertFalse(perms['can_delete'])  # Only SUPERADMIN can delete
    
    def test_it_admin_permissions_on_technician(self):
        """IT_ADMIN has correct permissions on TECHNICIAN."""
        perms = get_user_permissions(self.it_admin, self.technician)
        
        self.assertTrue(perms['can_view'])
        self.assertTrue(perms['can_update'])
        self.assertTrue(perms['can_change_role'])
        self.assertTrue(perms['can_deactivate'])
        self.assertFalse(perms['can_delete'])
    
    def test_it_admin_permissions_on_manager(self):
        """IT_ADMIN has limited permissions on MANAGER."""
        perms = get_user_permissions(self.it_admin, self.manager)
        
        self.assertTrue(perms['can_view'])
        self.assertFalse(perms['can_update'])
        self.assertFalse(perms['can_change_role'])
        self.assertFalse(perms['can_deactivate'])
        self.assertFalse(perms['can_delete'])
    
    def test_technician_permissions_on_self(self):
        """TECHNICIAN has correct permissions on self."""
        perms = get_user_permissions(self.technician, self.technician)
        
        self.assertTrue(perms['can_view'])
        self.assertTrue(perms['can_update'])
        self.assertFalse(perms['can_change_role'])  # Cannot change own role
        self.assertFalse(perms['can_deactivate'])    # Cannot deactivate self
        self.assertFalse(perms['can_delete'])        # Cannot delete self


class TestAssertionHelpers(unittest.TestCase):
    """Tests for assertion helper functions."""
    
    def setUp(self):
        self.superadmin = FakeUser('superadmin', 'SUPERADMIN')
        self.manager = FakeUser('manager', 'MANAGER')
        self.it_admin = FakeUser('it_admin', 'IT_ADMIN')
        self.technician = FakeUser('technician', 'TECHNICIAN')
    
    def test_assert_can_update_user_passes_when_allowed(self):
        """assert_can_update_user passes when user can update."""
        # User updating self
        assert_can_update_user(self.technician, self.technician)
        # Manager updating technician
        assert_can_update_user(self.manager, self.technician)
    
    def test_assert_can_update_user_raises_when_denied(self):
        """assert_can_update_user raises AuthorizationError when denied."""
        with self.assertRaises(AuthorizationError):
            assert_can_update_user(self.technician, self.it_admin)
    
    def test_assert_can_change_role_passes_when_allowed(self):
        """assert_can_change_role passes when user can change role."""
        assert_can_change_role(self.manager, self.technician, 'VIEWER')
    
    def test_assert_can_change_role_raises_when_denied(self):
        """assert_can_change_role raises AuthorizationError when denied."""
        with self.assertRaises(AuthorizationError):
            assert_can_change_role(self.manager, self.it_admin, 'MANAGER')
        with self.assertRaises(AuthorizationError):
            assert_can_change_role(self.technician, self.viewer, 'TECHNICIAN')
    
    def test_assert_can_deactivate_user_passes_when_allowed(self):
        """assert_can_deactivate_user passes when user can deactivate."""
        assert_can_deactivate_user(self.manager, self.technician)
    
    def test_assert_can_deactivate_user_raises_when_denied(self):
        """assert_can_deactivate_user raises AuthorizationError when denied."""
        with self.assertRaises(AuthorizationError):
            assert_can_deactivate_user(self.technician, self.viewer)
    
    def test_assert_can_delete_user_passes_when_allowed(self):
        """assert_can_delete_user passes when user can delete."""
        assert_can_delete_user(self.superadmin, self.technician)
    
    def test_assert_can_delete_user_raises_when_denied(self):
        """assert_can_delete_user raises AuthorizationError when denied."""
        with self.assertRaises(AuthorizationError):
            assert_can_delete_user(self.manager, self.technician)


if __name__ == '__main__':
    unittest.main()

