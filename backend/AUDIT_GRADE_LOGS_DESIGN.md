# Audit-Grade Activity Logs Design Document

This document specifies the complete audit-grade activity logging system for the IT Management Platform. It defines the model enhancements, structured logging payloads, adapter patterns, and UI rendering rules.

---

## 1. Model Enhancements

### 1.1 ActivityLog Model Schema (Current + New Fields)

The ActivityLog model is enhanced with new fields for structured, audit-grade logging while maintaining backward compatibility.

```python
# apps/logs/models.py

class ActivityLog(models.Model):
    """
    Activity log model for the IT Management Platform.
    
    Key Principles:
    - `timestamp` is the canonical time field (no created_at)
    - Logs are immutable after creation
    - Structured data is captured at write time
    """
    
    # =====================================================================
    # EXISTING FIELDS (preserved for backward compatibility)
    # =====================================================================
    
    log_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs'
    )
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='INFO')
    category = models.ForeignKey(
        LogCategory, on_delete=models.SET_NULL, null=True, blank=True
    )
    
    title = models.CharField(max_length=200)  # Short description
    description = models.TextField()  # Detailed description
    
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_path = models.CharField(max_length=500, blank=True)
    request_method = models.CharField(max_length=10, blank=True)
    
    extra_data = models.JSONField(default=dict, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # =====================================================================
    # NEW FIELDS (for audit-grade logging)
    # =====================================================================
    
    # Actor Information (captured at write time)
    actor_display_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Display name of actor at time of action"
    )
    actor_role = models.CharField(
        max_length=50,
        blank=True,
        help_text="Role of actor at time of action"
    )
    
    # Entity Display Name (human-readable entity reference)
    entity_display_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Human-readable entity name, e.g., 'Ticket #19 – Printer offline'"
    )
    
    # Structured Change Tracking
    changes = models.JSONField(
        null=True,
        blank=True,
        help_text="""
        Structured change data for audit:
        {
            "field_name": {
                "before": "old_value",
                "after": "new_value",
                "label": "Human readable field name"
            }
        }
        """
    )
    
    class Meta:
        db_table = 'activity_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['actor_id', 'timestamp']),
            models.Index(fields=['entity_type', 'entity_id', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['category', 'timestamp']),
        ]
```

---

## 2. Action Enumeration

### 2.1 Ticket Actions

```python
class TicketAction(Enum):
    TICKET_CREATED = 'TICKET_CREATED'
    TICKET_STATUS_CHANGED = 'TICKET_STATUS_CHANGED'
    TICKET_PRIORITY_CHANGED = 'TICKET_PRIORITY_CHANGED'
    TICKET_ASSIGNED = 'TICKET_ASSIGNED'
    TICKET_UNASSIGNED = 'TICKET_UNASSIGNED'
    TICKET_RESOLVED = 'TICKET_RESOLVED'
    TICKET_CLOSED = 'TICKET_CLOSED'
    TICKET_REOPENED = 'TICKET_REOPENED'
```

### 2.2 Asset Actions

```python
class AssetAction(Enum):
    ASSET_CREATED = 'ASSET_CREATED'
    ASSET_ASSIGNED = 'ASSET_ASSIGNED'
    ASSET_UNASSIGNED = 'ASSET_UNASSIGNED'
    ASSET_STATUS_CHANGED = 'ASSET_STATUS_CHANGED'
```

### 2.3 User Actions

```python
class UserAction(Enum):
    USER_CREATED = 'USER_CREATED'
    USER_ROLE_CHANGED = 'USER_ROLE_CHANGED'
    USER_DEACTIVATED = 'USER_DEACTIVATED'
    USER_REACTIVATED = 'USER_REACTIVATED'
```

---

## 3. Structured Logging Payloads

### 3.1 Ticket Status Change Example

**Use Case:** User changes ticket status from OPEN to IN_PROGRESS

```python
# In application layer (e.g., update_ticket.py)
from apps.logs.services.structured_payloads import log_ticket_status_changed

log_ticket_status_changed(
    actor=request.user,
    ticket=ticket_instance,
    from_status='OPEN',
    to_status='IN_PROGRESS',
    request=request
)
```

**Resulting Log Entry:**

```json
{
    "log_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-01-15T14:30:00-03:00",
    "actor_display_name": "Juan Pérez",
    "actor_role": "MANAGER",
    "action": "TICKET_STATUS_CHANGED",
    "entity_display_name": "Ticket #19 – Printer offline",
    "changes": {
        "status": {
            "before": "OPEN",
            "after": "IN_PROGRESS",
            "label": "Estado"
        }
    },
    "title": "Juan Pérez cambió el estado",
    "description": "Juan Pérez cambió el estado de OPEN a IN_PROGRESS",
    "extra_data": {
        "actor_id": 42,
        "actor_username": "juan.perez",
        "entity_display_name": "Ticket #19 – Printer offline"
    },
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
}
```

