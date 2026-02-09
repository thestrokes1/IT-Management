# IT Management Platform Architecture

This document defines the architectural rules for the IT Management Platform. All code must comply with these rules.

---

## 1. CQRS Write Model Rules

### 1.1 Model Mutations Location

**ALLOWED - Model mutations MUST only occur in:**
```
apps/{domain}/application/*.py
```

These are CQRS command files that handle create, update, delete operations.

**FORBIDDEN - Model mutations MUST NOT occur in:**
- `apps/frontend/views/*.py` - Views are read-only
- `apps/frontend/services.py` - Services are read-only
- `apps/{domain}/serializers.py` - Serializers are read-only
- `apps/{domain}/queries/*.py` - Queries are read-only
- `apps/{domain}/signals.py` - Signals must not mutate models
- `apps/{domain}/views.py` - Views are read-only

### 1.2 Model Mutation Methods

The following methods constitute model mutations and are subject to the location rules:
- `.save()` - Creating or updating a model instance
- `.delete()` - Deleting a model instance
- `.create()` - Using QuerySet.create()
- `.update()` - Using QuerySet.update()
- `.get_or_create()` - Creating via ORM
- `.update_or_create()` - Creating via ORM

---

## 2. Authorization Flow

### 2.1 Domain Authority Pattern

All authorization checks MUST use the domain authority layer:

**Location:** `apps/{domain}/domain/services/{domain}_authority.py`

**Pattern:**
```python
# Import from domain authority
from apps.{domain}.domain.services.{domain}_authority import (
    can_action,
    assert_can_action,
)

# In CQRS command:
def execute(self, user, entity_id):
    # Check authorization
    assert_can_action(user, entity)
    
    # Perform mutation only after authorization passes
    entity.save()
```

**Roles (highest to lowest):**
- `SUPERADMIN` (rank 4) - Full access
- `MANAGER` (rank 4) - Same as SUPERADMIN
- `IT_ADMIN` (rank 3) - Full domain access
- `TECHNICIAN` (rank 2) - Limited to assigned items
- `VIEWER` (rank 1) - Read-only

### 2.2 Technician Ownership

For TECHNICIAN role, ownership is determined by `assigned_to`, NOT `created_by`:
- Technicians can only edit/delete items assigned to them
- Technicians CANNOT assign/unassign items to others
- Technicians CAN self-assign to unassigned items

---

## 3. Activity Logging Rules

### 3.1 Transaction.on_commit

Activity logging MUST use `transaction.on_commit()` to ensure logging only occurs after successful transaction commit:

```python
from django.db import transaction

def execute(self, user, entity_id):
    entity = Entity.objects.get(id=entity_id)
    
    # Perform the mutation
    entity.status = 'CLOSED'
    entity.save()
    
    # Emit event after commit
    transaction.on_commit(lambda: emit_activity_event(user, entity))
```

### 3.2 Try/Except Pattern

Activity logging SHOULD be wrapped in try/except:

```python
try:
    emit_activity_event(user, entity)
except Exception as e:
    # Log error but don't fail the main operation
    logger.error(f"Activity logging failed: {e}")
```

---

## 4. Domain Events Usage

### 4.1 Event Emission Pattern

CQRS commands SHOULD emit domain events for state changes:

**Location:** `apps/{domain}/domain/events.py`

**Pattern:**
```python
def emit_domain_event(event_type, **kwargs):
    """Publish domain event to handlers."""
    from apps.core.events import publish
    publish(event_type, **kwargs)

# In CQRS command:
emit_domain_event(
    'entity_created',
    entity_id=entity.id,
    entity_name=entity.name,
    actor=user,
)
```

### 4.2 Event Types

Common event types:
- `{entity}_created` - Entity was created
- `{entity}_updated` - Entity was updated
- `{entity}_deleted` - Entity was deleted
- `{entity}_assigned` - Entity was assigned to user
- `{entity}_unassigned` - Entity was unassigned

