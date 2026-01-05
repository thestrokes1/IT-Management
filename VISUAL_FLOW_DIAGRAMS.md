# IT Management Platform - Visual Flow Diagrams
**Last Updated:** January 2025

---

## Dashboard Flow

```
┌─────────────────────────────────────────────────────────┐
│                    DASHBOARD                             │
│  ┌────────────────────────────────────────────────────┐ │
│  │         QUICK ACTIONS (Fixed!)                     │ │
│  │                                                    │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │ │
│  │  │   Create     │  │   New        │  │   Add    │ │ │
│  │  │   Ticket     │  │   Project    │  │   Asset  │ │ │
│  │  └──────────────┘  └──────────────┘  └──────────┘ │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
         │                    │                    │
         │                    │                    │
         v                    v                    v
   /tickets/create/    /projects/create/    /assets/create/
```

---

## Ticket Creation Flow

```
┌─────────────────────────────────────────────────────┐
│          CREATE TICKET PAGE                         │
│                                                     │
│  Method: GET  → Display form                        │
│  Method: POST → Process submission                  │
│                                                     │
│  Form Fields:                                       │
│  ├─ Title (required)                               │
│  ├─ Category (required)                            │
│  ├─ Ticket Type (optional)                         │
│  ├─ Priority (required)                            │
│  ├─ Description (required)                         │
│  ├─ Impact (optional)                              │
│  ├─ Urgency (optional)                             │
│  ├─ Assigned To (optional)                         │
│  ├─ Due Date/SLA (optional)                        │
│  └─ Requester (auto-filled)                        │
│                                                     │
│  [Submit] [Cancel]                                 │
└─────────────────────────────────────────────────────┘
         │                              │
    [Submit]                       [Cancel]
         │                              │
         v                              v
  ┌──────────────┐            ┌──────────────┐
  │ Validate     │            │ Back to      │
  │ Form Data    │            │ Tickets List │
  └──────────────┘            └──────────────┘
         │
         v
  ┌──────────────┐
  │ Create DB    │
  │ Record       │
  │ (Status: NEW)│
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Show Success │
  │ Message      │
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Redirect to  │
  │ Tickets List │
  └──────────────┘
```

---

## Ticket Edit Flow

```
┌─────────────────────────────────────────────────────┐
│          EDIT TICKET PAGE                           │
│                                                     │
│  Method: GET  → Load ticket data                    │
│  Method: POST → Process update                      │
│                                                     │
│  Form Fields:                                       │
│  ├─ Title (required)                               │
│  ├─ Category (required)                            │
│  ├─ Status (required)                              │
│  ├─ Priority (required)                            │
│  ├─ Description (required)                         │
│  ├─ Impact/Urgency (optional)                      │
│  ├─ Assigned To (optional)                         │
│  ├─ Assigned Team (optional)                       │
│  ├─ SLA Due Date (optional)                        │
│  ├─ Resolution Summary (optional)                  │
│  └─ Location/Contact (optional)                    │
│                                                     │
│  [Update] [Cancel]                                 │
└─────────────────────────────────────────────────────┘
         │                              │
    [Update]                       [Cancel]
         │                              │
         v                              v
  ┌──────────────┐            ┌──────────────┐
  │ Validate     │            │ Back to      │
  │ Form Data    │            │ Tickets List │
  └──────────────┘            └──────────────┘
         │
         v
  ┌──────────────┐
  │ Update DB    │
  │ Record       │
  │ (update_at)  │
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Show Success │
  │ Message      │
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Redirect to  │
  │ Tickets List │
  └──────────────┘
```

---

## Project Creation Flow

```
┌─────────────────────────────────────────────────────┐
│       CREATE PROJECT PAGE                           │
│                                                     │
│  Method: GET  → Display form                        │
│  Method: POST → Process submission                  │
│                                                     │
│  Form Fields:                                       │
│  ├─ Name (required)                                │
│  ├─ Category (required)                            │
│  ├─ Priority (required)                            │
│  ├─ Description (required)                         │
│  ├─ Project Manager (required)                     │
│  ├─ Objectives (optional)                          │
│  ├─ Requirements (optional)                        │
│  ├─ Deliverables (optional)                        │
│  ├─ Start Date (optional)                          │
│  ├─ End Date (optional)                            │
│  ├─ Deadline (optional)                            │
│  ├─ Budget (optional)                              │
│  ├─ Risk Level (optional)                          │
│  └─ Risk Description (optional)                    │
│                                                     │
│  [Create Project] [Cancel]                         │
└─────────────────────────────────────────────────────┘
         │                              │
    [Submit]                       [Cancel]
         │                              │
         v                              v
  ┌──────────────┐            ┌──────────────┐
  │ Validate     │            │ Back to      │
  │ Form Data    │            │ Projects List│
  └──────────────┘            └──────────────┘
         │
         v
  ┌──────────────┐
  │ Create DB    │
  │ Record       │
  │ (Status: PL.)│
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Show Success │
  │ Message      │
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Redirect to  │
  │ Projects List│
  └──────────────┘
```

