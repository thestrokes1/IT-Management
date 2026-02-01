# RBAC Implementation Plan

## Phase 1: Permission Mapper Layer
- [ ] Create `backend/apps/frontend/permissions_mapper.py` with UI permission translation functions

## Phase 2: Update Views
- [ ] Update `tickets.py` - Add `permissions_by_ticket` computation using mapper
- [ ] Update `assets.py` - Ensure consistent UI flag structure
- [ ] Update `projects.py` - Ensure consistent UI flag structure  
- [ ] Update `users.py` - Ensure consistent UI flag structure

## Phase 3: Update Templates
- [ ] Update `tickets.html` - Use UI flags (`can_update`, `can_delete`, `can_self_assign`)
- [ ] Update `assets.html` - Use UI flags with `assigned_to_me`
- [ ] Update `projects.html` - Use UI flags
- [ ] Update `users.html` - Use UI flags

## Phase 4: Update Tests
- [ ] Update `test_ticket_permissions.py` - Assert UI flags match authority
- [ ] Update `test_asset_permissions.py` - Assert UI flags match authority
- [ ] Update `test_project_permissions.py` - Assert UI flags match authority
- [ ] Update `test_user_permissions.py` - Assert UI flags match authority

## UI Permission Flags Contract (Authoritative)
```python
{
    "can_view": bool,           # authority.can_view(user, obj)
    "can_update": bool,         # authority.can_edit(user, obj) - UI alias
    "can_delete": bool,         # authority.can_delete(user, obj)
    "can_assign": bool,         # authority.can_assign(user, obj)
    "can_unassign": bool,       # authority.can_unassign(user, obj)
    "can_self_assign": bool,    # authority.can_assign_to_self(user, obj) - UI alias
    "assigned_to_me": bool,     # obj.assigned_to_id == user.id
}
```

## Key Rules
- Authority methods remain unchanged (can_view, can_edit, can_delete, can_assign, can_unassign, can_assign_to_self)
- Views translate domain permissions to UI flags
- Templates use ONLY UI flags (no role checks, no authority calls)
- Tests verify UI flags == authority decisions

