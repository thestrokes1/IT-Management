# ProfileView Ticket History - Complete Documentation

## Overview

This document provides comprehensive documentation for the ProfileView ticket history feature, including context variables, template usage, RBAC enforcement, and audit-grade logging.

---

## Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                      Presentation Layer                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    ProfileView (View)                        ││
│  │  - Handles HTTP requests                                    ││
│  │  - Calls service layer                                      ││
│  │  - Builds template context                                  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Service Layer                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                TicketQueryService                            ││
│  │  - Ticket fetching with Q objects                           ││
│  │  - Statistics calculation                                   ││
│  │  - RBAC permission checks                                   ││
│  │  - Filter options                                           ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Data Layer                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                     Ticket Model                             ││
│  │  - created_by (ForeignKey to User)                          ││
│  │  - assigned_to (ForeignKey to User, nullable)               ││
│  │  - status, priority, title, etc.                            ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Context Variables

The ProfileView provides the following context variables to the template:

### User Information
| Variable | Type | Description |
|----------|------|-------------|
| `user` | User | The logged-in user object |
| `user.id` | int | User's ID |
| `user.username` | str | User's username |
| `user.email` | str | User's email |
| `user.first_name` | str | User's first name |
| `user.last_name` | str | User's last name |
| `user.role` | str | User's role (SUPERADMIN, IT_ADMIN, MANAGER, TECHNICIAN, VIEWER) |
| `user.is_superuser` | bool | Whether user is a superuser |
| `user.is_active` | bool | Whether user account is active |
| `user.date_joined` | datetime | When user account was created |
| `user.last_login` | datetime | When user last logged in |

### Ticket Data
| Variable | Type | Description |
|----------|------|-------------|
| `my_tickets` | list | List of ticket dictionaries |
| `my_tickets.0.id` | int | Ticket ID (clickable link) |
| `my_tickets.0.title` | str | Ticket title |
| `my_tickets.0.status` | str | Ticket status (OPEN, IN_PROGRESS, RESOLVED, CLOSED) |
| `my_tickets.0.priority` | str | Ticket priority (CRITICAL, HIGH, MEDIUM, LOW) |
| `my_tickets.0.status_display` | str | Human-readable status |
| `my_tickets.0.priority_display` | str | Human-readable priority |
| `my_tickets.0.created_at` | datetime | When ticket was created |
| `my_tickets.0.updated_at` | datetime | When ticket was last updated |
| `my_tickets.0.created_by` | dict | Creator info: `{id, username}` |
| `my_tickets.0.updated_by` | dict | Last updater info: `{id, username}` |
| `my_tickets.0.assigned_to` | dict | Assignee info: `{id, username}` |
| `my_tickets.0.category` | str | Category name (if any) |

### Pagination Data
| Variable | Type | Description |
|----------|------|-------------|
| `ticket_pagination.page` | int | Current page number (1-indexed) |
| `ticket_pagination.page_size` | int | Items per page (10) |
| `ticket_pagination.total_count` | int | Total number of tickets |
| `ticket_pagination.total_pages` | int | Total number of pages |
| `ticket_pagination.has_next` | bool | Whether there is a next page |
| `ticket_pagination.has_previous` | bool | Whether there is a previous page |

### Statistics Data
| Variable | Type | Description |
|----------|------|-------------|
| `stats.total` | int | Total tickets (created + assigned) |
| `stats.created` | int | Tickets created by user |
| `stats.assigned` | int | Tickets assigned to user |
| `stats.resolved` | int | Resolved tickets count |
| `stats.open` | int | Open tickets count |
| `stats.can_reopen` | int | Tickets eligible for reopen |

### Filter Data
| Variable | Type | Description |
|----------|------|-------------|
| `available_filters.statuses` | list | Available status values from user's tickets |
| `available_filters.priorities` | list | Available priority values from user's tickets |
| `current_filters.status` | str or None | Currently selected status filter |
| `current_filters.priority` | str or None | Currently selected priority filter |

### RBAC Data
| Variable | Type | Description |
|----------|------|-------------|
| `can_reopen_ticket` | bool | Whether user can reopen tickets (admin only) |

