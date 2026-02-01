"""
Unit tests for role hierarchy utilities.

Tests pure domain utilities from apps.core.domain.roles without Django dependencies.
"""

import unittest

from apps.core.domain.roles import (
    ROLE_RANKS,
    VALID_ROLES,
    get_role_rank,
    has_higher_role,
    has_strictly_higher_role,
    compare_roles,
    is_admin_role,
    is_superadmin_or_manager,
    is_lowest_role,
    ROLE_HIERARCHY,
)


class TestRoleRanksValues(unittest.TestCase):
    """Test that ROLE_RANKS contains correct values."""

    def test_viewer_rank_is_one(self):
        """VIEWER should have rank 1 (lowest non-zero rank)."""
        self.assertEqual(ROLE_RANKS['VIEWER'], 1)

    def test_technician_rank_is_two(self):
        """TECHNICIAN should have rank 2."""
        self.assertEqual(ROLE_RANKS['TECHNICIAN'], 2)

    def test_it_admin_rank_is_three(self):
        """IT_ADMIN should have rank 3."""
        self.assertEqual(ROLE_RANKS['IT_ADMIN'], 3)

    def test_manager_rank_is_four(self):
        """MANAGER should have rank 4."""
        self.assertEqual(ROLE_RANKS['MANAGER'], 4)

    def test_superadmin_rank_is_four(self):
        """SUPERADMIN should have rank 4."""
        self.assertEqual(ROLE_RANKS['SUPERADMIN'], 4)


class TestManagerEqualsSuperadmin(unittest.TestCase):
    """Test that MANAGER and SUPERADMIN have equal privileges."""

    def test_manager_and_superadmin_same_rank(self):
        """MANAGER and SUPERADMIN should have the same rank."""
        self.assertEqual(ROLE_RANKS['MANAGER'], ROLE_RANKS['SUPERADMIN'])
        self.assertEqual(ROLE_RANKS['MANAGER'], 4)
        self.assertEqual(ROLE_RANKS['SUPERADMIN'], 4)

    def test_has_higher_role_equal_ranks(self):
        """has_higher_role should return True when roles have equal rank."""
        # MANAGER >= SUPERADMIN should be True (equal)
        self.assertTrue(has_higher_role('MANAGER', 'SUPERADMIN'))
        # SUPERADMIN >= MANAGER should be True (equal)
        self.assertTrue(has_higher_role('SUPERADMIN', 'MANAGER'))

    def test_has_strictly_higher_role_equal_ranks(self):
        """has_strictly_higher_role should return False when roles have equal rank."""
        # MANAGER > SUPERADMIN should be False (equal)
        self.assertFalse(has_strictly_higher_role('MANAGER', 'SUPERADMIN'))
        # SUPERADMIN > MANAGER should be False (equal)
        self.assertFalse(has_strictly_higher_role('SUPERADMIN', 'MANAGER'))

    def test_compare_roles_equal_ranks(self):
        """compare_roles should return 0 when roles have equal rank."""
        self.assertEqual(compare_roles('MANAGER', 'SUPERADMIN'), 0)
        self.assertEqual(compare_roles('SUPERADMIN', 'MANAGER'), 0)


class TestViewerIsLowest(unittest.TestCase):
    """Test that VIEWER is the lowest privilege role."""

    def test_viewer_is_lowest_rank(self):
        """VIEWER should have the lowest non-zero rank."""
        self.assertEqual(get_role_rank('VIEWER'), 1)

    def test_viewer_has_lower_rank_than_all_others(self):
        """VIEWER rank should be lower than all other roles."""
        self.assertLess(ROLE_RANKS['VIEWER'], ROLE_RANKS['TECHNICIAN'])
        self.assertLess(ROLE_RANKS['VIEWER'], ROLE_RANKS['IT_ADMIN'])
        self.assertLess(ROLE_RANKS['VIEWER'], ROLE_RANKS['MANAGER'])
        self.assertLess(ROLE_RANKS['VIEWER'], ROLE_RANKS['SUPERADMIN'])

    def test_is_lowest_role(self):
        """is_lowest_role should return True only for VIEWER."""
        self.assertTrue(is_lowest_role('VIEWER'))
        self.assertFalse(is_lowest_role('TECHNICIAN'))
        self.assertFalse(is_lowest_role('IT_ADMIN'))
        self.assertFalse(is_lowest_role('MANAGER'))
        self.assertFalse(is_lowest_role('SUPERADMIN'))

    def test_viewer_not_higher_than_anyone(self):
        """VIEWER should not have higher or equal role compared to others (except itself)."""
        self.assertFalse(has_higher_role('VIEWER', 'TECHNICIAN'))
        self.assertFalse(has_higher_role('VIEWER', 'IT_ADMIN'))
        self.assertFalse(has_higher_role('VIEWER', 'MANAGER'))
        self.assertFalse(has_higher_role('VIEWER', 'SUPERADMIN'))
        # VIEWER >= VIEWER should be True (equal)
        self.assertTrue(has_higher_role('VIEWER', 'VIEWER'))

    def test_viewer_not_strictly_higher_than_anyone(self):
        """VIEWER should not have strictly higher role than anyone."""
        self.assertFalse(has_strictly_higher_role('VIEWER', 'TECHNICIAN'))
        self.assertFalse(has_strictly_higher_role('VIEWER', 'IT_ADMIN'))
        self.assertFalse(has_strictly_higher_role('VIEWER', 'MANAGER'))
        self.assertFalse(has_strictly_higher_role('VIEWER', 'SUPERADMIN'))
        self.assertFalse(has_strictly_higher_role('VIEWER', 'VIEWER'))