### 3.2 Asset Assignment Example

**Use Case:** Manager assigns a laptop to an employee

```python
from apps.logs.services.structured_payloads import log_asset_assigned

log_asset_assigned(
    actor=request.user,
    asset=laptop_instance,
    assignee=employee_instance,
    request=request
)
```

**Resulting Log Entry:**

```json
{
    "log_id": "550e8400-e29b-41d4-a716-446655440001",
    "timestamp": "2025-01-15T15:45:00-03:00",
    "actor_display_name": "Admin Sistema",
    "actor_role": "IT_ADMIN",
    "action": "ASSET_ASSIGNED",
    "entity_display_name": "Asset #LAPTOP-001 – MacBook Pro 16\"",
    "changes": {
        "assigned_to": {
            "before": null,
            "after": 15,
            "label": "Asignado a"
        }
    },
    "title": "Admin Sistema asignó el asset",
    "description": "Admin Sistema asignó Asset #LAPTOP-001 – MacBook Pro 16\" a María García",
    "extra_data": {
        "actor_id": 1,
        "actor_username": "admin",
        "entity_display_name": "Asset #LAPTOP-001 – MacBook Pro 16\"",
        "assignee_id": 15,
        "assignee_name": "María García"
    },
    "ip_address": "10.0.0.1",
    "user_agent": "Mozilla/5.0..."
}
```

### 3.3 User Role Change Example

**Use Case:** Admin promotes a technician to manager

```python
from apps.logs.services.structured_payloads import log_user_role_changed

log_user_role_changed(
    actor=request.user,
    target_user=technician_instance,
    from_role='TECHNICIAN',
    to_role='MANAGER',
    request=request
)
```

**Resulting Log Entry:**

```json
{
    "log_id": "550e8400-e29b-41d4-a716-446655440002",
    "timestamp": "2025-01-15T16:00:00-03:00",
    "actor_display_name": "Admin Sistema",
    "actor_role": "SUPERADMIN",
    "action": "USER_ROLE_CHANGED",
    "entity_display_name": "Usuario: carlos_rodriguez",
    "changes": {
        "role": {
            "before": "TECHNICIAN",
            "after": "MANAGER",
            "label": "Rol"
        }
    },
    "title": "Admin Sistema cambió el rol",
    "description": "Admin Sistema cambió el rol de TECHNICIAN a MANAGER",
    "level": "WARNING",
    "extra_data": {
        "actor_id": 1,
        "actor_username": "admin",
        "entity_display_name": "Usuario: carlos_rodriguez"
    },
    "ip_address": "10.0.0.1",
    "user_agent": "Mozilla/5.0..."
}
```

---

## 4. Activity Adapter Service

The ActivityAdapter transforms ActivityLog model instances into UI-ready data structures. This follows Clean Architecture by separating data transformation from presentation.

### 4.1 ActivityUIData Structure

```python
# apps/logs/services/activity_adapter.py

@dataclass
class ActivityUIData:
    """Frontend-ready activity data for Recent Activity UI."""
    log_id: str
    timestamp: datetime
    timestamp_iso: str
    timestamp_relative: str  # "5 minutes ago"
    
    # Actor (WHO)
    actor_id: Optional[int]
    actor_display_name: str
    actor_role: str
    actor_url: Optional[str]  # /users/{id}/
    
    # Action (WHAT - verb phrase)
    action_key: str
    action_verb: str  # "cambió el estado"
    action_icon: str  # "fa-exchange-alt"
    action_color: str  # "text-blue-600"
    action_bg_color: str  # "bg-blue-100"
    
    # Entity (WHICH - target noun phrase)
    entity_type: str
    entity_id: Optional[int]
    entity_display_name: str  # "Ticket #19 – Printer offline"
    entity_url: Optional[str]  # /tickets/19/
    
    # Changes (CONTEXT)
    changes_summary: Optional[str]  # "Estado: OPEN → IN_PROGRESS"
    changes_detail: Optional[Dict]
    
    # Category for styling
    category: str
    level: str
    
    # UI flags
    is_clickable: bool
    is_error: bool
```

### 4.2 Action Configuration

