"""
Unit tests for domain authorization service.

Tests can_modify_resource, can_delete_resource, can_view_resource,
and assertion helpers using pure domain logic without Django.
"""

import unittest

from apps.core.domain.authorization import (
    AuthorizationError,
    can_modify_resource,
    can_delete_resource,
    can_view_resource,
    assert_can_modify,
    assert_can_delete,
)


class FakeUser:
    """
    Lightweight user object for domain testing.
    Mimics the interface of real User models (role + username).
    """
    
    def __init__(self, username: str, role: str):
        self.username = username
        self.role = role
    
    def __eq__(self, other):
        if not isinstance(other, FakeUser):
            return False
        return self.username == other.username
    
    def __hash__(self):
        return hash(self.username)
    
    def __repr__(self):
        return f"FakeUser(username='{self.username}', role='{self.role}')"


class TestCanModifyResource(unittest.TestCase):
    """Tests for can_modify_resource function."""
    
    def test_superadmin_can_modify_anyone(self):
        """SUPERADMIN can modify resources owned by any user."""
        superadmin = FakeUser("admin1", "SUPERADMIN")
        technician = FakeUser("tech1", "TECHNICIAN")
        viewer = FakeUser("viewer1", "VIEWER")
        another_admin = FakeUser("admin2", "SUPERADMIN")
        
        self.assertTrue(can_modify_resource(superadmin, technician))
        self.assertTrue(can_modify_resource(superadmin, viewer))
        self.assertTrue(can_modify_resource(superadmin, another_admin))
        self.assertTrue(can_modify_resource(superadmin, superadmin))
    
    def test_manager_can_modify_anyone(self):
        """MANAGER can modify resources owned by any user."""
        manager = FakeUser("mgr1", "MANAGER")
        technician = FakeUser("tech1", "TECHNICIAN")
        viewer = FakeUser("viewer1", "VIEWER")
        it_admin = FakeUser("admin1", "IT_ADMIN")
        another_manager = FakeUser("mgr2", "MANAGER")
        
        self.assertTrue(can_modify_resource(manager, technician))
        self.assertTrue(can_modify_resource(manager, viewer))
        self.assertTrue(can_modify_resource(manager, it_admin))
        self.assertTrue(can_modify_resource(manager, another_manager))
    
    def test_user_can_modify_own_resource(self):
        """Users can modify their own resources regardless of role."""
        users = [
            FakeUser("viewer1", "VIEWER"),
            FakeUser("tech1", "TECHNICIAN"),
            FakeUser("admin1", "IT_ADMIN"),
            FakeUser("mgr1", "MANAGER"),
            FakeUser("admin2", "SUPERADMIN"),
        ]
        
        for user in users:
            with self.subTest(user=user):
                self.assertTrue(can_modify_resource(user, user))
    
    def test_higher_role_can_modify_lower_role(self):
        """Higher role rank can modify resources owned by lower role."""
        # IT_ADMIN > TECHNICIAN
        it_admin = FakeUser("admin1", "IT_ADMIN")
        technician = FakeUser("tech1", "TECHNICIAN")
        self.assertTrue(can_modify_resource(it_admin, technician))
        
        # IT_ADMIN > VIEWER
        viewer = FakeUser("viewer1", "VIEWER")
        self.assertTrue(can_modify_resource(it_admin, viewer))
        
        # TECHNICIAN > VIEWER
        technician = FakeUser("tech1", "TECHNICIAN")
        self.assertTrue(can_modify_resource(technician, viewer))
    
    def test_lower_role_cannot_modify_higher_role(self):
        """Lower role rank cannot modify resources owned by higher role."""
        viewer = FakeUser("viewer1", "VIEWER")
        technician = FakeUser("tech1", "TECHNICIAN")
        it_admin = FakeUser("admin1", "IT_ADMIN")
        manager = FakeUser("mgr1", "MANAGER")
        superadmin = FakeUser("admin1", "SUPERADMIN")
        
        # VIEWER cannot modify anyone higher
        self.assertFalse(can_modify_resource(viewer, technician))
        self.assertFalse(can_modify_resource(viewer, it_admin))
        self.assertFalse(can_modify_resource(viewer, manager))
        self.assertFalse(can_modify_resource(viewer, superadmin))
        
        # TECHNICIAN cannot modify IT_ADMIN, MANAGER, SUPERADMIN
        self.assertFalse(can_modify_resource(technician, it_admin))
        self.assertFalse(can_modify_resource(technician, manager))
        self.assertFalse(can_modify_resource(technician, superadmin))
    
    def test_same_rank_cannot_modify_each_other(self):
        """Users with same rank cannot modify each other's resources."""
        # Two TECHNICIANs
        tech1 = FakeUser("tech1", "TECHNICIAN")
        tech2 = FakeUser("tech2", "TECHNICIAN")
        self.assertFalse(can_modify_resource(tech1, tech2))
        self.assertFalse(can_modify_resource(tech2, tech1))
        
        # Two IT_ADMINs
        admin1 = FakeUser("admin1", "IT_ADMIN")
        admin2 = FakeUser("admin2", "IT_ADMIN")
        self.assertFalse(can_modify_resource(admin1, admin2))
        self.assertFalse(can_modify_resource(admin2, admin1))
    
    def test_manager_and_superadmin_same_rank(self):
        """MANAGER and SUPERADMIN have same rank but are admins (can modify anyone)."""
        manager = FakeUser("mgr1", "MANAGER")
        superadmin = FakeUser("admin1", "SUPERADMIN")
        technician = FakeUser("tech1", "TECHNICIAN")
        
        # Both admins can modify technician
        self.assertTrue(can_modify_resource(manager, technician))
        self.assertTrue(can_modify_resource(superadmin, technician))
        
        # They can also modify each other (admin override)
        self.assertTrue(can_modify_resource(manager, superadmin))
        self.assertTrue(can_modify_resource(superadmin, manager))