class TestHasHigherRole(unittest.TestCase):
    """Test has_higher_role function."""

    def test_superadmin_greater_equal_manager(self):
        """SUPERADMIN >= MANAGER should be True (equal ranks)."""
        self.assertTrue(has_higher_role('SUPERADMIN', 'MANAGER'))

    def test_manager_greater_equal_it_admin(self):
        """MANAGER >= IT_ADMIN should be True."""
        self.assertTrue(has_higher_role('MANAGER', 'IT_ADMIN'))

    def test_it_admin_greater_equal_technician(self):
        """IT_ADMIN >= TECHNICIAN should be True."""
        self.assertTrue(has_higher_role('IT_ADMIN', 'TECHNICIAN'))

    def test_technician_greater_equal_viewer(self):
        """TECHNICIAN >= VIEWER should be True."""
        self.assertTrue(has_higher_role('TECHNICIAN', 'VIEWER'))

    def test_superadmin_greater_equal_all(self):
        """SUPERADMIN should have higher or equal role than all others."""
        self.assertTrue(has_higher_role('SUPERADMIN', 'SUPERADMIN'))
        self.assertTrue(has_higher_role('SUPERADMIN', 'MANAGER'))
        self.assertTrue(has_higher_role('SUPERADMIN', 'IT_ADMIN'))
        self.assertTrue(has_higher_role('SUPERADMIN', 'TECHNICIAN'))
        self.assertTrue(has_higher_role('SUPERADMIN', 'VIEWER'))

    def test_manager_greater_equal_all_except_superadmin(self):
        """MANAGER should have higher or equal role than all except SUPERADMIN."""
        self.assertTrue(has_higher_role('MANAGER', 'MANAGER'))
        self.assertTrue(has_higher_role('MANAGER', 'IT_ADMIN'))
        self.assertTrue(has_higher_role('MANAGER', 'TECHNICIAN'))
        self.assertTrue(has_higher_role('MANAGER', 'VIEWER'))

    def test_it_admin_greater_equal_lower_roles(self):
        """IT_ADMIN should have higher or equal role than TECHNICIAN and VIEWER."""
        self.assertTrue(has_higher_role('IT_ADMIN', 'IT_ADMIN'))
        self.assertTrue(has_higher_role('IT_ADMIN', 'TECHNICIAN'))
        self.assertTrue(has_higher_role('IT_ADMIN', 'VIEWER'))
        self.assertFalse(has_higher_role('IT_ADMIN', 'MANAGER'))
        self.assertFalse(has_higher_role('IT_ADMIN', 'SUPERADMIN'))

    def test_technician_greater_equal_viewer(self):
        """TECHNICIAN should have higher or equal role than VIEWER."""
        self.assertTrue(has_higher_role('TECHNICIAN', 'TECHNICIAN'))
        self.assertTrue(has_higher_role('TECHNICIAN', 'VIEWER'))
        self.assertFalse(has_higher_role('TECHNICIAN', 'IT_ADMIN'))
        self.assertFalse(has_higher_role('TECHNICIAN', 'MANAGER'))
        self.assertFalse(has_higher_role('TECHNICIAN', 'SUPERADMIN'))

    def test_lower_role_not_higher_than_higher_role(self):
        """Lower roles should not have higher or equal role than higher roles."""
        self.assertFalse(has_higher_role('VIEWER', 'TECHNICIAN'))
        self.assertFalse(has_higher_role('VIEWER', 'IT_ADMIN'))
        self.assertFalse(has_higher_role('VIEWER', 'MANAGER'))
        self.assertFalse(has_higher_role('VIEWER', 'SUPERADMIN'))
        self.assertFalse(has_higher_role('TECHNICIAN', 'IT_ADMIN'))
        self.assertFalse(has_higher_role('TECHNICIAN', 'MANAGER'))
        self.assertFalse(has_higher_role('TECHNICIAN', 'SUPERADMIN'))
        self.assertFalse(has_higher_role('IT_ADMIN', 'MANAGER'))
        self.assertFalse(has_higher_role('IT_ADMIN', 'SUPERADMIN'))

    def test_invalid_role_returns_zero_rank(self):
        """Invalid roles should return 0 rank and not be higher than valid roles."""
        self.assertEqual(get_role_rank('INVALID_ROLE'), 0)
        self.assertFalse(has_higher_role('INVALID_ROLE', 'SUPERADMIN'))
        self.assertFalse(has_higher_role('SUPERADMIN', 'INVALID_ROLE'))