---

## Project Edit Flow

```
┌─────────────────────────────────────────────────────┐
│       EDIT PROJECT PAGE                             │
│                                                     │
│  Method: GET  → Load project data                   │
│  Method: POST → Process update                      │
│                                                     │
│  Form Fields:                                       │
│  ├─ Name (required)                                │
│  ├─ Category (required)                            │
│  ├─ Status (required)                              │
│  ├─ Priority (required)                            │
│  ├─ Description (required)                         │
│  ├─ Project Manager (required)                     │
│  ├─ Objectives/Requirements/Deliverables           │
│  ├─ Start/End/Deadline Dates                       │
│  ├─ Budget (optional)                              │
│  ├─ Risk Level/Description                         │
│  └─ Updated By (auto-set)                          │
│                                                     │
│  [Update Project] [Cancel]                         │
└─────────────────────────────────────────────────────┘
         │                              │
    [Update]                       [Cancel]
         │                              │
         v                              v
  ┌──────────────┐            ┌──────────────┐
  │ Validate     │            │ Back to      │
  │ Form Data    │            │ Projects List│
  └──────────────┘            └──────────────┘
         │
         v
  ┌──────────────┐
  │ Update DB    │
  │ Record       │
  │ (update_by)  │
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Show Success │
  │ Message      │
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Redirect to  │
  │ Projects List│
  └──────────────┘
```

---

## Asset Creation Flow

```
┌─────────────────────────────────────────────────────┐
│        CREATE ASSET PAGE                            │
│                                                     │
│  Method: GET  → Display form                        │
│  Method: POST → Process submission                  │
│                                                     │
│  Form Fields:                                       │
│  ├─ Name (required)                                │
│  ├─ Type (required): Hardware/Software              │
│  ├─ Category (required)                            │
│  ├─ Status (required)                              │
│  ├─ Description (optional)                         │
│  ├─ Serial Number (optional)                       │
│  ├─ Model (optional)                               │
│  ├─ Manufacturer (optional)                        │
│  ├─ Version (optional)                             │
│  ├─ Purchase Date (optional)                       │
│  ├─ Purchase Cost (optional)                       │
│  ├─ Warranty Expiry (optional)                     │
│  ├─ End of Life (optional)                         │
│  ├─ Assigned To (optional)                         │
│  └─ Location (optional)                            │
│                                                     │
│  [Add Asset] [Cancel]                              │
└─────────────────────────────────────────────────────┘
         │                              │
    [Submit]                       [Cancel]
         │                              │
         v                              v
  ┌──────────────┐            ┌──────────────┐
  │ Validate     │            │ Back to      │
  │ Form Data    │            │ Assets List  │
  └──────────────┘            └──────────────┘
         │
         v
  ┌──────────────┐
  │ Create DB    │
  │ Record       │
  │ (Status: ACT)│
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Show Success │
  │ Message      │
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Redirect to  │
  │ Assets List  │
  └──────────────┘
```

---

## Asset Edit Flow

```
┌─────────────────────────────────────────────────────┐
│        EDIT ASSET PAGE                              │
│                                                     │
│  Method: GET  → Load asset data                     │
│  Method: POST → Process update                      │
│                                                     │
│  Form Fields:                                       │
│  ├─ Name (required)                                │
│  ├─ Asset Tag (required)                           │
│  ├─ Type (required)                                │
│  ├─ Category (required)                            │
│  ├─ Status (required)                              │
│  ├─ Description (optional)                         │
│  ├─ Serial Number (optional)                       │
│  ├─ Model/Manufacturer/Version                     │
│  ├─ Assigned To (optional)                         │
│  ├─ Location (optional)                            │
│  ├─ Purchase Info (optional)                       │
│  └─ Warranty Expiry (optional)                     │
│                                                     │
│  [Update Asset] [Cancel]                           │
└─────────────────────────────────────────────────────┘
         │                              │
    [Update]                       [Cancel]
         │                              │
         v                              v
  ┌──────────────┐            ┌──────────────┐
  │ Validate     │            │ Back to      │
  │ Form Data    │            │ Assets List  │
  └──────────────┘            └──────────────┘
         │
         v
  ┌──────────────┐
  │ Update DB    │
  │ Record       │
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Show Success │
  │ Message      │
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Redirect to  │
  │ Assets List  │
  └──────────────┘
```