---

## Template Usage

### Basic Ticket Table

```html
<table class="w-full text-sm">
    <thead class="bg-gray-50 border-b border-gray-200">
        <tr>
            <th class="px-4 py-3 text-left font-medium text-gray-600">ID</th>
            <th class="px-4 py-3 text-left font-medium text-gray-600">Title</th>
            <th class="px-4 py-3 text-left font-medium text-gray-600">Status</th>
            <th class="px-4 py-3 text-left font-medium text-gray-600">Priority</th>
            <th class="px-4 py-3 text-left font-medium text-gray-600">Created</th>
            <th class="px-4 py-3 text-left font-medium text-gray-600">Last Updated</th>
            <th class="px-4 py-3 text-left font-medium text-gray-600">Actions</th>
        </tr>
    </thead>
    <tbody class="divide-y divide-gray-100">
        {% for ticket in my_tickets %}
        <tr class="hover:bg-gray-50 transition-colors">
            <td class="px-4 py-3 font-medium text-gray-900">
                <a href="/tickets/{{ ticket.id }}/" class="text-blue-600 hover:text-blue-800">
                    #{{ ticket.id }}
                </a>
            </td>
            <td class="px-4 py-3 text-gray-700 max-w-xs truncate" title="{{ ticket.title }}">
                {{ ticket.title }}
            </td>
            <td class="px-4 py-3">
                <span class="px-2.5 py-1 rounded-full text-xs font-medium
                    {% if ticket.status == 'OPEN' %}bg-blue-100 text-blue-800{% endif %}
                    {% if ticket.status == 'IN_PROGRESS' %}bg-yellow-100 text-yellow-800{% endif %}
                    {% if ticket.status == 'RESOLVED' %}bg-green-100 text-green-800{% endif %}
                    {% if ticket.status == 'CLOSED' %}bg-gray-100 text-gray-800{% endif %}">
                    {{ ticket.status_display }}
                </span>
            </td>
            <td class="px-4 py-3">
                <span class="px-2.5 py-1 rounded-full text-xs font-medium
                    {% if ticket.priority == 'CRITICAL' %}bg-red-100 text-red-800{% endif %}
                    {% if ticket.priority == 'HIGH' %}bg-orange-100 text-orange-800{% endif %}
                    {% if ticket.priority == 'MEDIUM' %}bg-blue-100 text-blue-800{% endif %}
                    {% if ticket.priority == 'LOW' %}bg-gray-100 text-gray-800{% endif %}">
                    {{ ticket.priority_display }}
                </span>
            </td>
            <td class="px-4 py-3 text-gray-500 whitespace-nowrap">
                {{ ticket.created_at|date:"M d, Y H:i" }}
            </td>
            <td class="px-4 py-3 text-gray-500 whitespace-nowrap">
                {{ ticket.updated_at|date:"M d, Y H:i" }}
                {% if ticket.updated_by and ticket.updated_by.username %}
                <span class="text-xs text-gray-400 block">
                    by <a href="/user/{{ ticket.updated_by.id }}/" class="text-blue-600 hover:underline">
                        {{ ticket.updated_by.username }}
                    </a>
                </span>
                {% endif %}
            </td>
            <td class="px-4 py-3">
                <a href="/tickets/{{ ticket.id }}/" 
                   class="inline-flex items-center px-2.5 py-1 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-medium rounded">
                    <i class="fas fa-eye mr-1"></i> Open
                </a>
                {% if ticket.status == 'RESOLVED' or ticket.status == 'CLOSED' %}
                    {% if can_reopen_ticket %}
                    <a href="{% url 'frontend:profile_reopen_ticket' ticket.id %}" 
                       class="inline-flex items-center px-2.5 py-1 bg-yellow-50 hover:bg-yellow-100 text-yellow-700 text-xs font-medium rounded"
                       onclick="return confirm('Reopen this ticket?');">
                        <i class="fas fa-sync mr-1"></i> Reopen
                    </a>
                    {% endif %}
                {% endif %}
            </td>
        </tr>
        {% empty %}
        <tr>
            <td colspan="7" class="px-6 py-8 text-center text-gray-500">
                No tickets found in your history.
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### Filter Form

```html
<form method="GET" class="flex flex-wrap gap-2 items-center">
    {% if current_filters.status %}
    <input type="hidden" name="status" value="{{ current_filters.status }}">
    {% endif %}
    {% if current_filters.priority %}
    <input type="hidden" name="priority" value="{{ current_filters.priority }}">
    {% endif %}
    
    <select name="status" onchange="this.form.submit()" 
            class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg">
        <option value="">All Statuses</option>
        {% for status in available_filters.statuses %}
        <option value="{{ status }}" {% if current_filters.status == status %}selected{% endif %}>
            {{ status }}
        </option>
        {% endfor %}
    </select>
    
    <select name="priority" onchange="this.form.submit()" 
            class="px-3 py-1.5 text-sm border border-gray-300 rounded-lg">
        <option value="">All Priorities</option>
        {% for priority in available_filters.priorities %}
        <option value="{{ priority }}" {% if current_filters.priority == priority %}selected{% endif %}>
            {{ priority }}
        </option>
        {% endfor %}
    </select>
    
    {% if current_filters.status or current_filters.priority %}
    <a href="{% url 'frontend:profile' %}" class="px-3 py-1.5 text-sm text-red-600">
        <i class="fas fa-times mr-1"></i>Clear
    </a>
    {% endif %}