class TestCanDeleteResource(unittest.TestCase):
    """Tests for can_delete_resource function."""
    
    def test_superadmin_can_delete_anyone(self):
        """SUPERADMIN can delete resources owned by any user."""
        superadmin = FakeUser("admin1", "SUPERADMIN")
        technician = FakeUser("tech1", "TECHNICIAN")
        viewer = FakeUser("viewer1", "VIEWER")
        another_admin = FakeUser("admin2", "SUPERADMIN")
        
        self.assertTrue(can_delete_resource(superadmin, technician))
        self.assertTrue(can_delete_resource(superadmin, viewer))
        self.assertTrue(can_delete_resource(superadmin, another_admin))
    
    def test_manager_can_delete_anyone(self):
        """MANAGER can delete resources owned by any user."""
        manager = FakeUser("mgr1", "MANAGER")
        technician = FakeUser("tech1", "TECHNICIAN")
        viewer = FakeUser("viewer1", "VIEWER")
        it_admin = FakeUser("admin1", "IT_ADMIN")
        another_manager = FakeUser("mgr2", "MANAGER")
        
        self.assertTrue(can_delete_resource(manager, technician))
        self.assertTrue(can_delete_resource(manager, viewer))
        self.assertTrue(can_delete_resource(manager, it_admin))
        self.assertTrue(can_delete_resource(manager, another_manager))
    
    def test_user_can_delete_own_resource(self):
        """Users can delete their own resources regardless of role."""
        users = [
            FakeUser("viewer1", "VIEWER"),
            FakeUser("tech1", "TECHNICIAN"),
            FakeUser("admin1", "IT_ADMIN"),
            FakeUser("mgr1", "MANAGER"),
            FakeUser("admin2", "SUPERADMIN"),
        ]
        
        for user in users:
            with self.subTest(user=user):
                self.assertTrue(can_delete_resource(user, user))
    
    def test_non_admin_cannot_delete_higher_role(self):
        """Non-admin users cannot delete resources owned by higher role."""
        viewer = FakeUser("viewer1", "VIEWER")
        technician = FakeUser("tech1", "TECHNICIAN")
        it_admin = FakeUser("admin1", "IT_ADMIN")
        
        # TECHNICIAN cannot delete IT_ADMIN's resource
        self.assertFalse(can_delete_resource(technician, it_admin))
        
        # VIEWER cannot delete TECHNICIAN's resource
        self.assertFalse(can_delete_resource(viewer, technician))
    
    def test_non_admin_same_rank_cannot_delete(self):
        """Users with same rank cannot delete each other's resources."""
        tech1 = FakeUser("tech1", "TECHNICIAN")
        tech2 = FakeUser("tech2", "TECHNICIAN")
        
        self.assertFalse(can_delete_resource(tech1, tech2))
        self.assertFalse(can_delete_resource(tech2, tech1))
    
    def test_it_admin_cannot_delete_manager_or_superadmin(self):
        """IT_ADMIN (non-admin) cannot delete MANAGER or SUPERADMIN."""
        it_admin = FakeUser("admin1", "IT_ADMIN")
        manager = FakeUser("mgr1", "MANAGER")
        superadmin = FakeUser("admin2", "SUPERADMIN")
        
        self.assertFalse(can_delete_resource(it_admin, manager))
        self.assertFalse(can_delete_resource(it_admin, superadmin))