---

## User Creation Flow

```
┌─────────────────────────────────────────────────────┐
│       CREATE USER PAGE                              │
│                                                     │
│  Method: GET  → Display form (admin only)           │
│  Method: POST → Process submission                  │
│                                                     │
│  Access Control:                                    │
│  └─ can_manage_users required                       │
│     (SUPERADMIN, IT_ADMIN roles)                   │
│                                                     │
│  Form Fields:                                       │
│  ├─ Username (required, unique)                    │
│  ├─ Email (required, unique)                       │
│  ├─ Password (required, min 8 chars)               │
│  ├─ Password Confirm (required)                    │
│  ├─ First Name (optional)                          │
│  ├─ Last Name (optional)                           │
│  ├─ Role (required) - VIEWER default               │
│  └─ Is Active (checkbox)                           │
│                                                     │
│  [Create User] [Cancel]                            │
└─────────────────────────────────────────────────────┘
         │                              │
    [Create]                       [Cancel]
         │                              │
         v                              v
  ┌──────────────┐            ┌──────────────┐
  │ Validate     │            │ Back to      │
  │ Permissions  │            │ Users List   │
  └──────────────┘            └──────────────┘
         │
         v
  ┌──────────────┐
  │ Validate     │
  │ Form Data    │
  │ (unique,     │
  │  min length) │
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Create DB    │
  │ Record       │
  │ (auto emp_id)│
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Show Success │
  │ Message      │
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Redirect to  │
  │ Users List   │
  └──────────────┘
```

---

## User Edit Flow

```
┌─────────────────────────────────────────────────────┐
│       EDIT USER PAGE                                │
│                                                     │
│  Method: GET  → Load user data                      │
│  Method: POST → Process update                      │
│                                                     │
│  Access Control:                                    │
│  ├─ can_manage_users required (role/status/role)   │
│  └─ OR editing own profile                         │
│                                                     │
│  Form Fields (Admin):                               │
│  ├─ Email (required)                               │
│  ├─ Password (optional - change)                   │
│  ├─ Password Confirm (if changing)                 │
│  ├─ First Name/Last Name                           │
│  ├─ Role (required)                                │
│  └─ Is Active (checkbox)                           │
│                                                     │
│  Form Fields (Self-Edit):                           │
│  ├─ Email (required)                               │
│  ├─ Password (optional)                            │
│  ├─ First Name/Last Name                           │
│  └─ (No role/status changes)                       │
│                                                     │
│  [Update User] [Cancel]                            │
└─────────────────────────────────────────────────────┘
         │                              │
    [Update]                       [Cancel]
         │                              │
         v                              v
  ┌──────────────┐            ┌──────────────┐
  │ Validate     │            │ Back to      │
  │ Permissions  │            │ Users List   │
  └──────────────┘            └──────────────┘
         │
         v
  ┌──────────────┐
  │ Validate     │
  │ Form Data    │
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Update DB    │
  │ Record       │
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Show Success │
  │ Message      │
  └──────────────┘
         │
         v
  ┌──────────────┐
  │ Redirect to  │
  │ Users List   │
  └──────────────┘
```

---

## User Delete Flow

```
┌─────────────────────────────────────────────────────┐
│       USER DELETE OPERATION                         │
│                                                     │
│  Method: DELETE (API) / POST (form)                 │
│                                                     │
│  Access Control:                                    │
│  ├─ Authentication required                         │
│  ├─ Role must be ADMIN or SUPERADMIN               │
│  └─ Cannot delete self                             │
│                                                     │
└─────────────────────────────────────────────────────┘
         │
         v
  ┌──────────────────────────────────────┐
  │ Check Authentication & Permissions    │
  └──────────────────────────────────────┘
         │
    Invalid?     Valid?
     │              │
     v              v
  ┌──────────┐  ┌───────────────────┐
  │ 403/401  │  │ Check not self    │
  │ Response │  └───────────────────┘
  └──────────┘         │
                 Self?   Not Self?
                   │         │
                   v         v
              ┌────────┐  ┌─────────────┐
              │ Error  │  │ Delete User │
              │ (400)  │  │ from DB     │
              └────────┘  └─────────────┘
                            │
                            v
                    ┌───────────────┐
                    │ Return 204/   │
                    │ JSON success  │
                    └───────────────┘
```