```python
ACTION_CONFIG = {
    'TICKET_STATUS_CHANGED': {
        'verb': 'cambió el estado',
        'icon': 'fa-exchange-alt',
        'color': 'text-blue-600',
        'bg_color': 'bg-blue-100',
        'entity_type': 'Ticket',
    },
    'ASSET_ASSIGNED': {
        'verb': 'asignó el asset',
        'icon': 'fa-hand-paper',
        'color': 'text-orange-600',
        'bg_color': 'bg-orange-100',
        'entity_type': 'Asset',
    },
    'USER_ROLE_CHANGED': {
        'verb': 'cambió el rol',
        'icon': 'fa-user-shield',
        'color': 'text-red-600',
        'bg_color': 'bg-red-100',
        'entity_type': 'User',
    },
    # ... more actions
}
```

### 4.3 Adapter Usage

```python
from apps.logs.services.activity_adapter import ActivityAdapter

# In views.py
def dashboard_view(request):
    activities = ActivityLog.objects.order_by('-timestamp')[:10]
    
    # Transform for template
    adapted_activities = [
        ActivityAdapter.to_ui(activity) 
        for activity in activities
    ]
    
    return render(request, 'dashboard.html', {
        'recent_activities': adapted_activities
    })
```

---

## 5. UI Rendering Rules

### 5.1 Dashboard Recent Activity Template

```html
<!-- templates/frontend/dashboard.html - Recent Activity Section -->

{% for activity in recent_activities %}
{% if activity.is_clickable and activity.entity_url %}
<a href="{{ activity.entity_url }}" 
   class="flex items-start gap-3 p-3 hover:bg-gray-50 rounded-lg transition-colors block">
{% else %}
<div class="flex items-start gap-3 p-3 rounded-lg {% if activity.is_error %}bg-red-50{% else %}hover:bg-gray-50{% endif %}">
{% endif %}
    
    <!-- Actor Avatar -->
    <div class="flex-shrink-0">
        {% if activity.actor_id %}
        <a href="{{ activity.actor_url }}" class="block">
            <div class="w-8 h-8 rounded-full {{ activity.action_bg_color }} flex items-center justify-center">
                <span class="text-sm font-medium {{ activity.action_color }}">
                    {{ activity.actor_display_name|first|upper }}
                </span>
            </div>
        </a>
        {% else %}
        <div class="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
            <i class="fas fa-robot text-gray-400 text-sm"></i>
        </div>
        {% endif %}
    </div>
    
    <!-- Main Content -->
    <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 flex-wrap">
            <!-- Actor -->
            <a href="{{ activity.actor_url }}" 
               class="text-sm font-medium text-gray-900 hover:text-primary-600">
                {{ activity.actor_display_name }}
            </a>
            
            <!-- Action Verb -->
            <span class="text-sm text-gray-600">
                {{ activity.action_verb }}
            </span>
            
            <!-- Entity Link -->
            {% if activity.is_clickable and activity.entity_url %}
            <a href="{{ activity.entity_url }}" 
               class="text-sm font-medium text-primary-600 hover:underline truncate">
                {{ activity.entity_display_name }}
            </a>
            {% else %}
            <span class="text-sm font-medium text-gray-900 truncate">
                {{ activity.entity_display_name }}
            </span>
            {% endif %}
        </div>
        
        <!-- Changes Summary -->
        {% if activity.changes_summary %}
        <div class="mt-1 text-xs text-gray-500">
            <span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                {{ activity.changes_summary }}
            </span>
        </div>
        {% endif %}
        
        <!-- Timestamp & Category -->
        <div class="mt-1 flex items-center gap-2 text-xs text-gray-500">
            <span>{{ activity.timestamp_relative }}</span>
            
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium
                {% if activity.category == 'TICKET' %}bg-blue-100 text-blue-800
                {% elif activity.category == 'ASSET' %}bg-green-100 text-green-800
                {% elif activity.category == 'USER' %}bg-purple-100 text-purple-800
                {% elif activity.category == 'SECURITY' %}bg-red-100 text-red-800
                {% else %}bg-gray-100 text-gray-800{% endif %}">
                {{ activity.category }}
            </span>
        </div>
    </div>
    
    <!-- Action Icon -->
    <div class="flex-shrink-0">
        <div class="w-8 h-8 rounded-full {{ activity.action_bg_color }} flex items-center justify-center">
            <i class="fas {{ activity.action_icon }} {{ activity.action_color }} text-sm"></i>
        </div>
    </div>
    
{% if activity.is_clickable and activity.entity_url %}
</a>
{% else %}
</div>
{% endif %}
{% endfor %}
```

### 5.2 Expected Output

**Before (Generic):**
```
❌ "Ticket updated (ID 19)"
❌ "User updated"
❌ "Asset updated"
```

**After (Professional):**
```
✅ "Juan Pérez cambió el estado de Ticket #19 – Printer offline (Estado: OPEN → IN_PROGRESS)"
✅ "Admin Sistema cambió el rol de Usuario: carlos_rodriguez (Rol: TECHNICIAN → MANAGER)"
✅ "Juan Pérez asignó el asset Asset #LAPTOP-001 – MacBook Pro 16\" a María García"
```

