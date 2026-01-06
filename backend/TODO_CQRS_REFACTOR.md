# CQRS-Lite Refactoring TODO

## Overview
Refactor read operations to follow a CQRS-lite approach with query classes and command services.

## Plan

### Step 1: Create Query Classes (Domain-specific locations)

- [x] 1.1 Create `apps/projects/queries/__init__.py`
- [x] 1.2 Create `apps/projects/queries/project_query.py` with:
  - `get_all_projects()` - returns list of projects with prefetch
  - `get_project_by_id()` - returns single project or None
  - `get_project_with_details()` - returns project with members, category
  - `get_categories()` - returns active categories
  - `get_status_choices()` - returns status choices
  - `get_priority_choices()` - returns priority choices

- [x] 1.3 Create `apps/assets/queries/__init__.py`
- [x] 1.4 Create `apps/assets/queries/asset_query.py` with:
  - `get_all_assets()` - returns list of assets with prefetch
  - `get_asset_by_id()` - returns single asset or None
  - `get_asset_with_details()` - returns asset with category, assigned_to
  - `get_categories()` - returns active categories
  - `get_status_choices()` - returns status choices

- [x] 1.5 Create `apps/tickets/queries/__init__.py`
- [x] 1.6 Create `apps/tickets/queries/ticket_query.py` with:
  - `get_all_tickets()` - returns list of tickets with prefetch
  - `get_ticket_by_id()` - returns single ticket or None
  - `get_ticket_with_details()` - returns ticket with category, type, assigned_to
  - `get_categories()` - returns active categories
  - `get_types()` - returns active ticket types
  - `get_status_choices()` - returns status choices
  - `get_priority_choices()` - returns priority choices

### Step 2: Create Command Services

- [x] 2.1 Update `apps/frontend/services.py` with:
  - `ProjectService` - create_project, update_project, delete_project
  - `AssetService` - create_asset, update_asset, delete_asset
  - `TicketService` - create_ticket, update_ticket, delete_ticket

### Step 3: Refactor Views

- [x] 3.1 Refactor `apps/frontend/views/projects.py`:
  - Use `ProjectQuery` for all read operations in `get_context_data()`
  - Use `ProjectService` for create/update/delete operations
  - Remove direct ORM queries from views

- [x] 3.2 Refactor `apps/frontend/views/assets.py`:
  - Use `AssetQuery` for all read operations in `get_context_data()`
  - Use `AssetService` for create/update/delete operations
  - Remove direct ORM queries from views

- [x] 3.3 Refactor `apps/frontend/views/tickets.py`:
  - Use `TicketQuery` for all read operations in `get_context_data()`
  - Use `TicketService` for create/update/delete operations
  - Remove direct ORM queries from views

## Rules (Followed)
- Queries must NEVER mutate state - ✅ All query methods are read-only
- Queries must NOT return HttpResponse/JsonResponse - ✅ Queries return QuerySets/dicts only
- Services remain command-only (handle state mutations) - ✅ Services handle all writes
- Views call queries for reads and services for writes - ✅ Views use CQRS pattern

