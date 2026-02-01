# Implementation Plan: Ticket Unassignment Feature

## Goal
Add ticket unassignment functionality to match the existing asset assignment/unassignment pattern.

## Status: ✅ COMPLETED

## Tasks Completed

### 1. Added `ticket_unassign_self` view function
**File:** `backend/apps/frontend/views/tickets.py`
- Similar to `asset_unassign_self` in assets.py
- Uses domain authority for permission check (`can_unassign_self`)
- Performs unassignment and emits domain event (`emit_ticket_unassigned`)

### 2. URL pattern (already existed)
**File:** `backend/apps/frontend/urls.py`
- Route: `path('tickets/<int:ticket_id>/unassign-self/', ticket_unassign_self, name='ticket_unassign_self')`

### 3. Added unassign button in ticket_detail.html
**File:** `backend/templates/frontend/ticket_detail.html`
- Added "Cancel assignment" button for assigned user
- Shows when `permissions.assigned_to_me` and `permissions.can_unassign` are True
- Orange button matching the asset_detail.html style

### 4. Added unassign row action in tickets.html
**File:** `backend/templates/frontend/tickets.html`
- Added unassign link in the desktop table actions column
- Added unassign icon button in the mobile card view
- Similar to the unassign row action in assets.html

## Files Modified
1. `backend/apps/frontend/views/tickets.py` - Added `ticket_unassign_self` view function
2. `backend/templates/frontend/ticket_detail.html` - Added UI unassign button
3. `backend/templates/frontend/tickets.html` - Added row unassign actions

## Dependencies (Already Existed)
- Domain authority already has `can_unassign` and `assert_can_unassign` functions ✓
- Application layer has `UnassignTicket` use case ✓
- URL pattern already exists ✓

## Permission Rules (from domain authority)
- SUPERADMIN, MANAGER: can always unassign any ticket
- IT_ADMIN: can always unassign any ticket
- TECHNICIAN: can only unassign if ticket.assigned_to == user
- VIEWER: cannot unassign

## Testing Notes
The unassign functionality should be tested with:
1. Technician self-assigned to a ticket → should be able to unassign
2. Technician assigned by admin → should be able to unassign (since assigned_to == user)
3. Technician trying to unassign someone else's ticket → should be denied
4. Admin trying to unassign any ticket → should be allowed

