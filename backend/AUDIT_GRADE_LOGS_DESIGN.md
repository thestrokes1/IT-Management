# Audit-Grade Activity Logs Design

This document specifies the redesigned activity logging system for professional audit trails, traceability, and compliance.

---

## 1. Root Cause Analysis

### Problem Identified

Activity logs were being created on **read operations** (page views) instead of only on **write operations** (creates, updates, deletes).

**Symptoms:**
- Opening `/users/<id>/edit/` generated activity logs without changes
- Messages like "Asset assigned from Unassigned to Martin" appeared without actual assignment
- Recent Activity dashboard showed incorrect entries

**Root Cause:**
1. `log_model_changes` signal fired on every `post_save` event, including updates
2. Generic handlers created logs with format `"{Model}_UPDATED (ID {pk})"` even when no fields changed
3. Views called `model.save()` without checking if values actually changed

---

## 2. Fixed Signal Handlers

### 2.1 logs/signals.py - Critical Safeguards Added

```python
@receiver(post_save, dispatch_uid="log_model_changes")
def log_model_changes(sender, instance, created, **kwargs):
    """
    Generic handler for model create/update operations.
    
    CRITICAL SAFEGUARDS:
    1. Skip if model is in LOG_MODELS (prevents recursive logging)
    2. Skip if model is not from our apps
    3. Only log on CREATED, NOT on updates
    4. Updates must use explicit update_fields to be logged
    
    This prevents logs from appearing when simply viewing data.
    """
    # Skip log models to prevent recursive logging
    if sender.__name__ in LOG_MODELS:
        return

    # Skip non-app models (e.g., django.contrib.auth)
    if not sender.__module__.startswith('apps.'):
        return

    # ONLY log creations, NOT updates
    # Updates should be explicitly logged by use cases
    if not created:
        return
```

### 2.2 User Edit View - update_fields Guard

```python
def post(self, request, *args, **kwargs):
    user = self.edit_user
    
    # Track which fields actually changed
    changed_fields = []
    
    # Check each field for changes BEFORE saving
    new_email = request.POST.get('email', user.email)
    if user.email != new_email:
        user.email = new_email
        changed_fields.append('email')
    
    # ... similar for other fields ...
    
    # Only save if something actually changed
    if changed_fields:
        user.save(update_fields=changed_fields)
        messages.success(request, 'User updated.')
    else:
        messages.info(request, 'No changes were made.')
```

---

## 3. ActivityLog Model Schema

```python
class ActivityLog(models.Model):
    """
    Activity log model for the IT Management Platform.
    
    Key Fields for Audit-Grade Logging:
    - user: FK to User (actor)
    - action: Action type (TICKET_CREATED, ASSET_ASSIGNED, etc.)
    - title: Human-readable summary
    - description: Detailed description
    - model_name: Django model name (Ticket, Asset, etc.)
    - object_id: ID of affected object
    - object_repr: String representation
    - timestamp: Time of action (canonical field)
    - extra_data: JSON for structured data (changes, actor info)
    """
    
    # Log ID (unique identifier)
    log_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Actor Information
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Action Information
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    level = models.CharField(max_length=10, default='INFO')
    category = models.ForeignKey(LogCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Activity Details
    title = models.CharField(max_length=200)  # Human-readable summary
    description = models.TextField()  # Detailed description
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=255, blank=True)
    
    # Request Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Structured Data (actor info, changes)
    extra_data = models.JSONField(default=dict, blank=True)
    
    # Timestamp (canonical, immutable)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
```

---

## 4. Structured Logging Payloads

### 4.1 Structured Payloads Module

The `structured_payloads.py` module provides logging functions that generate human-readable messages at write time.

**Example: Ticket Status Change**

```python
def log_ticket_status_changed(
    actor,
    ticket_id: int,
    title: str,
    from_status: str,
    to_status: str,
    request=None
):
    """
    Log ticket status change with structured payload.
    
    Creates ActivityLog entry with:
    - title: "Juan Pérez cambió el estado de OPEN a IN_PROGRESS en Ticket #19 – Printer offline"
    - extra_data: {
        "actor_id": 42,
        "actor_username": "juan_perez",
        "actor_role": "MANAGER",
        "changes": {
            "status": {"before": "OPEN", "after": "IN_PROGRESS", "label": "Estado"}
        },
        "changes_summary": "Estado: OPEN → IN_PROGRESS"
    }
    """
```

