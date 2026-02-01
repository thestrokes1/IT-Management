"""
Domain unit tests for ticket authority rules.

Tests the pure domain logic for ticket permissions based on role hierarchy.
No Django imports, no ORM or database - pure domain tests.
"""

import sys
sys.path.insert(0, '.')

import unittest

from apps.tickets.domain.services.ticket_authority import (
    can_create_ticket,
    can_read_ticket,
    can_update_ticket,
    can_delete_ticket,
    can_assign_ticket,
    can_close_ticket,
    can_resolve_ticket,
    can_reopen_ticket,
    can_assign_self,
    get_ticket_permissions,
)


# ============================================================================
# Fake Classes for Testing (No Django/ORM dependencies)
# ============================================================================

class FakeUser:
    """Fake user for testing ticket permissions."""
    
    def __init__(self, user_id: int, username: str, role: str):
        self.id = user_id
        self.username = username
        self.role = role
    
    def __eq__(self, other):
        return isinstance(other, FakeUser) and self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
    
    def __repr__(self):
        return f"FakeUser({self.id}, '{self.username}', '{self.role}')"


class FakeTicket:
    """Fake ticket for testing permissions."""
    
    def __init__(self, ticket_id: int, title: str, created_by: FakeUser, assigned_to: FakeUser = None):
        self.id = ticket_id
        self.title = title
        self.created_by = created_by
        self.created_by_id = created_by.id
        self.assigned_to = assigned_to
    
    def __repr__(self):
        return f"FakeTicket({self.id}, '{self.title}', created_by={self.created_by})"


# ============================================================================
# Test Fixtures
# ============================================================================