---

## Profile View Flow

```
┌─────────────────────────────────────────────────────┐
│           PROFILE PAGE                              │
│                                                     │
│  Method: GET  → Display current user info           │
│  LoginRequiredMixin → Redirect if not logged in    │
│                                                     │
│  Information Displayed:                             │
│  ├─ Username                                       │
│  ├─ Email                                          │
│  ├─ Full Name                                      │
│  ├─ Role (with display name)                       │
│  ├─ Status                                         │
│  ├─ Department/Job Title                           │
│  ├─ Employee ID (auto-generated)                   │
│  ├─ Phone Number                                   │
│  ├─ Last Login                                     │
│  └─ Account Dates (created/updated)                │
│                                                     │
│  Actions:                                           │
│  └─ [Edit Profile] → EditUserView                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Global Search API Flow

```
┌─────────────────────────────────────────────────────┐
│          GLOBAL SEARCH API                          │
│  Endpoint: /api/search/?q=query&type=all            │
│                                                     │
│  Query Parameters:                                  │
│  ├─ q (required): Search term                       │
│  └─ type (optional): users/assets/projects/tickets  │
│                                                     │
└─────────────────────────────────────────────────────┘
         │
         v
  ┌──────────────────────────────────────┐
  │ Extract query and search type         │
  └──────────────────────────────────────┘
         │
         v
  ┌──────────────────────────────────────┐
  │ Search Each Category (if 'all' or    │
  │ specific type):                      │
│  ├─ Users: username, email, role       │
│  ├─ Assets: name, tag, category        │
│  ├─ Projects: name, status, priority   │
│  └─ Tickets: title, status, priority   │
  └──────────────────────────────────────┘
         │
         v
  ┌──────────────────────────────────────┐
  │ Return JSON Response:                │
│  {                                    │
│    "query": "search term",            │
│    "results": {                       │
│      "users": [...],                  │
│      "assets": [...],                 │
│      "projects": [...],               │
│      "tickets": [...]                 │
│    },                                 │
│    "count": total_results             │
│  }                                    │
  └──────────────────────────────────────┘
```

---

## Quick Actions API Flow

```
┌─────────────────────────────────────────────────────┐
│          QUICK ACTIONS API                          │
│  Endpoint: /api/quick-actions/                      │
│  Method: POST                                       │
│                                                     │
│  Actions:                                           │
│  ├─ create_ticket: Quick ticket creation            │
│  └─ create_project: Quick project creation          │
│                                                     │
└─────────────────────────────────────────────────────┘
         │
         v
  ┌──────────────────────────────────────┐
  │ Get action type from POST data        │
  └──────────────────────────────────────┘
         │
         v
  ┌──────────────────────────────────────┐
  │ Route to appropriate handler:         │
│  ├─ create_ticket:                    │
│  │   - Extract title, description     │
│  │   - Create ticket with NEW status  │
│  │   - Return ticket_id               │
│  │                                    │
│  └─ create_project:                   │
│      - Extract name, description      │
│      - Create project with PLANNING   │
│      - Return project_id             │
  └──────────────────────────────────────┘
         │
         v
  ┌──────────────────────────────────────┐
  │ Return JSON Response:                │
│  {                                    │
│    "success": true/false,             │
│    "message": "Created successfully", │
│    "ticket_id/project_id": id         │
│  }                                    │
  └──────────────────────────────────────┘
```

---

## Role-Based Access Control Flow

```
┌─────────────────────────────────────────────────────┐
│          ROLE-BASED ACCESS CONTROL                  │
│                                                     │
│  User Roles (hierarchy):                            │
│  ├─ SUPERADMIN     → Full system access             │
│  ├─ IT_ADMIN       → Full admin access              │
│  ├─ MANAGER        → Manage projects, tickets       │
│  ├─ TECHNICIAN     → Handle tickets, assets         │
│  └─ VIEWER         → Read-only access               │
│                                                     │
│  Permission Properties:                             │
│  ├─ is_admin        → SUPERADMIN, IT_ADMIN          │
│  ├─ is_manager      → SUPERADMIN, IT_ADMIN, MANAGER │
│  ├─ is_technician   → All except VIEWER             │
│  ├─ can_manage_users → SUPERADMIN, IT_ADMIN         │
│  ├─ can_manage_assets → All except VIEWER           │
│  ├─ can_manage_projects → All except VIEWER         │
│  ├─ can_manage_tickets → All except VIEWER          │
│  └─ can_view_logs     → SUPERADMIN, IT_ADMIN        │
│                                                     │
└─────────────────────────────────────────────────────┘
         │
         v
  ┌──────────────────────────────────────┐
  │ Permission Check in Views:            │