### 4.2 ChangeSet Data Class

```python
@dataclass
class ChangeSet:
    """Represents multiple field changes with before/after values."""
    changes: Dict[str, FieldChange] = field(default_factory=dict)
    
    def add(self, field_name: str, before: Any, after: Any, label: str = ""):
        """Add a field change."""
        self.changes[field_name] = FieldChange(
            before=before,
            after=after,
            label=label or field_name.replace('_', ' ').title()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            name: change.to_dict() 
            for name, change in self.changes.items()
        }
    
    def to_summary(self) -> Optional[str]:
        """Generate human-readable summary: 'Estado: OPEN → IN_PROGRESS'"""
```

### 4.3 Available Logging Functions

```python
# Ticket operations
log_ticket_created(actor, ticket_id, title, priority, category_name, request)
log_ticket_status_changed(actor, ticket_id, title, from_status, to_status, request)
log_ticket_assigned(actor, ticket_id, title, assignee_username, request)

# Asset operations
log_asset_created(actor, asset_id, name, asset_type, status, request)
log_asset_assigned(actor, asset_id, name, assignee_username, request)
log_asset_status_changed(actor, asset_id, name, from_status, to_status, request)

# User operations
log_user_created(actor, user_id, username, role, request)
log_user_role_changed(actor, user_id, username, from_role, to_role, request)

# Project operations
log_project_created(actor, project_id, name, request)
log_project_member_added(actor, project_id, project_name, member_username, role, request)

# Auth operations
log_user_login(user, request)
log_user_logout(user, request)
```

---

## 5. ActivityAdapter - UI Transformation

### 5.1 ActivityUIData DTO

```python
@dataclass
class ActivityUIData:
    """Frontend-ready activity data for Recent Activity UI."""
    
    # Identifiers
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
    action_verb: str  # "cambió el estado del ticket"
    action_icon: str  # "fa-exchange-alt"
    action_color: str  # "text-blue-600"
    
    # Entity (WHICH - target noun phrase)
    entity_type: str
    entity_id: Optional[int]
    entity_display_name: str  # "Ticket #19 – Printer offline"
    entity_url: Optional[str]  # /tickets/19/
    
    # Changes (CONTEXT)
    changes_summary: Optional[str]  # "Estado: OPEN → RESOLVED"
    changes_detail: Optional[Dict]
    
    # Category & Level
    category: str
    level: str
    
    # Computed flags
    is_clickable: bool
    is_error: bool
```

### 5.2 Action Configuration

```python
ACTION_CONFIG = {
    'TICKET_STATUS_CHANGED': {
        'verb': 'cambió el estado del ticket',
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
        'verb': 'cambió el rol del usuario',
        'icon': 'fa-user-shield',
        'color': 'text-red-600',
        'bg_color': 'bg-red-100',
        'entity_type': 'User',
    },
    # ... more actions
}
```

### 5.3 Adapter Usage

```python
from apps.logs.services.activity_adapter import ActivityAdapter, get_recent_activities_for_dashboard

# In view
recent_activities = get_recent_activities_for_dashboard(request.user, limit=10)

# In template - each activity is an ActivityUIData object
{% for activity in recent_activities %}
    {{ activity.actor_display_name }} 
    {{ activity.action_verb }}
    <a href="{{ activity.entity_url }}">{{ activity.entity_display_name }}</a>
{% endfor %}
```

---

## 6. Frontend UI Rendering

### 6.1 Dashboard Recent Activity Template