</form>
```

### Statistics Cards

```html
<div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
    <!-- Total Tickets -->
    <div class="bg-white rounded-xl shadow-md p-5 border-l-4 border-blue-500">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-500 uppercase">Total Tickets</p>
                <p class="text-3xl font-bold text-gray-900 mt-1">{{ stats.total }}</p>
            </div>
            <div class="bg-blue-100 p-3 rounded-full">
                <i class="fas fa-ticket-alt text-blue-600 text-xl"></i>
            </div>
        </div>
    </div>
    
    <!-- Created Tickets -->
    <div class="bg-white rounded-xl shadow-md p-5 border-l-4 border-green-500">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-500 uppercase">Created</p>
                <p class="text-3xl font-bold text-gray-900 mt-1">{{ stats.created }}</p>
            </div>
            <div class="bg-green-100 p-3 rounded-full">
                <i class="fas fa-plus-circle text-green-600 text-xl"></i>
            </div>
        </div>
    </div>
    
    <!-- Assigned Tickets -->
    <div class="bg-white rounded-xl shadow-md p-5 border-l-4 border-yellow-500">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-500 uppercase">Assigned</p>
                <p class="text-3xl font-bold text-gray-900 mt-1">{{ stats.assigned }}</p>
            </div>
            <div class="bg-yellow-100 p-3 rounded-full">
                <i class="fas fa-user-check text-yellow-600 text-xl"></i>
            </div>
        </div>
    </div>
    
    <!-- Resolved Tickets -->
    <div class="bg-white rounded-xl shadow-md p-5 border-l-4 border-purple-500">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-500 uppercase">Resolved</p>
                <p class="text-3xl font-bold text-gray-900 mt-1">{{ stats.resolved }}</p>
            </div>
            <div class="bg-purple-100 p-3 rounded-full">
                <i class="fas fa-check-double text-purple-600 text-xl"></i>
            </div>
        </div>
    </div>