class TestHasStrictlyHigherRole(unittest.TestCase):
    """Test has_strictly_higher_role function."""

    def test_manager_strictly_greater_than_it_admin(self):
        """MANAGER > IT_ADMIN should be True."""
        self.assertTrue(has_strictly_higher_role('MANAGER', 'IT_ADMIN'))

    def test_it_admin_strictly_greater_than_technician(self):
        """IT_ADMIN > TECHNICIAN should be True."""
        self.assertTrue(has_strictly_higher_role('IT_ADMIN', 'TECHNICIAN'))

    def test_technician_strictly_greater_than_viewer(self):
        """TECHNICIAN > VIEWER should be True."""
        self.assertTrue(has_strictly_higher_role('TECHNICIAN', 'VIEWER'))

    def test_superadmin_not_strictly_greater_than_manager(self):
        """SUPERADMIN > MANAGER should be False (equal ranks)."""
        self.assertFalse(has_strictly_higher_role('SUPERADMIN', 'MANAGER'))

    def test_manager_not_strictly_greater_than_superadmin(self):
        """MANAGER > SUPERADMIN should be False (equal ranks)."""
        self.assertFalse(has_strictly_higher_role('MANAGER', 'SUPERADMIN'))

    def test_same_role_not_strictly_greater(self):
        """Same roles should not be strictly greater than each other."""
        self.assertFalse(has_strictly_higher_role('VIEWER', 'VIEWER'))
        self.assertFalse(has_strictly_higher_role('TECHNICIAN', 'TECHNICIAN'))
        self.assertFalse(has_strictly_higher_role('IT_ADMIN', 'IT_ADMIN'))
        self.assertFalse(has_strictly_higher_role('MANAGER', 'MANAGER'))
        self.assertFalse(has_strictly_higher_role('SUPERADMIN', 'SUPERADMIN'))

    def test_superadmin_strictly_greater_than_lower_roles(self):
        """SUPERADMIN should be strictly greater than IT_ADMIN, TECHNICIAN, VIEWER."""
        self.assertTrue(has_strictly_higher_role('SUPERADMIN', 'IT_ADMIN'))
        self.assertTrue(has_strictly_higher_role('SUPERADMIN', 'TECHNICIAN'))
        self.assertTrue(has_strictly_higher_role('SUPERADMIN', 'VIEWER'))

    def test_manager_strictly_greater_than_lower_roles(self):
        """MANAGER should be strictly greater than IT_ADMIN, TECHNICIAN, VIEWER."""
        self.assertTrue(has_strictly_higher_role('MANAGER', 'IT_ADMIN'))
        self.assertTrue(has_strictly_higher_role('MANAGER', 'TECHNICIAN'))
        self.assertTrue(has_strictly_higher_role('MANAGER', 'VIEWER'))

    def test_lower_roles_not_strictly_greater_than_higher(self):
        """Lower roles should not be strictly greater than higher roles."""
        self.assertFalse(has_strictly_higher_role('IT_ADMIN', 'MANAGER'))
        self.assertFalse(has_strictly_higher_role('IT_ADMIN', 'SUPERADMIN'))
        self.assertFalse(has_strictly_higher_role('TECHNICIAN', 'MANAGER'))
        self.assertFalse(has_strictly_higher_role('TECHNICIAN', 'SUPERADMIN'))
        self.assertFalse(has_strictly_higher_role('TECHNICIAN', 'IT_ADMIN'))
        self.assertFalse(has_strictly_higher_role('VIEWER', 'IT_ADMIN'))
        self.assertFalse(has_strictly_higher_role('VIEWER', 'MANAGER'))
        self.assertFalse(has_strictly_higher_role('VIEWER', 'SUPERADMIN'))