│  ├─ LoginRequiredMixin (auth check)   │
│  ├─ Custom permission methods          │
│  └─ Redirect/403 for denied access     │
  └──────────────────────────────────────┘
```

---

## Dashboard API Flow

```
┌─────────────────────────────────────────────────────┐
│          DASHBOARD API                              │
│  Endpoint: /api/dashboard/                          │
│  Methods: GET, POST                                 │
│                                                     │
└─────────────────────────────────────────────────────┘
         │
         v
  ┌──────────────────────────────────────┐
  │ GET: Return dashboard data            │
│  {                                    │
│    "stats": {                         │
│      "users": count,                  │
│      "assets": count,                 │
│      "projects": count,               │
│      "tickets": count                 │
│    },                                 │
│    "recent_activity": [...],          │
│    "alerts": {                        │
│      "security_events": count,        │
│      "system_errors": count           │
│    }                                  │
│  }                                    │
  └──────────────────────────────────────┘
         │
    [POST: action=refresh_stats]
         │
         v
  ┌──────────────────────────────────────┐
  │ Return updated statistics             │
│  {                                    │
│    "success": true,                   │
│    "stats": {                         │
│      "users": count,                  │
│      "assets": count,                 │
│      "projects": count,               │
│      "tickets": count                 │
│    }                                  │
│  }                                    │
  └──────────────────────────────────────┘
```

---

## URL Mapping

```
Old (Admin) → New (Web Forms)

Authentication:
  /admin/login/      → /login/
  /admin/logout/     → /logout/

Dashboard:
  showCreateTicketModal()  → /tickets/create/
  showCreateProjectModal() → /projects/create/
  showCreateAssetModal()   → /assets/create/

Tickets List:
  /admin/tickets/ticket/add/  → /tickets/create/
  /admin/tickets/ticket/.../  → /tickets/
  /admin/tickets/ticket/X/    → /tickets/X/edit/

Projects List:
  /admin/projects/project/add/ → /projects/create/
  /admin/projects/project/.../  → /projects/
  /admin/projects/project/X/    → /projects/X/edit/

Assets List:
  /admin/assets/asset/add/ → /assets/create/
  /admin/assets/asset/.../  → /assets/
  /admin/assets/asset/X/    → /assets/X/edit/

Users List (NEW):
  /admin/auth/user/         → /users/
  /admin/auth/user/add/     → /users/create/
  /admin/auth/user/X/change → /users/X/edit/

Logs & Reports:
  → /logs/
  → /reports/

Profile:
  → /profile/

API Endpoints:
  /admin/              → /api/dashboard/
  (search)             → /api/search/
  (quick actions)      → /api/quick-actions/
```

---

## View Architecture

```
┌─────────────────────────────────────────────────────┐
│           LoginRequiredMixin (Security)              │
│  ┌────────────────────────────────────────────────┐ │
│  │           TemplateView (Base)                  │ │
│  │  ┌─────────────────────────────────────────┐  │ │
│  │  │  DashboardView                          │  │ │
│  │  │  - Statistics context                   │  │ │
│  │  │  - Recent activity                      │  │ │
│  │  └─────────────────────────────────────────┘  │ │
│  │                                                │ │
│  │  ┌─────────────────────────────────────────┐  │ │
│  │  │  AssetsView / CreateAssetView           │  │ │
│  │  │  - Asset listing                        │  │ │
│  │  │  - Create/Edit with validation          │  │ │
│  │  └─────────────────────────────────────────┘  │ │
│  │                                                │ │
│  │  ┌─────────────────────────────────────────┐  │ │
│  │  │  ProjectsView / CreateProjectView       │  │ │
│  │  │  - Project listing                      │  │ │
│  │  │  - Create/Edit with validation          │  │ │
│  │  └─────────────────────────────────────────┘  │ │
│  │                                                │ │
│  │  ┌─────────────────────────────────────────┐  │ │
│  │  │  TicketsView / CreateTicketView         │  │ │
│  │  │  - Ticket listing                       │  │ │
│  │  │  - Create/Edit with validation          │  │ │
│  │  └─────────────────────────────────────────┘  │ │
│  │                                                │ │
│  │  ┌─────────────────────────────────────────┐  │ │
│  │  │  UsersView / CreateUserView             │  │ │
│  │  │  - User listing (admin only)            │  │ │
│  │  │  - Create/Edit with validation          │  │ │
│  │  └─────────────────────────────────────────┘  │ │
│  │                                                │ │
│  │  ┌─────────────────────────────────────────┐  │ │
│  │  │  ProfileView / LogsView / ReportsView   │  │ │
│  │  │  - Read-only views                      │  │ │
│  │  └─────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## Template Inheritance Chain