class TestFixtures(unittest.TestCase):
    """Test fixtures setup."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Users of different roles
        self.superadmin = FakeUser(1, 'superadmin', 'SUPERADMIN')
        self.manager = FakeUser(2, 'manager', 'MANAGER')
        self.it_admin = FakeUser(3, 'it_admin', 'IT_ADMIN')
        self.technician = FakeUser(4, 'technician', 'TECHNICIAN')
        self.viewer = FakeUser(5, 'viewer', 'VIEWER')
        
        # Another technician for testing same-role scenarios
        self.technician2 = FakeUser(6, 'technician2', 'TECHNICIAN')
        self.it_admin2 = FakeUser(7, 'it_admin2', 'IT_ADMIN')
        
        # Tickets created by different users
        self.ticket_by_superadmin = FakeTicket(1, 'Ticket by SA', self.superadmin)
        self.ticket_by_manager = FakeTicket(2, 'Ticket by MGR', self.manager)
        self.ticket_by_it_admin = FakeTicket(3, 'Ticket by IT_ADMIN', self.it_admin)
        self.ticket_by_it_admin2 = FakeTicket(4, 'Ticket by IT_ADMIN2', self.it_admin2)
        self.ticket_by_technician = FakeTicket(5, 'Ticket by TECH', self.technician)
        self.ticket_by_technician2 = FakeTicket(6, 'Ticket by TECH2', self.technician2)
        self.ticket_by_viewer = FakeTicket(7, 'Ticket by VIEWER', self.viewer)


# ============================================================================
# Test Can Create Ticket
# ============================================================================

class TestCanCreateTicket(TestFixtures):
    """Tests for can_create_ticket function."""
    
    def test_superadmin_can_create(self):
        """SUPERADMIN can create tickets."""
        self.assertTrue(can_create_ticket(self.superadmin))
    
    def test_manager_can_create(self):
        """MANAGER can create tickets."""
        self.assertTrue(can_create_ticket(self.manager))
    
    def test_it_admin_can_create(self):
        """IT_ADMIN can create tickets."""
        self.assertTrue(can_create_ticket(self.it_admin))
    
    def test_technician_can_create(self):
        """TECHNICIAN can create tickets."""
        self.assertTrue(can_create_ticket(self.technician))
    
    def test_viewer_cannot_create(self):
        """VIEWER cannot create tickets."""
        self.assertFalse(can_create_ticket(self.viewer))


# ============================================================================
# Test Can Read Ticket
# ============================================================================

class TestCanReadTicket(TestFixtures):
    """Tests for can_read_ticket function."""
    
    def test_superadmin_can_read_any(self):
        """SUPERADMIN can read any ticket."""
        self.assertTrue(can_read_ticket(self.superadmin, self.ticket_by_technician))
    
    def test_manager_can_read_any(self):
        """MANAGER can read any ticket."""
        self.assertTrue(can_read_ticket(self.manager, self.ticket_by_viewer))
    
    def test_it_admin_can_read_any(self):
        """IT_ADMIN can read any ticket."""
        self.assertTrue(can_read_ticket(self.it_admin, self.ticket_by_technician))
    
    def test_technician_can_read_any(self):
        """TECHNICIAN can read any ticket."""
        self.assertTrue(can_read_ticket(self.technician, self.ticket_by_it_admin))
    
    def test_viewer_can_read_any(self):
        """VIEWER can read any ticket."""
        self.assertTrue(can_read_ticket(self.viewer, self.ticket_by_superadmin))


# ============================================================================
# Test Can Update Ticket
# ============================================================================

class TestCanUpdateTicket(TestFixtures):
    """Tests for can_update_ticket function."""
    
    # SUPERADMIN tests
    def test_superadmin_can_update_any(self):
        """SUPERADMIN can update any ticket."""
        self.assertTrue(can_update_ticket(self.superadmin, self.ticket_by_technician))
        self.assertTrue(can_update_ticket(self.superadmin, self.ticket_by_manager))
        self.assertTrue(can_update_ticket(self.superadmin, self.ticket_by_viewer))
    
    # MANAGER tests
    def test_manager_can_update_any(self):
        """MANAGER can update any ticket."""
        self.assertTrue(can_update_ticket(self.manager, self.ticket_by_it_admin))
        self.assertTrue(can_update_ticket(self.manager, self.ticket_by_technician))
        self.assertTrue(can_update_ticket(self.manager, self.ticket_by_superadmin))
    
    # IT_ADMIN tests
    def test_it_admin_can_update_ticket_by_technician(self):
        """IT_ADMIN can update ticket created by TECHNICIAN."""
        self.assertTrue(can_update_ticket(self.it_admin, self.ticket_by_technician))
    
    def test_it_admin_can_update_ticket_by_viewer(self):
        """IT_ADMIN can update ticket created by VIEWER."""
        self.assertTrue(can_update_ticket(self.it_admin, self.ticket_by_viewer))
    
    def test_it_admin_cannot_update_ticket_by_same_role(self):
        """IT_ADMIN cannot update ticket created by another IT_ADMIN."""
        self.assertFalse(can_update_ticket(self.it_admin, self.ticket_by_it_admin2))
    
    def test_it_admin_cannot_update_ticket_by_higher_role(self):
        """IT_ADMIN cannot update ticket created by MANAGER or SUPERADMIN."""
        self.assertFalse(can_update_ticket(self.it_admin, self.ticket_by_manager))
        self.assertFalse(can_update_ticket(self.it_admin, self.ticket_by_superadmin))
    
    # TECHNICIAN tests
    def test_technician_can_update_own_ticket(self):
        """TECHNICIAN can update their own ticket."""
        self.assertTrue(can_update_ticket(self.technician, self.ticket_by_technician))
    
    def test_technician_cannot_update_ticket_by_other_technician(self):
        """TECHNICIAN cannot update ticket created by another TECHNICIAN."""
        self.assertFalse(can_update_ticket(self.technician, self.ticket_by_technician2))
    
    def test_technician_cannot_update_ticket_by_higher_role(self):
        """TECHNICIAN cannot update ticket created by higher role."""
        self.assertFalse(can_update_ticket(self.technician, self.ticket_by_it_admin))
        self.assertFalse(can_update_ticket(self.technician, self.ticket_by_manager))
    
    # VIEWER tests
    def test_viewer_cannot_update_any(self):
        """VIEWER cannot update any ticket."""
        self.assertFalse(can_update_ticket(self.viewer, self.ticket_by_technician))
        self.assertFalse(can_update_ticket(self.viewer, self.ticket_by_viewer))
        self.assertFalse(can_update_ticket(self.viewer, self.ticket_by_superadmin))


# ============================================================================
# Test Can Delete Ticket
# ============================================================================

class TestCanDeleteTicket(TestFixtures):
    """Tests for can_delete_ticket function."""
    
    # SUPERADMIN tests
    def test_superadmin_can_delete_any(self):
        """SUPERADMIN can delete any ticket."""
        self.assertTrue(can_delete_ticket(self.superadmin, self.ticket_by_technician))
    
    # MANAGER tests
    def test_manager_can_delete_any(self):
        """MANAGER can delete any ticket."""
        self.assertTrue(can_delete_ticket(self.manager, self.ticket_by_it_admin))
    
    # IT_ADMIN tests
    def test_it_admin_can_delete_ticket_by_technician(self):
        """IT_ADMIN can delete ticket created by TECHNICIAN."""
        self.assertTrue(can_delete_ticket(self.it_admin, self.ticket_by_technician))
    
    def test_it_admin_cannot_delete_ticket_by_same_role(self):
        """IT_ADMIN cannot delete ticket created by another IT_ADMIN."""
        self.assertFalse(can_delete_ticket(self.it_admin, self.ticket_by_it_admin2))
    
    def test_it_admin_cannot_delete_ticket_by_higher_role(self):
        """IT_ADMIN cannot delete ticket created by higher role."""
        self.assertFalse(can_delete_ticket(self.it_admin, self.ticket_by_manager))
    
    # TECHNICIAN tests
    def test_technician_can_delete_own_ticket(self):
        """TECHNICIAN can delete their own ticket."""
        self.assertTrue(can_delete_ticket(self.technician, self.ticket_by_technician))
    
    def test_technician_cannot_delete_ticket_by_other_technician(self):
        """TECHNICIAN cannot delete ticket created by another TECHNICIAN."""
        self.assertFalse(can_delete_ticket(self.technician, self.ticket_by_technician2))
    
    # VIEWER tests
    def test_viewer_cannot_delete_any(self):
        """VIEWER cannot delete any ticket."""
        self.assertFalse(can_delete_ticket(self.viewer, self.ticket_by_viewer))


# ============================================================================
# Test Can Assign Ticket
# ============================================================================

class TestCanAssignTicket(TestFixtures):
    """Tests for can_assign_ticket function."""
    
    # SUPERADMIN tests
    def test_superadmin_can_assign_to_anyone(self):
        """SUPERADMIN can assign ticket to anyone."""
        self.assertTrue(can_assign_ticket(self.superadmin, self.ticket_by_technician, self.technician))
        self.assertTrue(can_assign_ticket(self.superadmin, self.ticket_by_technician, self.it_admin))
    
    # MANAGER tests
    def test_manager_can_assign_to_anyone(self):
        """MANAGER can assign ticket to anyone."""
        self.assertTrue(can_assign_ticket(self.manager, self.ticket_by_it_admin, self.technician))
    
    # IT_ADMIN tests
    def test_it_admin_can_assign_to_anyone(self):
        """IT_ADMIN can assign ticket to anyone."""
        self.assertTrue(can_assign_ticket(self.it_admin, self.ticket_by_technician, self.manager))
        self.assertTrue(can_assign_ticket(self.it_admin, self.ticket_by_technician, self.technician))
    
    # TECHNICIAN tests
    def test_technician_can_assign_to_self(self):
        """TECHNICIAN can assign ticket to themselves."""
        self.assertTrue(can_assign_ticket(self.technician, self.ticket_by_technician, self.technician))
    
    def test_technician_cannot_assign_to_other(self):
        """TECHNICIAN cannot assign ticket to another user."""
        self.assertFalse(can_assign_ticket(self.technician, self.ticket_by_technician, self.it_admin))
        self.assertFalse(can_assign_ticket(self.technician, self.ticket_by_technician, self.technician2))
    
    def test_technician_cannot_assign_others_ticket(self):
        """TECHNICIAN cannot assign ticket created by another TECHNICIAN (even to self)."""
        self.assertFalse(can_assign_ticket(self.technician, self.ticket_by_technician2, self.technician))
    
    # VIEWER tests
    def test_viewer_cannot_assign_any(self):
        """VIEWER cannot assign any ticket."""
        self.assertFalse(can_assign_ticket(self.viewer, self.ticket_by_technician, self.viewer))
        self.assertFalse(can_assign_ticket(self.viewer, self.ticket_by_viewer, self.viewer))


# ============================================================================
# Test Can Close Ticket
# ============================================================================

class TestCanCloseTicket(TestFixtures):
    """Tests for can_close_ticket function."""
    
    # SUPERADMIN tests
    def test_superadmin_can_close_any(self):
        """SUPERADMIN can close any ticket."""
        self.assertTrue(can_close_ticket(self.superadmin, self.ticket_by_technician))
    
    # MANAGER tests
    def test_manager_can_close_any(self):
        """MANAGER can close any ticket."""
        self.assertTrue(can_close_ticket(self.manager, self.ticket_by_it_admin))
    
    # IT_ADMIN tests
    def test_it_admin_can_close_ticket_by_technician(self):
        """IT_ADMIN can close ticket created by TECHNICIAN."""
        self.assertTrue(can_close_ticket(self.it_admin, self.ticket_by_technician))
    
    def test_it_admin_cannot_close_ticket_by_same_role(self):
        """IT_ADMIN cannot close ticket created by another IT_ADMIN."""
        self.assertFalse(can_close_ticket(self.it_admin, self.ticket_by_it_admin2))
    
    def test_it_admin_cannot_close_ticket_by_higher_role(self):
        """IT_ADMIN cannot close ticket created by higher role."""
        self.assertFalse(can_close_ticket(self.it_admin, self.ticket_by_manager))
    
    # TECHNICIAN tests
    def test_technician_can_close_own_ticket(self):
        """TECHNICIAN can close their own ticket."""
        self.assertTrue(can_close_ticket(self.technician, self.ticket_by_technician))
    
    def test_technician_cannot_close_ticket_by_other_technician(self):
        """TECHNICIAN cannot close ticket created by another TECHNICIAN."""
        self.assertFalse(can_close_ticket(self.technician, self.ticket_by_technician2))
    
    # VIEWER tests
    def test_viewer_cannot_close_any(self):
        """VIEWER cannot close any ticket."""
        self.assertFalse(can_close_ticket(self.viewer, self.ticket_by_viewer))


# ============================================================================
# Test Get Ticket Permissions
# ============================================================================

class TestGetTicketPermissions(TestFixtures):
    """Tests for get_ticket_permissions function."""
    
    def test_permissions_structure(self):
        """get_ticket_permissions returns correct structure."""
        perms = get_ticket_permissions(self.technician, self.ticket_by_technician)
        
        self.assertIn('can_create', perms)
        self.assertIn('can_read', perms)
        self.assertIn('can_update', perms)
        self.assertIn('can_delete', perms)
        self.assertIn('can_assign', perms)
        self.assertIn('can_close', perms)
    
    def test_permissions_consistency_self_ticket(self):
        """Permissions are consistent for technician on own ticket."""
        perms = get_ticket_permissions(self.technician, self.ticket_by_technician)
        
        # TECHNICIAN can create
        self.assertTrue(perms['can_create'])
        # Everyone can read
        self.assertTrue(perms['can_read'])
        # TECHNICIAN can update own
        self.assertTrue(perms['can_update'])
        # TECHNICIAN can delete own
        self.assertTrue(perms['can_delete'])
        # TECHNICIAN can assign to self
        self.assertTrue(perms['can_assign'])
        # TECHNICIAN can close own
        self.assertTrue(perms['can_close'])
    
    def test_permissions_consistency_viewer(self):
        """Permissions are consistent for VIEWER."""
        perms = get_ticket_permissions(self.viewer, self.ticket_by_technician)
        
        # VIEWER cannot create
        self.assertFalse(perms['can_create'])
        # Everyone can read
        self.assertTrue(perms['can_read'])
        # VIEWER cannot update
        self.assertFalse(perms['can_update'])
        # VIEWER cannot delete
        self.assertFalse(perms['can_delete'])
        # VIEWER cannot assign
        self.assertFalse(perms['can_assign'])
        # VIEWER cannot close
        self.assertFalse(perms['can_close'])
    
    def test_permissions_consistency_superadmin(self):
        """Permissions are consistent for SUPERADMIN."""
        perms = get_ticket_permissions(self.superadmin, self.ticket_by_technician)
        
        # SUPERADMIN can create
        self.assertTrue(perms['can_create'])
        # Everyone can read
        self.assertTrue(perms['can_read'])
        # SUPERADMIN can update
        self.assertTrue(perms['can_update'])
        # SUPERADMIN can delete
        self.assertTrue(perms['can_delete'])
        # SUPERADMIN can assign
        self.assertTrue(perms['can_assign'])
        # SUPERADMIN can close
        self.assertTrue(perms['can_close'])
    
    def test_permissions_consistency_it_admin_on_lower_role_ticket(self):
        """Permissions are consistent for IT_ADMIN on TECHNICIAN's ticket."""
        perms = get_ticket_permissions(self.it_admin, self.ticket_by_technician)
        
        # IT_ADMIN can create
        self.assertTrue(perms['can_create'])
        # Everyone can read
        self.assertTrue(perms['can_read'])
        # IT_ADMIN can update lower role ticket
        self.assertTrue(perms['can_update'])
        # IT_ADMIN can delete lower role ticket
        self.assertTrue(perms['can_delete'])
        # IT_ADMIN can assign
        self.assertTrue(perms['can_assign'])
        # IT_ADMIN can close lower role ticket
        self.assertTrue(perms['can_close'])


