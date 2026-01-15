# TODO: Expose Domain Permission Dictionaries to Frontend Templates

## Goal
Ensure frontend templates reflect backend authorization by using permission dictionaries from domain authority services.

## Tasks

### 1. Tickets Views (`apps/frontend/views/tickets.py`)
- [ ] Add `permissions_map` to `TicketsView` (list view)
- [ ] Verify `EditTicketView` uses `permissions` (already has `ticket_perms`)

### 2. Projects Views (`apps/frontend/views/projects.py`)
- [ ] Import `get_project_permissions` from project_authority
- [ ] Add `permissions_map` to `ProjectsView` (list view)
- [ ] Add `permissions` to `EditProjectView` (detail view)

### 3. Assets Views (`apps/frontend/views/assets.py`)
- [ ] Import `get_asset_permissions` from asset_authority
- [ ] Add `permissions_map` to `AssetsView` (list view)
- [ ] Add `permissions` to `EditAssetView` (detail view)

### 4. Users Views (`apps/frontend/views/users.py`)
- [ ] Import `get_user_permissions` from user_authority
- [ ] Add `permissions_map` to `UsersView` (list view)
- [ ] Add `permissions` to `EditUserView` (detail view)

## Pattern for Lists
```python
context["permissions_map"] = {
    obj.id: get_*_permissions(request.user, obj)
    for obj in queryset
}
```

## Pattern for Single Objects
```python
context["permissions"] = get_*_permissions(request.user, object)
```

## Constraints
- DO NOT perform authorization in templates
- DO NOT add role checks in views
- DO NOT modify domain services
- Keep views thin (query + permissions only)