</div>
```

### Pagination

```html
{% if ticket_pagination.total_pages > 1 %}
<div class="px-6 py-4 border-t border-gray-100 bg-gray-50">
    <div class="flex items-center justify-between">
        <div class="text-sm text-gray-500">
            Page {{ ticket_pagination.page }} of {{ ticket_pagination.total_pages }}
        </div>
        <div class="flex gap-2">
            {% if ticket_pagination.has_previous %}
            <a href="?page={{ ticket_pagination.page|add:"-1" }}&status={{ current_filters.status|default:"" }}&priority={{ current_filters.priority|default:"" }}" 
               class="px-3 py-1 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                <i class="fas fa-chevron-left mr-1"></i> Previous
            </a>
            {% else %}
            <span class="px-3 py-1 text-sm bg-gray-100 text-gray-400 border border-gray-200 rounded-lg cursor-not-allowed">
                <i class="fas fa-chevron-left mr-1"></i> Previous
            </span>
            {% endif %}
            
            {% if ticket_pagination.has_next %}
            <a href="?page={{ ticket_pagination.page|add:"1" }}&status={{ current_filters.status|default:"" }}&priority={{ current_filters.priority|default:"" }}" 
               class="px-3 py-1 text-sm bg-white border border-gray-300 rounded-lg hover:bg-gray-50">
                Next <i class="fas fa-chevron-right ml-1"></i>
            </a>
            {% else %}
            <span class="px-3 py-1 text-sm bg-gray-100 text-gray-400 border border-gray-200 rounded-lg cursor-not-allowed">
                Next <i class="fas fa-chevron-right ml-1"></i>
            </span>
            {% endif %}
        </div>
    </div>
</div>
{% endif %}

<!-- View All Link -->
{% if ticket_pagination.total_count > 10 %}
<div class="text-center py-4">
    <a href="?status={{ current_filters.status|default:"" }}&priority={{ current_filters.priority|default:"" }}" 
       class="inline-flex items-center px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-medium rounded-lg">
        <i class="fas fa-list mr-2"></i> View All {{ ticket_pagination.total_count }} Tickets
    </a>
</div>
{% endif %}
```

---

## RBAC Enforcement

### Permission Levels

| Role | Can View Tickets | Can Reopen Tickets |
|------|------------------|-------------------|
| SUPERADMIN | ✅ Yes | ✅ Yes |
| IT_ADMIN | ✅ Yes | ✅ Yes |
| MANAGER | ✅ Yes | ✅ Yes |
| TECHNICIAN | ✅ Yes | ❌ No |
| VIEWER | ✅ Yes | ❌ No |

### Reopen Permission Check

```python
def can_user_reopen_ticket(user):
    """Check if user has permission to reopen tickets."""
    if not user:
        return False
    
    user_role = getattr(user, 'role', 'VIEWER')
    
    # Only admins can reopen tickets
    return user.is_superuser or user_role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
```

### View Permission Check

All users can view tickets where they are the creator OR assignee:

```python
def get_user_tickets(user, status_filter=None, priority_filter=None):
    """Fetch tickets where user is creator OR assignee."""
    base_query = Q(created_by=user) | Q(assigned_to=user)
    
    if status_filter:
        base_query &= Q(status=status_filter)
    
    if priority_filter:
        base_query &= Q(priority=priority_filter)
    
    return Ticket.objects.filter(base_query).select_related(
        'created_by', 'assigned_to', 'category', 'updated_by'
    )
```

---

## Audit-Grade Logging

### Activity Logged on Ticket Reopen

When a ticket is reopened from the profile page, the following activity is logged:

```python
ActivityService.log_activity(
    user=request.user,           # Actor who performed the action
    action='TICKET_REOPENED',    # Action type
    model_name='ticket',         # Entity type
    object_id=ticket.id,         # Entity ID
    object_repr=str(ticket),     # Entity representation
    description=f"Ticket reopened from {old_status} to IN_PROGRESS",
    request=request              # For IP and User Agent
)
```

### Audit Log Fields

| Field | Source | Description |
|-------|--------|-------------|
| `actor` | `request.user` | User who performed the action |
| `action` | Code | Action type (TICKET_REOPENED) |
| `model_name` | Code | Entity type (ticket) |
| `object_id` | Ticket.id | ID of the ticket |
| `object_repr` | Ticket.__str__() | Human-readable ticket representation |
| `description` | Code | Description of changes |
| `timestamp` | `timezone.now()` | When action occurred |
| `ip_address` | `request.META['REMOTE_ADDR']` | Client IP address |
| `user_agent` | `request.META['HTTP_USER_AGENT']` | Browser/client info |
| `level` | Code | Log level (INFO, WARNING, ERROR) |

### Viewing Audit Logs

Audit logs can be viewed in the admin interface or via the ActivityService:

```python
from apps.logs.services.activity_service import ActivityService