class TestCanViewResource(unittest.TestCase):
    """Tests for can_view_resource function."""
    
    def test_can_view_own_resource(self):
        """Users can always view their own resources."""
        users = [
            FakeUser("viewer1", "VIEWER"),
            FakeUser("tech1", "TECHNICIAN"),
            FakeUser("admin1", "IT_ADMIN"),
            FakeUser("mgr1", "MANAGER"),
            FakeUser("admin2", "SUPERADMIN"),
        ]
        
        for user in users:
            with self.subTest(user=user):
                self.assertTrue(can_view_resource(user, user))
    
    def test_superadmin_can_view_anyone(self):
        """SUPERADMIN can view resources owned by any user."""
        superadmin = FakeUser("admin1", "SUPERADMIN")
        technician = FakeUser("tech1", "TECHNICIAN")
        viewer = FakeUser("viewer1", "VIEWER")
        
        self.assertTrue(can_view_resource(superadmin, technician))
        self.assertTrue(can_view_resource(superadmin, viewer))
    
    def test_manager_can_view_anyone(self):
        """MANAGER can view resources owned by any user."""
        manager = FakeUser("mgr1", "MANAGER")
        technician = FakeUser("tech1", "TECHNICIAN")
        viewer = FakeUser("viewer1", "VIEWER")
        it_admin = FakeUser("admin1", "IT_ADMIN")
        
        self.assertTrue(can_view_resource(manager, technician))
        self.assertTrue(can_view_resource(manager, viewer))
        self.assertTrue(can_view_resource(manager, it_admin))
    
    def test_higher_or_equal_role_can_view_lower(self):
        """Higher or equal role can view resources owned by lower role."""
        it_admin = FakeUser("admin1", "IT_ADMIN")
        technician = FakeUser("tech1", "TECHNICIAN")
        viewer = FakeUser("viewer1", "VIEWER")
        
        self.assertTrue(can_view_resource(it_admin, technician))
        self.assertTrue(can_view_resource(it_admin, viewer))
        
        self.assertTrue(can_view_resource(technician, viewer))
    
    def test_same_role_can_view_each_other(self):
        """Users with same role can view each other's resources."""
        tech1 = FakeUser("tech1", "TECHNICIAN")
        tech2 = FakeUser("tech2", "TECHNICIAN")
        
        self.assertTrue(can_view_resource(tech1, tech2))
        self.assertTrue(can_view_resource(tech2, tech1))
    
    def test_manager_and_superadmin_can_view_each_other(self):
        """MANAGER and SUPERADMIN can view each other's resources."""
        manager = FakeUser("mgr1", "MANAGER")
        superadmin = FakeUser("admin1", "SUPERADMIN")
        
        self.assertTrue(can_view_resource(manager, superadmin))
        self.assertTrue(can_view_resource(superadmin, manager))


class TestAssertCanModify(unittest.TestCase):
    """Tests for assert_can_modify function."""
    
    def test_assert_passes_when_authorized(self):
        """assert_can_modify does not raise when actor is authorized."""
        superadmin = FakeUser("admin1", "SUPERADMIN")
        technician = FakeUser("tech1", "TECHNICIAN")
        
        # Should not raise
        assert_can_modify(superadmin, technician)
        
        # User modifying own resource
        viewer = FakeUser("viewer1", "VIEWER")
        assert_can_modify(viewer, viewer)
    
    def test_assert_raises_when_unauthorized(self):
        """assert_can_modify raises AuthorizationError when actor is not authorized."""
        viewer = FakeUser("viewer1", "VIEWER")
        technician = FakeUser("tech1", "TECHNICIAN")
        
        with self.assertRaises(AuthorizationError) as ctx:
            assert_can_modify(viewer, technician)
        
        self.assertIn("viewer1", str(ctx.exception))
        self.assertIn("tech1", str(ctx.exception))
    
    def test_assert_raises_same_rank(self):
        """assert_can_modify raises when same-rank users try to modify."""
        tech1 = FakeUser("tech1", "TECHNICIAN")
        tech2 = FakeUser("tech2", "TECHNICIAN")
        
        with self.assertRaises(AuthorizationError):
            assert_can_modify(tech1, tech2)


class TestAssertCanDelete(unittest.TestCase):
    """Tests for assert_can_delete function."""
    
    def test_assert_passes_when_authorized(self):
        """assert_can_delete does not raise when actor is authorized."""
        superadmin = FakeUser("admin1", "SUPERADMIN")
        technician = FakeUser("tech1", "TECHNICIAN")
        
        # Should not raise
        assert_can_delete(superadmin, technician)
        
        # User deleting own resource
        viewer = FakeUser("viewer1", "VIEWER")
        assert_can_delete(viewer, viewer)
    
    def test_assert_raises_when_unauthorized(self):
        """assert_can_delete raises AuthorizationError when actor is not authorized."""
        viewer = FakeUser("viewer1", "VIEWER")
        technician = FakeUser("tech1", "TECHNICIAN")
        
        with self.assertRaises(AuthorizationError) as ctx:
            assert_can_delete(viewer, technician)
        
        self.assertIn("viewer1", str(ctx.exception))
        self.assertIn("tech1", str(ctx.exception))
    
    def test_assert_raises_same_rank(self):
        """assert_can_delete raises when same-rank users try to delete."""
        tech1 = FakeUser("tech1", "TECHNICIAN")
        tech2 = FakeUser("tech2", "TECHNICIAN")
        
        with self.assertRaises(AuthorizationError):
            assert_can_delete(tech1, tech2)
    
    def test_assert_raises_it_admin_deleting_manager(self):
        """IT_ADMIN cannot delete MANAGER's resources."""
        it_admin = FakeUser("admin1", "IT_ADMIN")
        manager = FakeUser("mgr1", "MANAGER")
        
        with self.assertRaises(AuthorizationError):
            assert_can_delete(it_admin, manager)