class TestCompareRoles(unittest.TestCase):
    """Test compare_roles function."""

    def test_superadmin_greater_than_lower_roles(self):
        """SUPERADMIN should be greater than IT_ADMIN, TECHNICIAN, VIEWER."""
        self.assertEqual(compare_roles('SUPERADMIN', 'SUPERADMIN'), 0)
        self.assertEqual(compare_roles('SUPERADMIN', 'MANAGER'), 0)  # equal
        self.assertEqual(compare_roles('SUPERADMIN', 'IT_ADMIN'), 1)
        self.assertEqual(compare_roles('SUPERADMIN', 'TECHNICIAN'), 1)
        self.assertEqual(compare_roles('SUPERADMIN', 'VIEWER'), 1)

    def test_manager_greater_than_lower_roles(self):
        """MANAGER should be greater than IT_ADMIN, TECHNICIAN, VIEWER."""
        self.assertEqual(compare_roles('MANAGER', 'MANAGER'), 0)
        self.assertEqual(compare_roles('MANAGER', 'IT_ADMIN'), 1)
        self.assertEqual(compare_roles('MANAGER', 'TECHNICIAN'), 1)
        self.assertEqual(compare_roles('MANAGER', 'VIEWER'), 1)
        self.assertEqual(compare_roles('MANAGER', 'SUPERADMIN'), 0)  # equal

    def test_it_admin_greater_than_lower_roles(self):
        """IT_ADMIN should be greater than TECHNICIAN and VIEWER."""
        self.assertEqual(compare_roles('IT_ADMIN', 'IT_ADMIN'), 0)
        self.assertEqual(compare_roles('IT_ADMIN', 'TECHNICIAN'), 1)
        self.assertEqual(compare_roles('IT_ADMIN', 'VIEWER'), 1)
        self.assertEqual(compare_roles('IT_ADMIN', 'MANAGER'), -1)
        self.assertEqual(compare_roles('IT_ADMIN', 'SUPERADMIN'), -1)

    def test_technician_greater_than_viewer(self):
        """TECHNICIAN should be greater than VIEWER."""
        self.assertEqual(compare_roles('TECHNICIAN', 'TECHNICIAN'), 0)
        self.assertEqual(compare_roles('TECHNICIAN', 'VIEWER'), 1)
        self.assertEqual(compare_roles('TECHNICIAN', 'IT_ADMIN'), -1)
        self.assertEqual(compare_roles('TECHNICIAN', 'MANAGER'), -1)
        self.assertEqual(compare_roles('TECHNICIAN', 'SUPERADMIN'), -1)

    def test_viewer_less_than_all_others(self):
        """VIEWER should be less than all other roles."""
        self.assertEqual(compare_roles('VIEWER', 'VIEWER'), 0)
        self.assertEqual(compare_roles('VIEWER', 'TECHNICIAN'), -1)
        self.assertEqual(compare_roles('VIEWER', 'IT_ADMIN'), -1)
        self.assertEqual(compare_roles('VIEWER', 'MANAGER'), -1)
        self.assertEqual(compare_roles('VIEWER', 'SUPERADMIN'), -1)

    def test_invalid_role_less_than_valid_role(self):
        """Invalid roles should compare as less than valid roles."""
        self.assertEqual(compare_roles('INVALID_ROLE', 'SUPERADMIN'), -1)
        self.assertEqual(compare_roles('SUPERADMIN', 'INVALID_ROLE'), 1)


class TestRoleHierarchy(unittest.TestCase):
    """Test ROLE_HIERARCHY ordering."""

    def test_role_hierarchy_order(self):
        """ROLE_HIERARCHY should be ordered from lowest to highest."""
        expected_order = ('VIEWER', 'TECHNICIAN', 'IT_ADMIN', 'MANAGER', 'SUPERADMIN')
        self.assertEqual(ROLE_HIERARCHY, expected_order)

    def test_valid_roles_contains_all_roles(self):
        """VALID_ROLES should contain all defined roles."""
        expected_roles = frozenset(['VIEWER', 'TECHNICIAN', 'IT_ADMIN', 'MANAGER', 'SUPERADMIN'])
        self.assertEqual(VALID_ROLES, expected_roles)


class TestAdminRoleChecks(unittest.TestCase):
    """Test is_admin_role and is_superadmin_or_manager functions."""

    def test_is_admin_role(self):
        """is_admin_role should return True for IT_ADMIN and above."""
        self.assertTrue(is_admin_role('IT_ADMIN'))
        self.assertTrue(is_admin_role('MANAGER'))
        self.assertTrue(is_admin_role('SUPERADMIN'))
        self.assertFalse(is_admin_role('TECHNICIAN'))
        self.assertFalse(is_admin_role('VIEWER'))

    def test_is_superadmin_or_manager(self):
        """is_superadmin_or_manager should return True only for SUPERADMIN and MANAGER."""
        self.assertTrue(is_superadmin_or_manager('SUPERADMIN'))
        self.assertTrue(is_superadmin_or_manager('MANAGER'))
        self.assertFalse(is_superadmin_or_manager('IT_ADMIN'))
        self.assertFalse(is_superadmin_or_manager('TECHNICIAN'))
        self.assertFalse(is_superadmin_or_manager('VIEWER'))


if __name__ == '__main__':
    unittest.main()

