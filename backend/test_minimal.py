#!/usr/bin/env python
"""Minimal test to verify ticket authority works."""

import sys
sys.path.insert(0, '.')

from apps.tickets.domain.services.ticket_authority import (
    can_create_ticket, can_read_ticket, can_update_ticket,
    can_delete_ticket, can_assign_ticket, can_close_ticket
)
from apps.core.domain.roles import ROLE_RANKS, has_higher_role, has_strictly_higher_role

# Fake classes
class FakeUser:
    def __init__(self, uid, name, role):
        self.id, self.username, self.role = uid, name, role
    def __eq__(self, o): return isinstance(o, FakeUser) and self.id == o.id
    def __hash__(self): return hash(self.id)

class FakeTicket:
    def __init__(self, tid, title, creator):
        self.id, self.title, self.created_by = tid, title, creator
        self.created_by_id = creator.id

# Setup
sa = FakeUser(1, 'sa', 'SUPERADMIN')
mgr = FakeUser(2, 'mgr', 'MANAGER')
admin = FakeUser(3, 'admin', 'IT_ADMIN')
tech = FakeUser(4, 'tech', 'TECHNICIAN')
viewer = FakeUser(5, 'viewer', 'VIEWER')
tech2 = FakeUser(6, 'tech2', 'TECHNICIAN')

ticket_tech = FakeTicket(5, 'TECH', tech)
ticket_tech2 = FakeTicket(6, 'TECH2', tech2)

errors = []

def test(name, cond, expected):
    if cond != expected:
        errors.append(f"FAIL: {name} - expected {expected}, got {cond}")

print("Running minimal tests...")

# Create
test("can_create_ticket(sa)", can_create_ticket(sa), True)
test("can_create_ticket(viewer)", can_create_ticket(viewer), False)

# Read - everyone can read
test("can_read_ticket(viewer, ticket_tech)", can_read_ticket(viewer, ticket_tech), True)

# Update
test("can_update_ticket(sa, ticket_tech)", can_update_ticket(sa, ticket_tech), True)
test("can_update_ticket(tech, ticket_tech)", can_update_ticket(tech, ticket_tech), True)
test("can_update_ticket(tech, ticket_tech2)", can_update_ticket(tech, ticket_tech2), False)
test("can_update_ticket(viewer, ticket_tech)", can_update_ticket(viewer, ticket_tech), False)

# Delete
test("can_delete_ticket(sa, ticket_tech)", can_delete_ticket(sa, ticket_tech), True)
test("can_delete_ticket(tech, ticket_tech)", can_delete_ticket(tech, ticket_tech), True)
test("can_delete_ticket(tech, ticket_tech2)", can_delete_ticket(tech, ticket_tech2), False)

# Assign
test("can_assign_ticket(sa, ticket_tech, tech)", can_assign_ticket(sa, ticket_tech, tech), True)
test("can_assign_ticket(tech, ticket_tech, tech)", can_assign_ticket(tech, ticket_tech, tech), True)
test("can_assign_ticket(tech, ticket_tech2, tech)", can_assign_ticket(tech, ticket_tech2, tech), False)

# Close
test("can_close_ticket(sa, ticket_tech)", can_close_ticket(sa, ticket_tech), True)
test("can_close_ticket(tech, ticket_tech)", can_close_ticket(tech, ticket_tech), True)
test("can_close_ticket(tech, ticket_tech2)", can_close_ticket(tech, ticket_tech2), False)

print()
if errors:
    print("ERRORS FOUND:")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED!")
    sys.exit(0)