---

## 6. Structured Logging Functions Reference

### 6.1 Ticket Logging Functions

```python
# Log ticket creation
log_ticket_created(actor, ticket, request=None)

# Log status change with from/to values
log_ticket_status_changed(actor, ticket, from_status, to_status, request=None)

# Log priority change with from/to values  
log_ticket_priority_changed(actor, ticket, from_priority, to_priority, request=None)

# Log assignment with assignee info
log_ticket_assigned(actor, ticket, assignee, request=None)
```

### 6.2 Asset Logging Functions

```python
# Log asset creation
log_asset_created(actor, asset, request=None)

# Log asset assignment
log_asset_assigned(actor, asset, assignee, request=None)

# Log asset unassignment
log_asset_unassigned(actor, asset, previous_assignee, request=None)

# Log status change
log_asset_status_changed(actor, asset, from_status, to_status, request=None)
```

### 6.3 User Logging Functions

```python
# Log user creation
log_user_created(actor, target_user, request=None)

# Log role change (security-sensitive, logs as WARNING)
log_user_role_changed(actor, target_user, from_role, to_role, request=None)

# Log deactivation (security-sensitive)
log_user_deactivated(actor, target_user, request=None)
```

---

## 7. Implementation Checklist

### 7.1 Backend Tasks

| Task | Status | File |
|------|--------|------|
| Add new model fields (actor_display_name, entity_display_name, changes) | ☐ | `apps/logs/models.py` |
| Create ActivityUIData dataclass | ✅ | `apps/logs/services/activity_adapter.py` |
| Create ActivityAdapter.to_ui() method | ✅ | `apps/logs/services/activity_adapter.py` |
| Create structured logging functions | ✅ | `apps/logs/services/structured_payloads.py` |
| Create migration for new fields | ☐ | `apps/logs/migrations/` |
| Update dashboard view to use adapter | ☐ | `apps/frontend/views/dashboard.py` |

### 7.2 Frontend Tasks

| Task | Status | File |
|------|--------|------|
| Update dashboard template with new rendering | ☐ | `templates/frontend/dashboard.html` |
| Remove generic activity messages | ☐ | All templates |
| Add activity detail view | ☐ | `templates/frontend/activity_detail.html` |

### 7.3 Migration Tasks

| Task | Status | File |
|------|--------|------|
| Create database migration | ☐ | `apps/logs/migrations/` |
| Backfill actor_display_name from existing logs | ☐ | Migration script |
| Test backward compatibility | ☐ | Tests |

---

## 8. Acceptance Criteria

### 8.1 Must Have

- [ ] No more generic messages like "Ticket updated (ID 19)"
- [ ] Every entry reads as: "WHO did WHAT to WHICH entity"
- [ ] Before/after changes are displayed when available
- [ ] Entire row is clickable → entity detail page
- [ ] Icons and colors by category (Ticket=Blue, Asset=Green, User=Purple, Security=Red)
- [ ] Logs are suitable for audit, security review, and compliance reporting
- [ ] No business logic in templates
- [ ] Clean Architecture boundaries respected

### 8.2 Should Have

- [ ] Localized timestamps (Argentina timezone)
- [ ] Actor display names with clickable profile links
- [ ] Category badges with appropriate styling
- [ ] Error/Warning level differentiation

### 8.3 Nice to Have

- [ ] Activity detail modal with full change history
- [ ] Filter by category/action in dashboard
- [ ] Real-time updates via WebSocket

---

## 9. Backward Compatibility

The system maintains backward compatibility:

1. **Existing logs**: Continue to work with fallback values
2. **Extra data field**: New structured data is stored in `extra_data.changes`
3. **Adapter handles missing fields**: Uses getattr with defaults for old logs
4. **Template compatibility**: Can fall back to old fields (title, description) if new fields are empty

Example fallback in adapter:
```python
entity_display_name = (
    getattr(activity_log, 'entity_display_name', None)
    or activity_log.object_repr
    or f"{activity_log.model_name} #{activity_log.object_id}"
)
```

---

## 10. Summary

This design provides:

1. **Structured Logging** - All data captured at write time in consistent format
2. **Human-Readable Messages** - Pre-generated, localized messages
3. **Complete Change Tracking** - Before/after values for every field
4. **Security Metadata** - IP, user-agent, request path
5. **Clean UI** - Professional, clickable activity rows with icons and colors
6. **Audit Compliance** - Immutable records suitable for compliance reporting
7. **Clean Architecture** - Separation of concerns between logging, adapting, and rendering