# ============================================================================
# Test Can Resolve Ticket
# ============================================================================

class FakeTicketWithStatus(FakeTicket):
    """Fake ticket with status for testing resolve/reopen permissions."""

    def __init__(self, ticket_id: int, title: str, created_by: FakeUser, status: str = 'OPEN', assigned_to: FakeUser = None):
        super().__init__(ticket_id, title, created_by, assigned_to)
        self.status = status


class TestCanResolveTicket(TestFixtures):
    """Tests for can_resolve_ticket function."""

    def setUp(self):
        """Set up test fixtures with status-aware tickets."""
        super().setUp()
        # Tickets with different statuses
        self.resolved_ticket = FakeTicketWithStatus(10, 'Resolved Ticket', self.technician, status='RESOLVED')
        self.open_ticket = FakeTicketWithStatus(11, 'Open Ticket', self.technician, status='OPEN')
        self.closed_ticket = FakeTicketWithStatus(12, 'Closed Ticket', self.technician, status='CLOSED')

    # SUPERADMIN tests
    def test_superadmin_can_resolve_any(self):
        """SUPERADMIN can resolve any ticket."""
        self.assertTrue(can_resolve_ticket(self.superadmin, self.open_ticket))
        self.assertTrue(can_resolve_ticket(self.superadmin, self.resolved_ticket))

    # MANAGER tests
    def test_manager_can_resolve_any(self):
        """MANAGER can resolve any ticket."""
        self.assertTrue(can_resolve_ticket(self.manager, self.open_ticket))

    # IT_ADMIN tests
    def test_it_admin_can_resolve_ticket_by_technician(self):
        """IT_ADMIN can resolve ticket created by TECHNICIAN."""
        self.assertTrue(can_resolve_ticket(self.it_admin, self.open_ticket))

    def test_it_admin_cannot_resolve_ticket_by_same_role(self):
        """IT_ADMIN cannot resolve ticket created by another IT_ADMIN."""
        ticket_by_it_admin2 = FakeTicketWithStatus(13, 'Ticket by IT_ADMIN2', self.it_admin2, status='OPEN')
        self.assertFalse(can_resolve_ticket(self.it_admin, ticket_by_it_admin2))

    # TECHNICIAN tests
    def test_technician_can_resolve_own_ticket(self):
        """TECHNICIAN can resolve their own ticket."""
        self.assertTrue(can_resolve_ticket(self.technician, self.open_ticket))

    def test_technician_cannot_resolve_ticket_by_other_technician(self):
        """TECHNICIAN cannot resolve ticket created by another TECHNICIAN."""
        ticket_by_tech2 = FakeTicketWithStatus(14, 'Ticket by TECH2', self.technician2, status='OPEN')
        self.assertFalse(can_resolve_ticket(self.technician, ticket_by_tech2))

    # VIEWER tests
    def test_viewer_cannot_resolve_any(self):
        """VIEWER cannot resolve any ticket."""
        self.assertFalse(can_resolve_ticket(self.viewer, self.open_ticket))