# Get recent activities for a specific ticket
activities = ActivityService.get_activity_logs(
    user=request.user,
    model_name='ticket',
    object_id=ticket_id,
    limit=50
)
```

---

## TicketQueryService API

### Methods

#### `get_user_tickets(**kwargs)`

Fetches tickets for a user with optional filtering and pagination.

**Parameters:**
- `user`: The user to fetch tickets for
- `status_filter`: Optional status to filter by
- `priority_filter`: Optional priority to filter by
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10, max: 50)
- `order_by`: Field to order by (default: '-created_at')

**Returns:**
```python
{
    'tickets': [
        {
            'id': 1,
            'title': 'Ticket Title',
            'status': 'OPEN',
            'priority': 'HIGH',
            'status_display': 'Open',
            'priority_display': 'High',
            'created_at': datetime,
            'updated_at': datetime,
            'created_by': {'id': 1, 'username': 'user'},
            'updated_by': {'id': 1, 'username': 'user'},
            'assigned_to': {'id': 2, 'username': 'assignee'},
            'category': 'Category Name',
        },
        ...
    ],
    'page': 1,
    'page_size': 10,
    'total_count': 25,
    'total_pages': 3,
    'has_next': True,
    'has_previous': False,
}
```

#### `get_user_ticket_stats(user)`

Calculates statistics for a user's tickets.

**Returns:**
```python
{
    'total': 25,      # All tickets (created or assigned)
    'created': 10,    # Tickets created by user
    'assigned': 15,   # Tickets assigned to user
    'resolved': 8,    # Resolved tickets
    'open': 17,       # Open tickets (NEW, OPEN, IN_PROGRESS)
    'can_reopen': 5,  # Tickets eligible for reopen
}
```

#### `can_user_reopen_ticket(user)`

Checks if user has permission to reopen tickets.

**Returns:** `bool` - True if user can reopen tickets

#### `get_available_filters(user)`

Gets available filter options based on user's tickets.

**Returns:**
```python
{
    'statuses': ['OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'],
    'priorities': ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'],
}
```

---

## Testing

### Unit Tests Location

`backend/apps/frontend/tests/test_profile_ticket_history.py`

### Running Tests

```bash
# Run all profile tests
pytest backend/apps/frontend/tests/test_profile_ticket_history.py -v

# Run specific test class
pytest backend/apps/frontend/tests/test_profile_ticket_history.py::TestTicketQueryService -v

# Run specific test
pytest backend/apps/frontend/tests/test_profile_ticket_history.py::TestTicketQueryService::test_can_user_reopen_ticket_admin_returns_true -v
```

### Test Coverage

- `TestTicketQueryService`: Tests for service layer methods
- `TestProfileView`: Tests for view layer
- `TestProfileReopenTicket`: Tests for reopen functionality
- `TestPagination`: Tests for pagination
- `TestRBACEnforcement`: Tests for RBAC

---

## Troubleshooting

### Issue: Tickets not showing

**Cause**: User may not have created or been assigned any tickets.

**Solution**: Create a ticket or assign one to the user.

### Issue: Reopen button not visible

**Cause**: User doesn't have admin role.

**Solution**: Only SUPERADMIN, IT_ADMIN, MANAGER can see the reopen button.

### Issue: Filter dropdowns are empty

**Cause**: User has no tickets with that status/priority.

**Solution**: The dropdowns only show values that exist in the user's tickets.

### Issue: Pagination not working

**Cause**: Missing pagination context variables.

**Solution**: Ensure `ticket_pagination` is in the context.

---

## Performance Considerations

1. **Query Optimization**: Uses `select_related()` to avoid N+1 queries
2. **Pagination**: Limits results to 10 per page
3. **Database Indexes**: Ensure indexes on:
   - `ticket.created_by`
   - `ticket.assigned_to`
   - `ticket.status`
   - `ticket.priority`

---

## Security Considerations

1. **RBAC**: All ticket access is restricted to creator/assignee
2. **SQL Injection**: Protected via Django ORM
3. **XSS**: Template escaping is automatic
4. **CSRF**: Django's `@login_required` and CSRF protection enabled
