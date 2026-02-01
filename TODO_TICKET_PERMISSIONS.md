# TODO: Ticket Permissions Implementation & Enforcement

## Objective
Implement centralized `get_ticket_permissions(user, ticket)` function with required permissions and enforce permissions on all ticket mutations.

---

## Completed Tasks

### Phase 1: Domain Layer Changes ✅
- [x] 1.1 Add `can_assign_self(user, ticket)` function to `ticket_authority.py`
- [x] 1.2 Add `can_resolve(user, ticket)` function to `ticket_authority.py`
- [x] 1.3 Add `can_reopen(user, ticket)` function to `ticket_authority.py`
- [x] 1.4 Update `get_ticket_permissions()` to return required permissions
- [x] 1.5 Add assertion functions for enforcement

### Phase 2: Test Updates ✅
- [x] 2.1 Update domain tests with new permission functions
- [x] 2.2 Add test cases for `can_reopen` with RESOLVED status check

### Phase 3: TicketStatusHistory Model ✅
- [x] 3.1 Add `TicketStatusHistory` model to `models.py`
- [x] 3.2 Create migration file

### Phase 4: Activity Logger Service ✅
- [x] 4.1 Create `apps/core/services/activity_logger.py`
- [x] 4.2 Implement `log_activity()` function
- [x] 4.3 Add human-readable action labels
- [x] 4.4 Add convenience functions

### Phase 5: Domain Events ✅
- [x] 5.1 Create `apps/tickets/domain/events.py`
- [x] 5.2 Define ticket domain events:
  - `TicketAssigned`
  - `TicketUpdated`
  - `TicketResolved`
  - `TicketReopened`
  - `TicketStatusChanged`
- [x] 5.3 Implement event handlers that write ActivityLog + StatusHistory
- [x] 5.4 Events triggered only after successful commit (via EventDispatcher)

---

## Architecture Summary

### Domain Events Flow:
```
Application Layer (Use Case)
    ↓
Permission Check (assert_*)
    ↓
Business Logic
    ↓
Event Dispatch (emit_ticket_*)
    ↓
EventDispatcher.dispatch() → transaction.on_commit()
    ↓
Event Handlers (write ActivityLog + StatusHistory)
```

### Files Created/Modified:

| File | Purpose |
|------|---------|
| `backend/apps/tickets/domain/services/ticket_authority.py` | Permission functions + assertions |
| `backend/apps/tickets/models.py` | TicketStatusHistory model |
| `backend/apps/tickets/migrations/XXXXX_create_ticket_status_history.py` | Migration |
| `backend/apps/tickets/tests/domain/test_ticket_authority.py` | Domain tests |
| `backend/apps/core/services/activity_logger.py` | Centralized activity logging |
| `backend/apps/tickets/domain/events.py` | Domain events + handlers |

---

## Domain Events

### Event Classes:
```python
from apps.tickets.domain.events import (
    TicketAssigned,
    TicketUpdated,
    TicketResolved,
    TicketReopened,
    TicketStatusChanged,
    emit_ticket_assigned,
    # ... etc
)

# Emit an event (triggers after transaction commit)
emit_ticket_assigned(
    ticket_id=ticket.id,
    ticket_title=ticket.title,
    actor=request.user,
    assignee_id=assignee.id,
    assignee_username=assignee.username,
)
```

### Event Handlers:
Each handler writes ActivityLog and/or StatusHistory:
- `handle_ticket_assigned` → ActivityLog
- `handle_ticket_updated` → ActivityLog
- `handle_ticket_resolved` → ActivityLog
- `handle_ticket_reopened` → ActivityLog
- `handle_ticket_status_changed` → StatusHistory

### Rules Followed:
✅ Events triggered only after successful commit (via `transaction.on_commit()`)
✅ Event handlers write ActivityLog + StatusHistory
✅ No side effects inside entities
✅ Human-readable action labels
✅ No business logic inside the logger

---

## Usage in Application Layer

```python
from apps.tickets.domain.services.ticket_authority import (
    assert_can_resolve,
    assert_can_reopen,
)
from apps.tickets.domain.events import (
    emit_ticket_resolved,
    emit_ticket_reopened,
    emit_ticket_status_changed,
)

class ResolveTicket:
    def execute(self, user, ticket_id, resolution_summary):
        ticket = Ticket.objects.get(ticket_id=ticket_id)
        
        # 1. Permission check
        assert_can_resolve(user, ticket)
        
        # 2. Store previous status for event
        previous_status = ticket.status
        
        # 3. Update ticket
        ticket.status = 'RESOLVED'
        ticket.resolution_summary = resolution_summary
        ticket.resolved_at = timezone.now()
        ticket.save()
        
        # 4. Emit events (handlers run after commit)
        emit_ticket_status_changed(
            ticket_id=ticket.id,
            ticket_title=ticket.title,
            actor=user,
            from_status=previous_status,
            to_status='RESOLVED',
        )
        emit_ticket_resolved(
            ticket_id=ticket.id,
            ticket_title=ticket.title,
            actor=user,
            resolution_summary=resolution_summary,
        )
```