# ============================================================================
# Test Can Reopen Ticket
# ============================================================================

class TestCanReopenTicket(TestFixtures):
    """Tests for can_reopen_ticket function."""

    def setUp(self):
        """Set up test fixtures with status-aware tickets."""
        super().setUp()
        # Tickets with different statuses
        self.resolved_ticket = FakeTicketWithStatus(10, 'Resolved Ticket', self.technician, status='RESOLVED')
        self.open_ticket = FakeTicketWithStatus(11, 'Open Ticket', self.technician, status='OPEN')
        self.closed_ticket = FakeTicketWithStatus(12, 'Closed Ticket', self.technician, status='CLOSED')

    # Status constraint tests
    def test_cannot_reopen_non_resolved_ticket(self):
        """Cannot reopen ticket that is not in RESOLVED status."""
        self.assertFalse(can_reopen_ticket(self.superadmin, self.open_ticket))
        self.assertFalse(can_reopen_ticket(self.superadmin, self.closed_ticket))

    # SUPERADMIN tests
    def test_superadmin_can_reopen_resolved_ticket(self):
        """SUPERADMIN can reopen any RESOLVED ticket."""
        self.assertTrue(can_reopen_ticket(self.superadmin, self.resolved_ticket))

    def test_superadmin_cannot_reopen_non_resolved(self):
        """SUPERADMIN cannot reopen non-RESOLVED tickets."""
        self.assertFalse(can_reopen_ticket(self.superadmin, self.open_ticket))
        self.assertFalse(can_reopen_ticket(self.superadmin, self.closed_ticket))

    # MANAGER tests
    def test_manager_can_reopen_resolved_ticket(self):
        """MANAGER can reopen any RESOLVED ticket."""
        self.assertTrue(can_reopen_ticket(self.manager, self.resolved_ticket))

    # IT_ADMIN tests
    def test_it_admin_can_reopen_ticket_by_technician(self):
        """IT_ADMIN can reopen RESOLVED ticket created by TECHNICIAN."""
        self.assertTrue(can_reopen_ticket(self.it_admin, self.resolved_ticket))

    def test_it_admin_cannot_reopen_ticket_by_same_role(self):
        """IT_ADMIN cannot reopen RESOLVED ticket created by another IT_ADMIN."""
        ticket_by_it_admin2 = FakeTicketWithStatus(13, 'Ticket by IT_ADMIN2', self.it_admin2, status='RESOLVED')
        self.assertFalse(can_reopen_ticket(self.it_admin, ticket_by_it_admin2))

    def test_it_admin_cannot_reopen_ticket_by_higher_role(self):
        """IT_ADMIN cannot reopen RESOLVED ticket created by MANAGER or SUPERADMIN."""
        ticket_by_manager = FakeTicketWithStatus(14, 'Ticket by MANAGER', self.manager, status='RESOLVED')
        ticket_by_superadmin = FakeTicketWithStatus(15, 'Ticket by SUPERADMIN', self.superadmin, status='RESOLVED')
        self.assertFalse(can_reopen_ticket(self.it_admin, ticket_by_manager))
        self.assertFalse(can_reopen_ticket(self.it_admin, ticket_by_superadmin))

    # TECHNICIAN tests
    def test_technician_can_reopen_own_resolved_ticket(self):
        """TECHNICIAN can reopen their own RESOLVED ticket."""
        self.assertTrue(can_reopen_ticket(self.technician, self.resolved_ticket))

    def test_technician_cannot_reopen_ticket_by_other_technician(self):
        """TECHNICIAN cannot reopen RESOLVED ticket created by another TECHNICIAN."""
        ticket_by_tech2 = FakeTicketWithStatus(16, 'Ticket by TECH2', self.technician2, status='RESOLVED')
        self.assertFalse(can_reopen_ticket(self.technician, ticket_by_tech2))

    def test_technician_cannot_reopen_ticket_by_higher_role(self):
        """TECHNICIAN cannot reopen RESOLVED ticket created by higher role."""
        ticket_by_it_admin = FakeTicketWithStatus(17, 'Ticket by IT_ADMIN', self.it_admin, status='RESOLVED')
        ticket_by_manager = FakeTicketWithStatus(18, 'Ticket by MANAGER', self.manager, status='RESOLVED')
        self.assertFalse(can_reopen_ticket(self.technician, ticket_by_it_admin))
        self.assertFalse(can_reopen_ticket(self.technician, ticket_by_manager))

    def test_technician_cannot_reopen_non_resolved_ticket(self):
        """TECHNICIAN cannot reopen non-RESOLVED tickets (even own)."""
        own_open_ticket = FakeTicketWithStatus(19, 'Own Open Ticket', self.technician, status='OPEN')
        self.assertFalse(can_reopen_ticket(self.technician, own_open_ticket))

    # VIEWER tests
    def test_viewer_cannot_reopen_any(self):
        """VIEWER cannot reopen any ticket."""
        self.assertFalse(can_reopen_ticket(self.viewer, self.resolved_ticket))


