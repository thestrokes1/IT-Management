#!/usr/bin/env python
"""
Standalone test runner for domain tests.
Run from the backend directory: python run_domain_tests.py
"""

import sys
sys.path.insert(0, '.')

import unittest

# Import and run core roles tests
from apps.core.tests.domain.test_roles import (
    TestRoleRanksValues, TestManagerEqualsSuperadmin, TestViewerIsLowest,
    TestHasHigherRole, TestHasStrictlyHigherRole, TestCompareRoles,
    TestRoleHierarchy, TestAdminRoleChecks
)

# Import and run authorization tests
from apps.core.tests.domain.test_authorization import TestCanModifyResource, TestAuthorizationEdgeCases

# Import and run ticket authority tests
from apps.tickets.tests.domain.test_ticket_authority import (
    TestCanCreateTicket, TestCanReadTicket, TestCanUpdateTicket,
    TestCanDeleteTicket, TestCanAssignTicket, TestCanCloseTicket,
    TestGetTicketPermissions, TestIntegrationScenarios
)

# Import and run user authority tests
from apps.users.tests.domain.test_user_authority import (
    TestCanViewUser, TestCanUpdateUser, TestCanChangeRole,
    TestCanDeactivateUser, TestCanDeleteUser, TestGetUserPermissions,
    TestAssertionHelpers
)

def main():
    print("=" * 70)
    print("DOMAIN TESTS SUITE")
    print("=" * 70)
    print()
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestRoleRanksValues))
    suite.addTests(loader.loadTestsFromTestCase(TestManagerEqualsSuperadmin))
    suite.addTests(loader.loadTestsFromTestCase(TestViewerIsLowest))
    suite.addTests(loader.loadTestsFromTestCase(TestHasHigherRole))
    suite.addTests(loader.loadTestsFromTestCase(TestHasStrictlyHigherRole))
    suite.addTests(loader.loadTestsFromTestCase(TestCompareRoles))
    suite.addTests(loader.loadTestsFromTestCase(TestRoleHierarchy))
    suite.addTests(loader.loadTestsFromTestCase(TestAdminRoleChecks))
    suite.addTests(loader.loadTestsFromTestCase(TestCanModifyResource))
    suite.addTests(loader.loadTestsFromTestCase(TestAuthorizationEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestCanCreateTicket))
    suite.addTests(loader.loadTestsFromTestCase(TestCanReadTicket))
    suite.addTests(loader.loadTestsFromTestCase(TestCanUpdateTicket))
    suite.addTests(loader.loadTestsFromTestCase(TestCanDeleteTicket))
    suite.addTests(loader.loadTestsFromTestCase(TestCanAssignTicket))
    suite.addTests(loader.loadTestsFromTestCase(TestCanCloseTicket))
    suite.addTests(loader.loadTestsFromTestCase(TestGetTicketPermissions))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    
    # Add user authority tests
    suite.addTests(loader.loadTestsFromTestCase(TestCanViewUser))
    suite.addTests(loader.loadTestsFromTestCase(TestCanUpdateUser))
    suite.addTests(loader.loadTestsFromTestCase(TestCanChangeRole))
    suite.addTests(loader.loadTestsFromTestCase(TestCanDeactivateUser))
    suite.addTests(loader.loadTestsFromTestCase(TestCanDeleteUser))
    suite.addTests(loader.loadTestsFromTestCase(TestGetUserPermissions))
    suite.addTests(loader.loadTestsFromTestCase(TestAssertionHelpers))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print("=" * 70)
    
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(main())

