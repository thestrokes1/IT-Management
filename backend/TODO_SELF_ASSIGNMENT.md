# TODO: Technician Self-Assignment Implementation

## Step 1: Models - Add assignment_status field
- [ ] Update `tickets/models.py` - Add `assignment_status` field to Ticket model
- [ ] Update `assets/models.py` - Add `assignment_status` field to Asset model
- [ ] Add properties for assignment visibility

## Step 2: Domain Services - Update authorization
- [ ] Update `tickets/domain/services/ticket_authority.py`:
  - Add `can_self_assign_ticket()` function
  - Add `can_reassign_ticket()` function  
  - Add `can_edit_assigned_ticket()` function
  - Update `can_assign_ticket()` for new rules
- [ ] Update `assets/domain/services/asset_authority.py`:
  - Add `can_self_assign_asset()` function
  - Add `can_reassign_asset()` function
  - Add `can_edit_assigned_asset()` function

## Step 3: Domain Events - Add asset events
- [ ] Create `assets/domain/events.py` with AssetAssigned and AssetUnassigned events
- [ ] Register event handlers in application setup

## Step 4: Application Layer - Create use cases
- [ ] Create `tickets/application/assign_ticket_to_self.py`
- [ ] Create `assets/application/assign_asset_to_self.py`
- [ ] Update `tickets/application/update_ticket.py` with assignment rules
- [ ] Create `assets/application/update_asset.py`

## Step 5: Permissions - Add self-assignment permissions
- [ ] Update `tickets/permissions.py`:
  - Add `CanSelfAssign` class
  - Add `IsAssignedTechnician` class
  - Add `CanReassign` class
- [ ] Update `assets/permissions.py`:
  - Add `CanSelfAssignAsset` class
  - Add `CanReassignAsset` class

## Step 6: Serializers - Expose assignment status
- [ ] Update `tickets/serializers.py`:
  - Add `assignment_status` field
  - Add `assigned_technician` field
  - Add `can_self_assign` computed field
- [ ] Update `assets/serializers.py`:
  - Add `assignment_status` field
  - Add `assigned_technician` field
  - Add `can_self_assign` computed field

## Step 7: Views & URLs - Add assign-self endpoints
- [ ] Update `tickets/urls.py` - Add `assign-self/` action
- [ ] Update `tickets/views.py` - Add assign-self endpoint logic
- [ ] Update `assets/urls.py` - Add `assign-self/` action
- [ ] Update `assets/views.py` - Add assign-self endpoint logic

## Step 8: Activity Logging - Add asset assignment actions
- [ ] Update `core/services/activity_logger.py` - Add asset assignment actions (already exists)

## Testing
- [ ] Run existing tests to verify no regressions
- [ ] Test self-assignment flow manually