# ============================================================================
# Test Can Assign Self
# ============================================================================

class TestCanAssignSelf(TestFixtures):
    """Tests for can_assign_self function."""

    def setUp(self):
        """Set up test fixtures with status-aware tickets."""
        super().setUp()
        # Tickets with different assignments
        self.unassigned_ticket = FakeTicketWithStatus(20, 'Unassigned Ticket', self.technician, status='OPEN')
        self.assigned_to_self = FakeTicketWithStatus(21, 'Assigned to Self', self.technician, status='OPEN', assigned_to=self.technician)
        self.assigned_to_other = FakeTicketWithStatus(22, 'Assigned to Other', self.technician, status='OPEN', assigned_to=self.it_admin)

    # SUPERADMIN tests
    def test_superadmin_can_assign_self_to_any(self):
        """SUPERADMIN can assign any ticket to themselves."""
        self.assertTrue(can_assign_self(self.superadmin, self.unassigned_ticket))
        self.assertTrue(can_assign_self(self.superadmin, self.assigned_to_other))

    # MANAGER tests
    def test_manager_can_assign_self_to_any(self):
        """MANAGER can assign any ticket to themselves."""
        self.assertTrue(can_assign_self(self.manager, self.unassigned_ticket))

    # IT_ADMIN tests
    def test_it_admin_can_assign_self_to_any(self):
        """IT_ADMIN can assign any ticket to themselves."""
        self.assertTrue(can_assign_self(self.it_admin, self.unassigned_ticket))

    # TECHNICIAN tests
    def test_technician_can_assign_own_unassigned_ticket_to_self(self):
        """TECHNICIAN can assign their own unassigned ticket to themselves."""
        self.assertTrue(can_assign_self(self.technician, self.unassigned_ticket))

    def test_technician_cannot_assign_own_ticket_already_assigned_to_self(self):
        """TECHNICIAN cannot assign ticket already assigned to themselves."""
        self.assertFalse(can_assign_self(self.technician, self.assigned_to_self))

    def test_technician_cannot_assign_ticket_assigned_to_other(self):
        """TECHNICIAN cannot assign ticket assigned to another user."""
        self.assertFalse(can_assign_self(self.technician, self.assigned_to_other))

    def test_technician_cannot_assign_others_ticket(self):
        """TECHNICIAN cannot assign ticket created by another TECHNICIAN."""
        ticket_by_tech2 = FakeTicketWithStatus(23, 'Ticket by TECH2', self.technician2, status='OPEN')
        self.assertFalse(can_assign_self(self.technician, ticket_by_tech2))

    def test_technician_cannot_assign_ticket_by_higher_role(self):
        """TECHNICIAN cannot assign ticket created by higher role."""
        ticket_by_it_admin = FakeTicketWithStatus(24, 'Ticket by IT_ADMIN', self.it_admin, status='OPEN')
        self.assertFalse(can_assign_self(self.technician, ticket_by_it_admin))

    # VIEWER tests
    def test_viewer_cannot_assign_any(self):
        """VIEWER cannot assign any ticket to themselves."""
        self.assertFalse(can_assign_self(self.viewer, self.unassigned_ticket))