class TestAuthorizationError(unittest.TestCase):
    """Tests for AuthorizationError exception."""
    
    def test_error_message_format(self):
        """AuthorizationError message includes actor and owner usernames."""
        error = AuthorizationError(
            "User 'alice' is not authorized to modify resource owned by 'bob'"
        )
        
        self.assertIn("alice", str(error))
        self.assertIn("bob", str(error))
        self.assertIn("not authorized", str(error))
    
    def test_error_is_exception(self):
        """AuthorizationError is a proper Exception subclass."""
        error = AuthorizationError("test")
        self.assertIsInstance(error, Exception)


class TestAuthorizationScenarios(unittest.TestCase):
    """Integration-style tests for complex authorization scenarios."""
    
    def test_full_hierarchy_modify_scenario(self):
        """
        Test modify permissions across the full role hierarchy:
        SUPERADMIN > MANAGER > IT_ADMIN > TECHNICIAN > VIEWER
        (MANAGER and SUPERADMIN are equal and both admins)
        """
        users = {
            'superadmin': FakeUser("admin", "SUPERADMIN"),
            'manager': FakeUser("mgr", "MANAGER"),
            'it_admin': FakeUser("admin2", "IT_ADMIN"),
            'technician': FakeUser("tech", "TECHNICIAN"),
            'viewer': FakeUser("viewer", "VIEWER"),
        }
        
        # Admins can modify anyone
        for admin in ['superadmin', 'manager']:
            for target in users:
                with self.subTest(admin=admin, target=target):
                    self.assertTrue(
                        can_modify_resource(users[admin], users[target])
                    )
        
        # IT_ADMIN can modify TECHNICIAN and VIEWER
        self.assertTrue(can_modify_resource(users['it_admin'], users['technician']))
        self.assertTrue(can_modify_resource(users['it_admin'], users['viewer']))
        
        # IT_ADMIN cannot modify MANAGER or SUPERADMIN
        self.assertFalse(can_modify_resource(users['it_admin'], users['manager']))
        self.assertFalse(can_modify_resource(users['it_admin'], users['superadmin']))
        
        # TECHNICIAN can only modify VIEWER
        self.assertTrue(can_modify_resource(users['technician'], users['viewer']))
        self.assertFalse(can_modify_resource(users['technician'], users['it_admin']))
        
        # VIEWER cannot modify anyone
        for target in users:
            if target != 'viewer':
                with self.subTest(viewer='viewer', target=target):
                    self.assertFalse(
                        can_modify_resource(users['viewer'], users[target])
                    )
    
    def test_full_hierarchy_delete_scenario(self):
        """
        Test delete permissions across the full role hierarchy.
        Deletion is stricter - only admins can delete others' resources.
        """
        users = {
            'superadmin': FakeUser("admin", "SUPERADMIN"),
            'manager': FakeUser("mgr", "MANAGER"),
            'it_admin': FakeUser("admin2", "IT_ADMIN"),
            'technician': FakeUser("tech", "TECHNICIAN"),
            'viewer': FakeUser("viewer", "VIEWER"),
        }
        
        # Admins can delete anyone
        for admin in ['superadmin', 'manager']:
            for target in users:
                with self.subTest(admin=admin, target=target):
                    self.assertTrue(
                        can_delete_resource(users[admin], users[target])
                    )
        
        # IT_ADMIN cannot delete anyone except self
        for target in users:
            if target != 'it_admin':
                with self.subTest(target=target):
                    self.assertFalse(
                        can_delete_resource(users['it_admin'], users[target])
                    )
        
        # TECHNICIAN cannot delete anyone except self
        for target in users:
            if target != 'technician':
                with self.subTest(target=target):
                    self.assertFalse(
                        can_delete_resource(users['technician'], users[target])
                    )
        
        # VIEWER cannot delete anyone except self
        for target in users:
            if target != 'viewer':
                with self.subTest(target=target):
                    self.assertFalse(
                        can_delete_resource(users['viewer'], users[target])
                    )


if __name__ == "__main__":
    unittest.main()