```html
{% for activity in recent_activities %}
{% with ui=activity %}

{% if ui.is_clickable and ui.entity_url %}
<a href="{{ ui.entity_url }}" class="activity-row">
{% else %}
<div class="activity-row">
{% endif %}

    <!-- Actor Avatar -->
    <div class="actor-avatar">
        {% if ui.actor_id %}
        <a href="{{ ui.actor_url }}">
            <div class="w-10 h-10 rounded-full {{ ui.action_bg_color }} flex items-center justify-center">
                <span class="{{ ui.action_color }}">{{ ui.actor_display_name|first|upper }}</span>
            </div>
        </a>
        {% endif %}
    </div>
    
    <!-- Main Content -->
    <div class="activity-content">
        <!-- WHO did WHAT to WHICH -->
        <p class="activity-text">
            <span class="font-medium">{{ ui.actor_display_name }}</span>
            <span class="{{ ui.action_color }}">{{ ui.action_verb }}</span>
            <a href="{{ ui.entity_url }}" class="font-medium text-primary-600 hover:underline">
                {{ ui.entity_display_name }}
            </a>
        </p>
        
        <!-- Changes Summary -->
        {% if ui.changes_summary %}
        <p class="changes-summary">
            {{ ui.changes_summary }}
        </p>
        {% endif %}
        
        <!-- Timestamp & Category -->
        <div class="activity-meta">
            <span class="text-gray-500">{{ ui.timestamp_relative }}</span>
            <span class="category-badge category-{{ ui.category|lower }}">
                {{ ui.category }}
            </span>
        </div>
    </div>
    
    <!-- Action Icon -->
    <div class="activity-icon">
        <div class="w-10 h-10 rounded-full {{ ui.action_bg_color }} flex items-center justify-center">
            <i class="fas {{ ui.action_icon }} {{ ui.action_color }}"></i>
        </div>
    </div>

{% if ui.is_clickable and ui.entity_url %}
</a>
{% else %}
</div>
{% endif %}

{% endwith %}
{% empty %}
<p class="no-activity">No hay actividad reciente</p>
{% endfor %}
```

### 6.2 CSS Classes for Styling

```css
.activity-row {
    @apply flex items-start gap-3 p-4 hover:bg-gray-50 rounded-lg transition-colors;
}

.activity-text {
    @apply text-sm text-gray-900;
}

.action-verb {
    @apply font-medium;
}

.entity-link {
    @apply text-primary-600 hover:underline;
}

.changes-summary {
    @apply mt-1 text-xs text-gray-500;
}

.category-badge {
    @apply inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium;
}

.category-ticket {
    @apply bg-blue-100 text-blue-800;
}

.category-asset {
    @apply bg-green-100 text-green-800;
}

.category-user {
    @apply bg-purple-100 text-purple-800;
}

.category-security {
    @apply bg-red-100 text-red-800;
}
```

---

## 7. Implementation Checklist

### 7.1 Completed ✓

| Task | Status |
|------|--------|
| Fixed signal handlers to only log on CREATED | ✓ |
| Added update_fields guard in EditUserView | ✓ |
| Added change detection before save | ✓ |
| Created ActivityAdapter for UI transformation | ✓ |
| Created structured_payloads.py | ✓ |
| Added ActionConfig for UI display | ✓ |

### 7.2 Pending

| Task | Status |
|------|--------|
| Update ticket views to use structured payloads | ☐ |
| Update asset views to use structured payloads | ☐ |
| Update project views to use structured payloads | ☐ |
| Update dashboard to use ActivityAdapter | ☐ |
| Add tests for logging behavior | ☐ |

---

## 8. Backward Compatibility

The changes maintain backward compatibility:
- Existing ActivityLog fields remain unchanged
- New structured fields (in extra_data) are nullable
- Old logs render with fallback values
- ActivityAdapter handles both old and new formats

---

## 9. Summary

### Key Principles

1. **Logs are immutable** - Created once, never modified
2. **Structure at write time** - Human-readable messages generated when logging
3. **No inference in templates** - Templates only render pre-computed data
4. **RBAC respected** - Views use adapter for UI, not business logic

### What Was Fixed

| Before (Broken) | After (Fixed) |
|-----------------|---------------|
| Opening edit page creates log | No log created |
| Generic "User_UPDATED (ID X)" | "Juan Pérez cambió el rol..." |
| No before/after tracking | Changes stored in JSON |
| Template guesses meaning | Adapter provides all data |

### Result

**Before:**
```
❌ "Ticket updated (ID 19)"
❌ Opening /users/5/edit/ → creates log with no changes
```

**After:**
```
✅ "Juan Pérez cambió el estado de OPEN a IN_PROGRESS en Ticket #19 – Printer offline"
✅ Changes: {"status": {"before": "OPEN", "after": "IN_PROGRESS", "label": "Estado"}}
✅ Opening edit page → NO LOG (no changes detected)
```

Activity logs now:
- Only created on actual write operations
- Include structured before/after values
- Generate human-readable messages at write time
- Suitable for audit, security review, and compliance