# ============================================================================
# Test Integration Scenarios
# ============================================================================

class TestIntegrationScenarios(TestFixtures):
    """Integration-style tests for complete scenarios."""

    def test_full_hierarchy_scenario(self):
        """Test a complete hierarchy scenario with all role combinations."""
        # SUPERADMIN can do everything on any ticket
        for ticket in [self.ticket_by_superadmin, self.ticket_by_manager,
                       self.ticket_by_it_admin, self.ticket_by_technician,
                       self.ticket_by_viewer]:
            self.assertTrue(can_update_ticket(self.superadmin, ticket))
            self.assertTrue(can_delete_ticket(self.superadmin, ticket))
            self.assertTrue(can_close_ticket(self.superadmin, ticket))

        # MANAGER can do everything on any ticket
        for ticket in [self.ticket_by_superadmin, self.ticket_by_manager,
                       self.ticket_by_it_admin, self.ticket_by_technician,
                       self.ticket_by_viewer]:
            self.assertTrue(can_update_ticket(self.manager, ticket))
            self.assertTrue(can_delete_ticket(self.manager, ticket))
            self.assertTrue(can_close_ticket(self.manager, ticket))

        # IT_ADMIN can only act on tickets by TECHNICIAN or VIEWER
        self.assertTrue(can_update_ticket(self.it_admin, self.ticket_by_technician))
        self.assertTrue(can_update_ticket(self.it_admin, self.ticket_by_viewer))
        self.assertFalse(can_update_ticket(self.it_admin, self.ticket_by_it_admin))
        self.assertFalse(can_update_ticket(self.it_admin, self.ticket_by_manager))
        self.assertFalse(can_update_ticket(self.it_admin, self.ticket_by_superadmin))

    def test_technician_permission_boundaries(self):
        """Test TECHNICIAN permission boundaries."""
        # TECHNICIAN's own ticket - can do everything
        self.assertTrue(can_update_ticket(self.technician, self.ticket_by_technician))
        self.assertTrue(can_delete_ticket(self.technician, self.ticket_by_technician))
        self.assertTrue(can_close_ticket(self.technician, self.ticket_by_technician))

        # Another TECHNICIAN's ticket - cannot do anything
        self.assertFalse(can_update_ticket(self.technician, self.ticket_by_technician2))
        self.assertFalse(can_delete_ticket(self.technician, self.ticket_by_technician2))
        self.assertFalse(can_close_ticket(self.technician, self.ticket_by_technician2))

        # Higher role's ticket - cannot do anything
        self.assertFalse(can_update_ticket(self.technician, self.ticket_by_it_admin))
        self.assertFalse(can_delete_ticket(self.technician, self.ticket_by_manager))


if __name__ == '__main__':
    unittest.main()

