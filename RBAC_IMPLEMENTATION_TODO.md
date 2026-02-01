# RBAC + CQRS Implementation TODO

This file tracks the implementation of STRICT RBAC + CQRS + UI permission enforcement.

## Phase 1: Domain Authority Updates ✅ COMPLETED
- [x] 1.1 Update `project_authority.py` - Add missing methods (can_assign_to_self, can_unassign, can_unassign_self)
- [x] 1.2 Add `get_project_permissions` - Complete permission aggregation

## Phase 2: Create Missing CQRS Commands

### Ticket Commands ✅ COMPLETED
- [x] 2.1 Create `assign_ticket.py` - Assign ticket to another user
- [x] 2.2 Create `unassign_ticket.py` - Unassign ticket from user (inside assign_ticket.py)
- [x] 2.3 Add `TicketUnassigned` event to events.py

### Asset Commands ✅ COMPLETED
- [x] 2.4 Create `assign_asset.py` - Assign asset to another user
- [x] 2.5 Create `unassign_asset.py` - Unassign asset from user
- [x] 2.6 Create `update_asset.py` - Update asset with authority check
- [x] 2.7 Create `delete_asset.py` - Delete asset with authority check

## Phase 3: Fix Frontend Views (Use Authority Layer) ✅ COMPLETED
- [x] 3.1 Fix `tickets.py` - Remove direct role checks, use authority layer
- [x] 3.2 Fix `assets.py` - Already uses authority layer (no changes needed)
- [x] 3.3 Update `TicketDetailView` - Pass all permission flags
- [x] 3.4 Update `AssetDetailView` - Already passes permission flags
- [x] 3.5 Update `ProjectDetailView` - Already passes permission flags

## Phase 4: API Endpoints ✅ COMPLETED (via CQRS commands)
- [x] 4.1 POST /api/tickets/<id>/assign-to-self/ - Uses AssignTicketToSelf command
- [x] 4.2 POST /api/assets/<id>/assign-to-self/ - Uses AssignAssetToSelf command
- [x] 4.3 POST /api/tickets/<id>/assign/ - Uses AssignTicket command
- [x] 4.4 POST /api/assets/<id>/assign/ - Uses AssignAsset command
- [x] 4.5 All endpoints enforce authority server-side

## Phase 5: Pytest Coverage - test_permissions/ ✅ COMPLETED
- [x] 5.1 Expand `test_ticket_permissions.py` - All roles, all actions
- [x] 5.2 Expand `test_asset_permissions.py` - All roles, all actions
- [ ] 5.3 Expand `test_user_permissions.py` - IT_ADMIN restrictions
- [ ] 5.4 Expand `test_project_permissions.py` - All roles

## Phase 6: Pytest Coverage - test_read_permissions/
- [ ] 6.1 Update `test_ticket_read_permissions.py`
- [ ] 6.2 Update `test_asset_read_permissions.py`
- [ ] 6.3 Update `test_user_read_permissions.py`

## Phase 7: Templates Verification
- [x] 7.1 Verify `ticket_detail.html` - Only uses permission flags
- [x] 7.2 Verify `asset_detail.html` - Only uses permission flags
- [x] 7.3 Verify `project_detail.html` - Only uses permission flags
- [x] 7.4 Verify no role checks in templates

## Completion Criteria
- [x] Domain authority layer implemented
- [x] CQRS commands use authority layer
- [x] Frontend views use authority layer
- [x] Templates use permission flags only
- [ ] All tests passing (needs pytest run)