---

## 5. Forbidden Anti-Patterns

### 5.1 Services Mutating Models (FORBIDDEN)

```python
# WRONG - Services must not mutate models
class ProjectService:
    def update_project(self, project_id, data):
        project = Project.objects.get(id=project_id)
        project.status = data['status']  # FORBIDDEN
        project.save()  # FORBIDDEN
```

```python
# CORRECT - Use CQRS command
class ProjectService:
    def update_project(self, request, project_id):
        # Delegate to CQRS command
        command = UpdateProject()
        return command.execute(request.user, project_id, request.POST)
```

### 5.2 Views Mutating Models (FORBIDDEN)

```python
# WRONG - Views must not mutate models
def update_ticket(request, ticket_id):
    ticket = Ticket.objects.get(id=ticket_id)
    ticket.status = request.POST['status']  # FORBIDDEN
    ticket.save()  # FORBIDDEN
```

```python
# CORRECT - Use CQRS command
def update_ticket(request, ticket_id):
    command = UpdateTicket()
    result = command.execute(
        user=request.user,
        ticket_id=ticket_id,
        ticket_data=request.POST
    )
```

### 5.3 Serializers Mutating Models (FORBIDDEN)

```python
# WRONG - Serializers must not mutate models
class TicketSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance.status = validated_data.get('status', instance.status)
        instance.save()  # FORBIDDEN
        return instance
```

### 5.4 Signals Mutating Models (FORBIDDEN)

```python
# WRONG - Signals must not mutate models
@receiver(post_save, sender=Project)
def project_saved(sender, instance, **kwargs):
    instance.status = 'MODIFIED'  # FORBIDDEN
    instance.save()  # FORBIDDEN
```

---

## 6. Directory Structure

```
backend/
├── apps/
│   ├── {domain}/
│   │   ├── application/        # CQRS commands (WRITE model)
│   │   │   ├── create_*.py
│   │   │   ├── update_*.py
│   │   │   ├── delete_*.py
│   │   │   └── manage_*.py
│   │   ├── domain/
│   │   │   ├── services/       # Authority layer
│   │   │   │   └── {domain}_authority.py
│   │   │   └── events.py       # Domain events
│   │   ├── models.py           # Models (passive)
│   │   ├── serializers.py      # Read-only (QUERY model)
│   │   ├── queries/            # Read-only (QUERY model)
│   │   │   └── {domain}_query.py
│   │   ├── views.py            # Read-only (orchestration)
│   │   └── signals.py          # No mutations allowed
│   └── frontend/
│       ├── views/              # Read-only (orchestration)
│       ├── services.py         # Read-only (orchestration)
│       └── permissions_mapper.py
└── core/
    ├── domain/
    │   └── authorization.py    # Base authorization
    └── services/
        └── activity_logger.py # Activity logging
```

---

## 7. Enforcement Tests

This architecture is enforced by tests in:
```
apps/frontend/tests/test_cqrs_architecture.py
```

Tests verify:
- Model mutations only in CQRS commands
- No mutations in forbidden directories
- CQRS command files exist
- Domain events are used
- Authorization patterns are followed

---

## 8. Adding New CQRS Commands

When adding a new domain operation:

1. Create command in `apps/{domain}/application/`
2. Add authorization in `apps/{domain}/domain/services/{domain}_authority.py`
3. Emit domain event in `apps/{domain}/domain/events.py`
4. Update views to delegate to command (no direct mutations)
5. Add tests for the new command

---

## Summary

| Layer | Can Mutate? | Notes |
|-------|-------------|-------|
| `application/` | YES | CQRS commands only |
| `domain/services/` | YES | Authority checks |
| `views/` | NO | Read-only orchestration |
| `services.py` | NO | Read-only orchestration |
| `serializers.py` | NO | Read-only serialization |
| `queries/` | NO | Read-only queries |
| `signals.py` | NO | No mutations allowed |
| `models.py` | NO | Passive models only |

