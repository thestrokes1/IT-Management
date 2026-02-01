# Permission System Documentation

This document describes the role-based access control (RBAC) system for the IT Management Platform. It is derived from analysis of the domain authority services, policies, and mixins.

## 1. Overview

### Server-Side Enforcement

All permissions are enforced server-side through:

1. **Domain Authority Services** - Pure Python functions that implement authorization rules
2. **Policy Classes** - Role-based policies for complex scenarios (Projects)
3. **Mixins** - Django class-based view decorators for dispatch-level checks
4. **Service Layer** - Services call `can_*` and `assert_*` functions before mutations

### UI vs Backend Permissions

| Layer | Purpose | Examples |
|-------|---------|----------|
| `get_*_permissions()` | UI visibility only | Show/hide Edit/Delete buttons |
| `can_*` functions | Query permission | Render buttons in UI |
| `assert_*` functions | Enforcement | Block unauthorized requests |
| Mixins/Policies | Gatekeeping | Redirect/403 on dispatch |

**Important**: The `get_ticket_permissions()`, `get_asset_permissions()`, `get_project_permissions()`, and `get_user_permissions()` functions are **UI-only**. They compute what actions a user *could* see, but do not actually enforce security. Real enforcement happens via `assert_*` functions and Mixins.

---

## 2. Role Hierarchy

Roles are ordered from lowest to highest privilege:

| Role | Level | Description |
|------|-------|-------------|
| VIEWER | 1 | Read-only access |
| TECHNICIAN | 2 | Can create/edit own resources |
| MANAGER | 3 | Can manage team resources |
| IT_ADMIN | 4 | Administrative access |
| SUPERADMIN | 5 | Full system access |

---

## 3. Permission Matrices

### Tickets

| Role | Create | View | Update | Delete | Enforcement |
|------|--------|------|--------|--------|-------------|
| VIEWER | ❌ | ✅ | ❌ | ❌ | `can_create_ticket()`, `assert_can_delete_ticket()` |
| TECHNICIAN | ✅ | ✅ | Own only | Own only | `can_create_ticket()`, `can_update_ticket(user, ticket)` |
| MANAGER | ✅ | ✅ | ✅ | ✅ | `can_update_ticket()` (always True) |
| IT_ADMIN | ✅ | ✅ | Lower roles only | Lower roles only | `can_update_ticket()` checks created_by role |
| SUPERADMIN | ✅ | ✅ | ✅ | ✅ | `can_update_ticket()` (always True) |

**Authority Functions**:
- `can_create_ticket(user)` - Returns `user.role != 'VIEWER'`
- `can_read_ticket(user, ticket)` - Always `True`
- `can_update_ticket(user, ticket)` - SUPERADMIN/MANAGER: always; IT_ADMIN: created_by role < IT_ADMIN; TECHNICIAN: created_by == user
- `can_delete_ticket(user, ticket)` - Same as update
- `can_assign_ticket(user, ticket, assignee)` - SUPERADMIN/MANAGER: always; IT_ADMIN: always; TECHNICIAN: own ticket to self only
- `can_close_ticket(user, ticket)` - Same as update

**Enforcement Points**:
- `CreateTicketView.post()` - Calls `can_create_ticket()`
- `ticket_crud` DELETE - Calls `assert_can_delete_ticket()`
- `ticket_crud` PATCH - Calls `assert_can_update_ticket()`

---

### Assets

| Role | Create | View | Update | Delete | Enforcement |
|------|--------|------|--------|--------|-------------|
| VIEWER | ❌ | ✅ | ❌ | ❌ | `can_create_asset()`, `CanManageAssetsMixin` |
| TECHNICIAN | ✅ | ✅ | ✅ | ❌ | `can_update_asset()` checks ownership/role |
| MANAGER | ✅ | ✅ | ✅ | ✅ | `is_admin_override()` returns True |
| IT_ADMIN | ✅ | ✅ | ✅ | ✅ | `can_delete_asset()` via hierarchy |
| SUPERADMIN | ✅ | ✅ | ✅ | ✅ | `is_admin_override()` returns True |