```
dashboard.html
        │
        v
  base.html (extends)
        │
        v
  ┌─────────────────────┐
  │ HTML Structure      │
  │ - Head (CSS/JS)     │
  │ - Sidebar (Nav)     │
  │ - Content (Forms)   │
  │ - Footer            │
  └─────────────────────┘

create-ticket.html
        │
        v
  base.html (extends)
        │
        v
  ┌─────────────────────┐
  │ Ticket Form         │
  │ - Form fields       │
  │ - Validation msgs   │
  │ - Submit buttons    │
  └─────────────────────┘
```

---

## Security Chain

```
User Request
     │
     v
URL Router (urls.py)
     │
     v
View Class (with LoginRequiredMixin)
     │
     ├─ Is user authenticated?
     │  └─ No? Redirect to /login/
     │
     ├─ Yes! Continue
     │
     ├─ Has required permissions? (can_manage_users, etc.)
     │  └─ No? 403 Forbidden / Redirect
     │
     v
Template (with {% csrf_token %})
     │
     ├─ Render form with CSRF token
     │
     v
User Submits
     │
     v
CSRF Token Verification
     │
     ├─ Valid? Continue
     │  └─ Invalid? Reject (403)
     │
     v
Form Validation
     │
     ├─ Valid? Process request
     │  └─ Invalid? Show errors
     │
     v
Database Operation
     │
     ├─ Create/Update/Delete
     │  └─ Set created_by/updated_by
     │
     v
Success Response
     │
     ├─ Success message
     └─ Redirect to list page
```

---

## Notifications API Flow

```
┌─────────────────────────────────────────────────────┐
│          NOTIFICATIONS API                          │
│  Endpoint: /api/notifications/                      │
│  Method: GET                                        │
│                                                     │
└─────────────────────────────────────────────────────┘
         │
         v
  ┌──────────────────────────────────────┐
  │ Get authenticated user                │
  └──────────────────────────────────────┘
         │
         v
  ┌──────────────────────────────────────┐
  │ Fetch user notifications              │
│  - Activity logs                      │
│  - Security events                    │
│  - Ticket updates                     │
  └──────────────────────────────────────┘
         │
         v
  ┌──────────────────────────────────────┐
  │ Return JSON Response:                │
│  {                                    │
│    "notifications": [...],            │
│    "unread_count": n                  │
│  }                                    │
  └──────────────────────────────────────┘
```

---

## Data Flow (Full Cycle)

```
┌─────────────────────────────────────────────────────┐
│          USER SUBMITS FORM                          │
└─────────────────────────────────────────────────────┘
              │
              v
┌─────────────────────────────────────────────────────┐
│     VIEW CLASS                                       │
│     - GET: Display form with context                │
│     - POST: Process submission                      │
│     - Extract form data                             │
│     - Validate all fields                           │
└─────────────────────────────────────────────────────┘
              │
              ├─ Validation Failed?
              │         │
              │         v
              │  Return form with errors
              │
              └─ Validation OK?
                      │
                      v
        ┌─────────────────────────────┐
        │ DATABASE OPERATIONS         │
        │ - Create Model Instance     │
        │ - Save to Database          │
        │ - Set created_by = user     │
        │ - Auto-assign status        │
        │ - Generate employee_id      │
        └─────────────────────────────┘
                      │
                      v
        ┌─────────────────────────────┐
        │ SIGNAL HANDLERS             │
        │ - Create activity log       │
        │ - Create security event     │
        │ - Update related records    │
        └─────────────────────────────┘
                      │
                      v
        ┌─────────────────────────────┐
        │ USER FEEDBACK               │
        │ - Success message           │
        │ - Redirect to list page     │
        │ - Show new item in list     │
        └─────────────────────────────┘
```

---

This implementation ensures that all operations flow through secure, validated web forms with proper role-based access control, logging, and user feedback.