**Authority Functions**:
- `can_create_asset(user)` - Returns `has_strictly_higher_role(user.role, 'VIEWER')`
- `can_read_asset(user, asset)` - Always `True`
- `can_update_asset(user, asset)` - Admin override OR owner OR strictly higher role
- `can_delete_asset(user, asset)` - Admin override OR strictly higher role (owner alone insufficient)
- `can_assign_asset(user, asset)` - Returns `has_higher_role(user.role, 'IT_ADMIN')`
- `can_view_asset_logs(user, asset)` - Returns `has_higher_role(user.role, 'IT_ADMIN')`

**Helper Functions**:
- `is_admin_override(user)` - Returns True for SUPERADMIN or MANAGER
- `is_owner(user, created_by)` - Checks if `user.id == created_by.id`
- `can_modify_subordinate(user, created_by)` - Checks `has_strictly_higher_role(user.role, created_by.role)`

**Enforcement Points**:
- `CreateAssetView` - Uses `CanManageAssetsMixin`
- `EditAssetView` - Uses `CanManageAssetsMixin`
- `delete_asset()` - Calls `assert_can_delete_asset()`
- `asset_crud` DELETE - Uses legacy role check (known exception)

---

### Projects

| Role | Create | View | Update | Delete | Enforcement |
|------|--------|------|--------|--------|-------------|
| VIEWER | ❌ | ✅ | ❌ | ❌ | `can_create_project()`, `ProjectPolicy.can_edit()` |
| TECHNICIAN | ❌ | ✅ | ❌ | ❌ | `can_create_project()` requires MANAGER+ |
| MANAGER | ✅ | ✅ | ✅ | ✅ | `ProjectPolicy.can_create()`, `can_delete_project()` |
| IT_ADMIN | ❌ | ✅ | ❌ | ❌ | Excluded from project management |
| SUPERADMIN | ✅ | ✅ | ✅ | ✅ | `ProjectPolicy` admin override |

**Authority Functions**:
- `can_create_project(user)` - Returns `has_higher_role(user.role, 'MANAGER')`
- `can_read_project(user, project)` - Always `True`
- `can_update_project(user, project)` - Returns `has_higher_role(user.role, 'MANAGER')`
- `can_delete_project(user, project)` - Returns `user.role == 'SUPERADMIN'`
- `can_assign_project_members(user, project)` - Returns `has_higher_role(user.role, 'MANAGER')`
- `can_view_project_logs(user, project)` - Returns `has_higher_role(user.role, 'MANAGER')`

**Policy Class**: `ProjectPolicy` provides additional layer with `can_view()`, `can_create()`, `can_edit()`, `can_delete()`, `can_manage()` methods returning `AuthorizationResult` objects.

**Enforcement Points**:
- `CreateProjectView` - Uses `CanManageProjectsMixin` + `ProjectPolicy.can_create()`
- `EditProjectView.dispatch()` - Calls `ProjectPolicy.can_edit()`
- `delete_project()` - Uses `ProjectPolicy.can_delete().require()`
- `project_crud` - Uses `ProjectPolicy.*().require()` pattern

---

### Users

| Role | Create | View | Update | Change Role | Delete | Enforcement |
|------|--------|------|--------|-------------|--------|-------------|
| VIEWER | ✅ | ✅ | Own only | ❌ | ❌ | `can_create_user()`, `can_update_user()` |
| TECHNICIAN | ✅ | ✅ | Own only | ❌ | ❌ | `can_update_user()` checks self or hierarchy |
| MANAGER | ✅ | ✅ | Lower roles | ❌ | ❌ | `can_update_user()` allows IT_ADMIN on TECHNICIAN/VIEWER |
| IT_ADMIN | ✅ | ✅ | Lower roles | ❌ | ❌ | Same as MANAGER |
| SUPERADMIN | ✅ | ✅ | All | ✅ | ✅ | `can_change_role()`, `can_delete_user()` |

**Authority Functions**:
- `can_create_user(actor)` - Always `True` (self-registration)
- `can_view_user(actor, target)` - Always `True` (read access permissive)
- `can_update_user(actor, target)` - Self OR hierarchy-based
- `can_change_role(actor, target, new_role)` - Cannot self; cannot assign >= own role; SUPERADMIN can assign MANAGER
- `can_deactivate_user(actor, target)` - Cannot self; hierarchy-based
- `can_delete_user(actor, target)` - Cannot self; only SUPERADMIN

**Enforcement Points**:
- `CreateUserView` - Uses `CanManageUsersMixin`
- `EditUserView.dispatch()` - Checks `request.user != self.edit_user and not request.user.can_manage_users`
- `change_user_role()` - Checks `request.user.role == 'SUPERADMIN'`
- `delete_user()` - Calls `assert_can_delete_user()`

---

## 4. Enforcement Mapping Reference

### Mixins Used

| Mixin | Protects | Check |
|-------|----------|-------|
| `CanManageUsersMixin` | CreateUserView, CreateUser | `user.can_manage_users` (IT_ADMIN+) |
| `CanManageTicketsMixin` | EditTicketView | `user.can_manage_tickets` (VIEWER+) |
| `CanManageProjectsMixin` | CreateProjectView | `user.can_manage_projects` (MANAGER+) |
| `CanManageAssetsMixin` | CreateAssetView, EditAssetView | `user.can_manage_assets` (MANAGER+) |

### Domain Authority Functions

| Resource | Create | Update | Delete | Assign |
|----------|--------|--------|--------|--------|
| Ticket | `can_create_ticket()` | `assert_can_update_ticket()` | `assert_can_delete_ticket()` | `assert_can_assign_ticket()` |
| Asset | `can_create_asset()` | `assert_can_update_asset()` | `assert_can_delete_asset()` | `can_assign_asset()` |
| Project | `can_create_project()` | `assert_can_update_project()` | `assert_can_delete_project()` | `can_assign_project_members()` |
| User | `can_create_user()` | `assert_can_update_user()` | `assert_can_delete_user()` | N/A |

---

## 5. Legacy Endpoints

The following endpoints use legacy permission checks (role strings instead of domain authority):

| Endpoint | Action | Legacy Check | Status |
|----------|--------|--------------|--------|
| `asset_crud` | DELETE | `role in ['ADMIN', 'SUPERADMIN', 'IT_ADMIN']` | Known exception |
| `asset_crud` | PATCH | `can_manage_assets` or `role in [...]` | Known exception |

These endpoints should be migrated to use `assert_*` functions for consistency.

---

## 6. Testing

Permission tests are located at:
- `apps/frontend/tests/test_permissions/test_ticket_permissions.py`
- `apps/frontend/tests/test_permissions/test_asset_permissions.py`
- `apps/frontend/tests/test_permissions/test_project_permissions.py`
- `apps/frontend/tests/test_permissions/test_user_permissions.py`

Tests verify that unauthorized users receive HTTP 403 when attempting state-changing operations.

---

## 7. Summary

| Resource | Primary Enforcement | Secondary Enforcement |
|----------|--------------------|-----------------------|
| Tickets | Domain authority (`assert_*`) | None |
| Assets | Domain authority + Mixins | Legacy role check in `asset_crud` |
| Projects | `ProjectPolicy` + domain authority | None |
| Users | Domain authority + custom dispatch checks | None |

**All state-changing operations (POST/PUT/PATCH/DELETE) have backend protection.** The system is designed so that bypassing the UI (e.g., direct API calls) will still result in permission denied errors.

## Guarantees

- All state-changing operations are protected server-side
- UI permissions do not grant access
- Any authorization regression fails CI
