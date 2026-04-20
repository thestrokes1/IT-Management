# CLAUDE.md — IT Management Platform

> Single source of truth for project context, architecture rules, and improvement plan.
> Update this file whenever a task below is completed or context changes.

---

## IMPROVEMENT PLAN

Track progress here. Check items off as they are completed.

### Phase 0 — Documentation Consolidation ✅
- [x] Create this CLAUDE.md as single source of truth
- [x] Merge ARCHITECTURE.md content into CLAUDE.md
- [x] Merge docs/permissions.md content into CLAUDE.md
- [x] Delete ARCHITECTURE.md
- [x] Delete docs/index.md
- [x] Delete docs/permissions.md
- [x] Delete PROFILE_VIEW_DOCUMENTATION.md (25 KB, stale)
- [x] Delete VISUAL_FLOW_DIAGRAMS.md (49 KB, stale)

### Phase 1 — Quick Wins ✅
- [x] Delete `apps/logs/services/involved_usernames_fix.py` (662 LOC, dead code — zero imports)
- [x] Add `pytest.ini` to establish test infrastructure baseline
- [x] Move `pythonanywhere_wsgi.py` to `docs/deployment/`

### Phase 2 — Safety Net ✅
- [x] Create `backend/conftest.py` — shared role fixtures (viewer, technician, manager, it_admin, superadmin)
- [x] Create `apps/tickets/tests/test_authority.py` + `test_commands.py` — 55 tests
- [x] Create `apps/assets/tests/test_authority.py` + `test_commands.py` — 49 tests
- [x] Create `apps/projects/tests/test_authority.py` + `test_commands.py` — 56 tests
- [x] Update `.github/workflows/backend.yml` to run actual test suite (was pointing at nonexistent path)
- [ ] Create `apps/frontend/tests/test_permissions/` — HTTP-level permission tests (optional, lower priority)

**Bugs fixed during Phase 2 (found by tests):**
- `ticket_authority.py`: 4 legacy aliases (`assert_can_delete`, `assert_can_assign`, `assert_can_close`, `assert_can_resolve`) were calling themselves recursively — infinite recursion on any delete/assign/close/resolve assertion
- `asset_authority.py`: `assert_can_create_asset` was missing — `create_asset.py` imported it but it didn't exist
- `assets/domain/events.py` → `emit_asset_updated`: type mismatch — `get_changed_fields` returns `List[Dict]` but `AssetUpdated` expected `Dict[str, tuple]`. Every asset update was silently broken at the event layer.

### Phase 3 — Log Service Decomposition ✅ (dead code eliminated)
- [x] Deleted `apps/logs/examples.py` (247 LOC, pure docs, never imported)
- [x] Deleted empty `apps/projects/application/createProject.py` (camelCase duplicate)
- [x] Deleted `event_adapter.py` (442 LOC) — zero external consumers after `examples.py` removal
- [x] Deleted `security_event_logger.py` (931 LOC) — zero external consumers
- [x] Deleted `log_creator.py` (674 LOC) — zero external consumers
- [x] Deleted `structured_payloads.py` (802 LOC) — zero external consumers
- [x] Deleted `security_service.py` (645 LOC, SecurityDashboardService) — only exported from `__init__.py`, never actually called
- [x] Cleaned up `__init__.py` — removed all deleted file exports
- **Result: 13 files / ~8,500 LOC → 8 files / ~4,386 LOC (48% reduction)**
- [x] `activity_service.py`: removed 21 unused methods + dead imports — 1,124 LOC → **489 LOC (56% reduction)**
- [x] `logs/services/diff_utils.py` (320 LOC) — deleted after activity_service no longer imports it
- [x] `logs/dto.py` (696 LOC) — zero external consumers
- [x] `logs/application/` (use_cases.py, ~500 LOC) — zero external consumers
- [x] `logs/infrastructure/` (repository.py, ~315 LOC) — zero external consumers
- [x] `frontend/permissions.py` (425 LOC) — zero external imports anywhere in codebase
- [x] `core/idempotent.py` (473 LOC) — zero consumers
- [x] `tickets/queries/` (ticket_query.py, 159 LOC) — zero consumers
- **Final logs/services/: 7 files / 3,431 LOC (was 13 files / 8,500 LOC — 60% total reduction)**

### Phase 4 — Authority Consolidation ✅
- [x] Fixed `user_authority.py`: `assert_can_change_role` alias called itself recursively — removed duplicate
- [x] Removed `TicketAuthority` wrapper class (90 LOC pure delegation boilerplate) from `ticket_authority.py`
- [x] Updated `tickets/web_views.py` to import authority functions directly instead of via class
- [x] Fixed `asset_crud` DELETE: was checking `role in ['ADMIN', 'SUPERADMIN', 'IT_ADMIN']` (wrong — 'ADMIN' is not a valid role, missed MANAGER and TECHNICIAN-own-asset case) → now uses `can_delete(user, asset)`
- [x] Fixed `asset_crud` PATCH: same pattern → now uses `can_edit(user, asset)`
- [x] Fixed `asset_unassign` view: bad inline role check → now uses `can_unassign(user, asset)`
- [x] Replaced 3 inline `role in ['SUPERADMIN','MANAGER','IT_ADMIN']` dropdown checks with `is_admin_role(user.role)` from `core.domain.roles`
- [x] Replaced all 15 inline role checks in `dashboard.py` with `is_admin_role()`, `is_superadmin_or_manager()`, and `user_role != 'VIEWER'`
- [x] Eliminated all remaining inline role string checks: `profile.py`, `tickets.py`, `users.py` (frontend), `web_views.py`, `activity_service.py`, `activity_adapter.py`, `create_project.py`, `ticket_query_service.py`, `project_authority.py` — **Zero `role in [...]` checks remain anywhere in the codebase outside models.py**
- [x] Removed `_ROLE_*` constant blocks from all 4 authority files — replaced with inline string literals (`'VIEWER'`, `'TECHNICIAN'`, etc.) which are self-documenting and remove one layer of indirection

### Phase 5 — View Decomposition
- [x] Created `apps/tickets/web_mixins.py` — `TicketDetailLoggingMixin` with 6 logging methods + `_get_client_ip` extracted from `TicketDetailView`
- [x] `tickets/web_views.py`: 1,126 LOC → 824 LOC (27% reduction). Logging concern separated from view/action logic.
- [x] Fixed `_can_change_priority` inline role check → `is_admin_role(user.role)`
- [ ] Note: `tickets/web_views.py` has ONE class (`TicketDetailView`) handling detail + 5 POST actions (assign/status/priority/note/review) via one URL — further split would require template and URL changes
- [ ] `assets` and `projects` apps have no separate `web_views.py` — all views are in `frontend/views/`

### Phase 6 — Permission Consolidation ✅
- [x] Created `apps/core/permissions.py` — 3 base classes: `ListPermission`, `ObjectPermission`, `ViewPermission` (57 LOC)
- [x] Rewrote `tickets/permissions.py`: 518 LOC → 76 LOC (85% reduction) — deleted 22 unused classes, 13 live classes now 2-4 lines each
- [x] Rewrote `assets/permissions.py`: 371 LOC → 59 LOC (84% reduction) — deleted 11 unused classes, 10 live classes simplified
- [x] Rewrote `users/permissions.py`: 323 LOC → 66 LOC (80% reduction) — deleted 12+ unused classes, 8 live classes simplified
- [x] Left `projects/permissions.py` unchanged — all 16 classes are used and use Django model properties (different abstraction layer), no dead code to remove
- **Total LOC removed: ~1,154 lines across 3 permission files**

### Phase 8 — UI/UX Polish & Deployment Fixes (Next up)

#### 🔴 Functional — app is not fully demoable without these

- [ ] **Seed demo users** — `itadmin`, `manager`, `tech`, `viewer` shown on login page but don't exist on Render DB. Write a management command `seed_demo_users` that creates them with `admin123` password, idempotent (safe to re-run). Add to build command in `render.yaml` after `init_superuser`.
- [ ] **Seed categories** — Creating a ticket/asset/project requires categories to exist. Fresh deployment has zero so create forms fail silently. Write `seed_categories` management command (or combine with above into `seed_data`) that creates: TicketCategory (Hardware Issue, Software, Network/Connectivity, General Inquiry, Email/Communication), AssetCategory (Laptop, Desktop, Monitor, Printer, Phone, Server), ProjectCategory (Infrastructure, Security, Development, Maintenance).
- [ ] **Console errors on every page** — 4–7 JS errors logged per page load (visible in dev toolbar). Identify and fix — likely missing API endpoints or undefined JS references.

#### 🟡 Code hygiene

- [ ] **Add `.playwright-mcp/` to `.gitignore`** — Playwright screenshots/snapshots are untracked and will get accidentally staged. Add `/.playwright-mcp/` to `.gitignore`.
- [ ] **Add `favicon.ico`** — Every page request logs `GET /favicon.ico 404`. Add a simple favicon to `static/` and reference it in `base.html`.
- [ ] **Delete old Render service** — `IT-Management` (srv-d65ps575r7bs73bk8ho0, deployed Feb 2026) is still running at `it-management-e72k.onrender.com` and consuming free-tier resources alongside the new service. Delete it from Render dashboard.
- [ ] **Update `PROJECT SUMMARY` status** — CLAUDE.md still says `Status: Not deployed` — now deployed at `https://it-management-backend-afpb.onrender.com`.

#### 🟢 UI — verify and polish

- [ ] **Light mode spot-check** — All recent fixes were tested in dark mode only. Open the app in light mode and verify: button text, breadcrumbs, hover states, empty states all look correct.
- [ ] **Mobile layout** — Test sidebar collapse/hamburger on a narrow viewport after the navbar removal. The `lg:hidden` hamburger button at the top of main content needs to actually open the sidebar smoothly.
- [ ] **Projects "Create" button missing for SUPERADMIN on local DB** — Verify this works on Render where the admin user has SUPERADMIN role. If it fails there too, debug `permissions.can_create` for projects.
- [ ] **Ticket detail page** — Not checked in UI review. Verify dark mode styling, breadcrumb (should be `Dashboard > Tickets > #ID`), and action buttons (assign, close, resolve) are visible and functional.
- [ ] **Create/Edit forms** — Check all create forms (ticket, asset, project, user) in dark mode. Form fields, labels, and submit buttons may have the same white-on-white issue we fixed for list pages.

### Phase 7 — Deploy (Code ready — user action needed)
**Pre-deploy fixes applied:**
- `render.py`: `conn_max_links=500` → `conn_max_age=60` (invalid param → TypeError on startup)
- `render.yaml`: Added `rootDir: backend`, removed manual `.venv`, added `migrate` + `collectstatic`
- `render.yaml`: **Moved to repo root** — Render Blueprint reads from repo root, not `backend/`
- `.gitignore`: Removed erroneous `apps/` entry that silently blocked new files from git
- `db.sqlite3`: Removed from git tracking (`git rm --cached`)
- Deleted 0-byte ghost file `backend/apps/frontend/views/tickets` (existed since Feb 19)
- `urls.py`: Fixed indentation + added `debug_toolbar` conditional guard

**Steps to deploy:**
- [x] Commit all changes (74 files, 3,838 insertions, 9,941 deletions)
- [x] Push to `https://github.com/thestrokes1/IT-Management.git` (commit `45deb02`)
- [ ] Go to render.com → New → **Blueprint** → connect `thestrokes1/IT-Management`
- [ ] Render reads root-level `render.yaml` and auto-provisions PostgreSQL + Redis
- [ ] `DJANGO_SECRET_KEY` auto-generated — no manual env vars needed
- [ ] Build runs: `pip install` → `migrate` → `collectstatic` (all automatic)
- [ ] App at `https://it-management-backend.onrender.com`

**Note:** Free plan spins down after 15 min inactivity (~30s cold start). Starter ($7/mo) = always-on.

---

## PROJECT SUMMARY

**What it is:** Django web application for IT department operations.

**Domains managed:**
| Domain | Purpose |
|--------|---------|
| Tickets | IT support lifecycle: NEW → OPEN → IN_PROGRESS → RESOLVED → CLOSED, SLA tracking |
| Assets | Hardware/software inventory, assignment, lifecycle (purchase → warranty → disposal) |
| Projects | IT project management, team members, budget, task tracking |
| Users | Role-based access, user lifecycle, security lockout fields |
| Logs | Full audit trail: ActivityLog (differential changes) + SecurityEvent |
| Security | Rate limiting, auth event tracking, SecurityAudit model |

**Status:** Deployed at `https://it-management-backend-afpb.onrender.com` (Render free tier, spins down after 15 min inactivity). Login: `admin` / `Deploy2026!IT`.

---

## TECH STACK

| Layer | Technology |
|-------|-----------|
| Framework | Django 4.2.11 + Python 3.13 |
| API | Django REST Framework 3.14.0 + JWT (simplejwt 5.3.0) |
| Frontend | Server-side Django templates + Tailwind CSS 3.4 (no JS framework) |
| Database | SQLite (dev) → PostgreSQL (prod via psycopg2-binary) |
| Cache | Redis (django-redis 5.4.0) |
| Task queue | Celery (configured but minimal use) |
| Static files | WhiteNoise 6.6.0 |
| Auth | django-allauth 0.57.0 + custom RBAC |
| API docs | drf-spectacular 0.26.5 (Swagger) |
| Testing | pytest 7.4.0 + pytest-django 4.7.0 |
| Forms | django-crispy-forms + crispy-tailwind |

**Full dependency list** (`backend/requirements.txt`):
```
Django==4.2.11, djangorestframework==3.14.0, djangorestframework-simplejwt==5.3.0,
django-cors-headers==4.3.1, django-environ==0.11.2, dj-database-url==2.1.0,
psycopg2-binary==2.9.9, django-allauth==0.57.0, django-extensions==3.2.3,
drf-spectacular==0.26.5, drf-spectacular-sidecar==2023.12.1, whitenoise==6.6.0,
django-redis==5.4.0, redis==5.0.1, django-filter==23.5, gunicorn==21.2.0,
python-decouple==3.8, pytest==7.4.0, pytest-django==4.7.0
```

---

## CODEBASE SIZE

| Metric | Value |
|--------|-------|
| Total Python files | 223 |
| Total lines of code | ~56,000 (not 30K as initially estimated) |
| HTML templates | 23 |
| Django apps | 8 |
| CQRS command files | ~25 |

**Where the lines go:**

| Layer | LOC | Assessment |
|-------|-----|------------|
| `logs/services/` (13 files) | ~8,500 | Primary bloat — needs decomposition |
| Domain authority services | ~5,000 | Duplicated patterns — refactor target |
| Web views (`frontend/views/` + domain `web_views.py`) | ~4,500 | Some god files — refactor target |
| API views (DRF, per domain) | ~4,300 | Acceptable |
| CQRS command handlers (`application/`) | ~4,400 | Intentional — keep |
| Permissions (per domain, 5 files) | ~2,600 | Duplicated — refactor target |
| Signals (6 files) | ~1,800 | Complex chains |
| Models (6 files) | ~3,200 | Well-sized |
| Settings (4 files) | ~900 | Slightly over-split |

**Realistic target after Phase 3–6:** ~38,000–40,000 LOC (28–30% reduction)

---

## ARCHITECTURE RULES (CQRS)

These rules must be followed for all new code.

### Write Model — WHERE mutations are allowed

```
ALLOWED:   apps/{domain}/application/*.py   ← CQRS commands only
FORBIDDEN: views/, services.py, serializers.py, queries/, signals.py
```

Mutation methods: `.save()`, `.delete()`, `.create()`, `.update()`, `.get_or_create()`, `.update_or_create()`

### Correct Pattern

```python
# In a CQRS command (apps/{domain}/application/update_ticket.py):
from apps.tickets.domain.services.ticket_authority import assert_can_update_ticket

def execute(self, user, ticket_id, data):
    ticket = Ticket.objects.get(id=ticket_id)
    assert_can_update_ticket(user, ticket)   # authorization first
    ticket.status = data['status']
    ticket.save()                             # mutation only after auth passes
    transaction.on_commit(lambda: emit_activity_event(user, ticket))  # log after commit
```

### Forbidden Anti-Patterns

```python
# WRONG — view mutating a model
def update_ticket(request, ticket_id):
    ticket = Ticket.objects.get(id=ticket_id)
    ticket.status = request.POST['status']
    ticket.save()  # FORBIDDEN in views

# WRONG — serializer mutating a model
class TicketSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance.save()  # FORBIDDEN in serializers

# WRONG — signal mutating a model
@receiver(post_save, sender=Project)
def project_saved(sender, instance, **kwargs):
    instance.status = 'MODIFIED'
    instance.save()  # FORBIDDEN in signals
```

### Activity Logging Rule

Logging MUST use `transaction.on_commit()` so it only fires after a successful DB commit:

```python
transaction.on_commit(lambda: emit_activity_event(user, entity))
```

Wrap in try/except — logging failure must never break the main operation.

### Layer Mutation Reference

| Layer | Can Mutate? |
|-------|-------------|
| `application/` (CQRS commands) | YES |
| `domain/services/` (authority) | YES |
| `views/`, `web_views.py` | NO |
| `services.py` | NO |
| `serializers.py` | NO |
| `queries/` | NO |
| `signals.py` | NO |
| `models.py` | NO |

### Adding a New CQRS Command

1. Create command in `apps/{domain}/application/`
2. Add `assert_*` function in `apps/{domain}/domain/services/{domain}_authority.py`
3. Emit domain event via `apps/{domain}/domain/events.py`
4. Wire view to call the command (no direct mutations in view)
5. Write test for the command

---

## ROLE HIERARCHY & PERMISSIONS

### Roles

**`core/domain/roles.py` ROLE_RANKS (used by all authority services):**
```
SUPERADMIN (4) = MANAGER (4) > IT_ADMIN (3) > TECHNICIAN (2) > VIEWER (1)
```

**Important:** MANAGER and SUPERADMIN have equal rank 4. IT_ADMIN rank is 3, meaning MANAGER outranks IT_ADMIN.
This differs from `users/models.py` ROLE_LEVEL (which has IT_ADMIN=4, MANAGER=3) — that dict is not used for authorization checks and is inconsistent with roles.py. Trust roles.py for permission logic.

**Technician ownership rule:** Technicians own items via `assigned_to`, NOT `created_by`. They can edit/delete only items assigned to them. They can self-assign to unassigned items but cannot assign items to others.

### Permission Matrix

#### Tickets

| Role | Create | Update | Delete | Assign |
|------|--------|--------|--------|--------|
| VIEWER | ❌ | ❌ | ❌ | ❌ |
| TECHNICIAN | ✅ | Own only | Own only | Own → self only |
| MANAGER | ✅ | ✅ | ✅ | ✅ |
| IT_ADMIN | ✅ | Lower roles | Lower roles | ✅ |
| SUPERADMIN | ✅ | ✅ | ✅ | ✅ |

Authority: `ticket_authority.py` — `can_create_ticket()`, `assert_can_update_ticket()`, `assert_can_delete_ticket()`, `assert_can_assign_ticket()`

#### Assets

| Role | Create | Update | Delete | Assign |
|------|--------|--------|--------|--------|
| VIEWER | ❌ | ❌ | ❌ | ❌ |
| TECHNICIAN | ✅ | ✅ | ❌ | ❌ |
| MANAGER | ✅ | ✅ | ✅ | ❌ |
| IT_ADMIN | ✅ | ✅ | ✅ | ✅ |
| SUPERADMIN | ✅ | ✅ | ✅ | ✅ |

Authority: `asset_authority.py` — `can_create_asset()`, `assert_can_update_asset()`, `assert_can_delete_asset()`, `can_assign_asset()`

**Known legacy gap:** `asset_crud` DELETE/PATCH use role string checks instead of `assert_*` functions. Fix tracked in Phase 4.

#### Projects

| Role | Create | Update | Delete | Manage Members |
|------|--------|--------|--------|----------------|
| VIEWER | ❌ | ❌ | ❌ | ❌ |
| TECHNICIAN | ❌ | ❌ | ❌ | ❌ |
| MANAGER | ✅ | ✅ | ❌ | ✅ |
| IT_ADMIN | ❌ | ❌ | ❌ | ❌ |
| SUPERADMIN | ✅ | ✅ | ✅ | ✅ |

Authority: `project_authority.py` + `ProjectPolicy` class — `can_create_project()`, `assert_can_update_project()`, `assert_can_delete_project()`

Note: IT_ADMIN is excluded from project management by design.

#### Users

| Role | Create | Update | Change Role | Delete |
|------|--------|--------|-------------|--------|
| VIEWER | ✅ (self-register) | Own only | ❌ | ❌ |
| TECHNICIAN | ✅ | Own only | ❌ | ❌ |
| MANAGER | ✅ | Lower roles | ❌ | ❌ |
| IT_ADMIN | ✅ | Lower roles | ❌ | ❌ |
| SUPERADMIN | ✅ | All | ✅ | ✅ |

Authority: `user_authority.py` — `can_update_user()`, `can_change_role()`, `assert_can_delete_user()`

### Mixins Reference

| Mixin | Protects | Minimum Role |
|-------|----------|-------------|
| `CanManageUsersMixin` | CreateUserView | IT_ADMIN |
| `CanManageTicketsMixin` | EditTicketView | VIEWER+ |
| `CanManageProjectsMixin` | CreateProjectView | MANAGER |
| `CanManageAssetsMixin` | CreateAssetView, EditAssetView | MANAGER |

### UI vs Backend Permissions — Important Distinction

- `get_*_permissions()` functions are **UI-only** — they show/hide buttons, they do NOT enforce security
- Real enforcement is via `assert_*` functions and Mixins
- A direct API call bypassing the UI will still be rejected if authorization fails

---

## STRENGTHS

1. **Architecture-enforced CQRS** — Clean write/read separation, no mutations outside commands
2. **Comprehensive RBAC** — 5-level hierarchy, per-domain authority, well-documented
3. **Audit-grade logging** — ActivityLog with differential change tracking, SecurityEvent, security fields on User (`failed_login_attempts`, `locked_until`, `last_login_ip`)
4. **Clean domain separation** — Each app is self-contained (models, views, permissions, commands, signals)
5. **Production-ready config** — Gunicorn, WhiteNoise, render.yaml, split dev/prod settings, .env support
6. **No frontend dependency hell** — Pure Django templates + Tailwind, no JS framework to maintain
7. **Domain events infrastructure** — Core event system in place for extensibility
8. **Good base documentation** — Architecture rules, permission matrix, deployment configs already exist

---

## WEAKNESSES

| Weakness | Severity | Detail |
|----------|----------|--------|
| No test coverage | Critical | pytest installed but almost no tests. Any refactor is blind. |
| Log service monolith | High | 13 files ~8,500 LOC in `logs/services/`. `involved_usernames_fix.py` was dead code. |
| God-file web views | High | `tickets/web_views.py` at 1,124 LOC handles all ticket UI in one file |
| Authority code duplication | Medium | `ticket_authority.py` (971) and `asset_authority.py` (712) reimplement same role-check patterns |
| Permission class duplication | Medium | 2,600 LOC across 5 `permissions.py` files doing similar DRF checks |
| No CI/CD pipeline | Medium | No GitHub Actions workflows |
| Legacy asset_crud endpoints | Low | Uses role strings not `assert_*` — inconsistent with rest of codebase |
| Celery barely used | Low | Configured but only minimal usage — adds dependency weight |
| SQLite/PostgreSQL divergence | Low | Dev on SQLite can hide migration issues |

---

## WHAT TO IMPROVE

### High Priority (do before touching anything)

**1. Add test suite** — Without tests, all refactoring is guesswork. Target: CQRS commands, permission matrix, logging behavior.

**2. Log service decomposition** — `logs/services/` is 13 files with complex inter-dependencies. `activity_service.py` at 1,123 LOC is a state machine that needs splitting. Dead code (`involved_usernames_fix.py`) already deleted.

**3. Split god-file views** — `tickets/web_views.py` at 1,124 LOC. Split into class-based views per action.

### Medium Priority

**4. Authority base class** — `core/domain/authority_base.py` exists but is underused. Common role-check methods should live there; domain authorities should extend it.

**5. Permission consolidation** — Move shared DRF permission logic to `core/permissions.py`, subclass per domain.

**6. Fix legacy asset_crud** — Two endpoints still use role string checks. Migrate to `assert_*` pattern.

### Low Priority

**7. Settings cleanup** — `prod.py` targets PythonAnywhere, `render.py` targets Render. Both are valid — keep both but document which to use.

**8. Remove or commit to Celery** — Either add meaningful async tasks (SLA breach notifications, email alerts) or remove Celery from requirements.

---

## DEPLOYMENT OPTIONS (Free, No Credit Card)

### Option 1: Render — RECOMMENDED (already configured)
- `render.yaml` is already in the repo
- Free tier: web service + PostgreSQL (90-day free DB)
- No credit card required for free tier
- Spins down after 15 min inactivity (free plan)
- **Steps:**
  1. Push repo to GitHub
  2. Go to render.com → New → Blueprint (reads `render.yaml` automatically)
  3. Set env vars: `DJANGO_SECRET_KEY`, `DJANGO_SETTINGS_MODULE=config.settings.render`
  4. Deploy

### Option 2: Railway — Best long-term free option
- $5/month free credit, no credit card required
- Managed PostgreSQL included
- No sleep on inactivity
- **Steps:**
  1. Go to railway.app → New Project → Deploy from GitHub
  2. Add PostgreSQL plugin
  3. Set `DJANGO_SETTINGS_MODULE=config.settings.render` (render.py works for Railway too) or create `config/settings/railway.py`
  4. Set `DJANGO_SECRET_KEY`, `DATABASE_URL`

### Option 3: PythonAnywhere — Always-on free
- `pythonanywhere_wsgi.py` already in repo root
- No sleep — always on (best for demos)
- No credit card required
- **Limitation:** Free tier is MySQL only, not PostgreSQL. `prod.py` uses PostgreSQL config — needs adjustment for MySQL on free tier.
- **Steps:**
  1. Upload code via git clone in PythonAnywhere console
  2. Configure WSGI file to point to `pythonanywhere_wsgi.py`
  3. Set env vars in PythonAnywhere dashboard

### Option 4: Fly.io — NOT suitable
- Requires credit card even for free tier

### Decision guide:
- Want quickest deploy → **Render** (render.yaml ready)
- Want no sleep/stable demo → **PythonAnywhere** (but switch DB to MySQL or use a free external PostgreSQL)
- Want best long-term free tier → **Railway**

---

## FILE REFERENCE MAP

```
backend/
├── config/
│   ├── settings/
│   │   ├── base.py          # Core settings — edit for new installed apps, auth
│   │   ├── dev.py           # Dev overrides — SQLite, debug toolbar
│   │   ├── prod.py          # PythonAnywhere target — MySQL/PostgreSQL
│   │   └── render.py        # Render.com target — PostgreSQL + Redis + WhiteNoise
│   ├── urls.py              # Root URL routing
│   └── celery.py            # Celery (minimal use)
├── apps/
│   ├── core/
│   │   ├── domain/
│   │   │   ├── authority_base.py  # ← Underused. Expand here for Phase 4.
│   │   │   ├── roles.py           # Role constants + ROLE_LEVEL map
│   │   │   └── authorization.py   # Base authorization
│   │   ├── events.py              # Domain event infrastructure
│   │   └── exception_mapper.py    # Exception → HTTP status mapping
│   ├── users/
│   │   ├── models.py              # Custom User, 5-role RBAC, security lockout fields
│   │   ├── domain/services/user_authority.py
│   │   └── application/           # CQRS: ChangeUserRole
│   ├── tickets/
│   │   ├── models.py              # Ticket, TicketCategory, TicketType
│   │   ├── web_views.py           # ← 1,124 LOC god file. Split in Phase 5.
│   │   ├── domain/services/ticket_authority.py  # ← 971 LOC. Refactor in Phase 4.
│   │   └── application/           # CQRS: Create, Update, Assign, Close, Delete
│   ├── assets/
│   │   ├── models.py              # Asset, AssetCategory
│   │   ├── domain/services/asset_authority.py   # ← 712 LOC. Refactor in Phase 4.
│   │   └── application/           # CQRS: Create, Update, Assign, Delete
│   ├── projects/
│   │   ├── models.py              # Project, ProjectCategory, TaskCategory
│   │   ├── signals.py             # ← 461 LOC. Complex event chains.
│   │   └── application/           # CQRS: Create, Update, Delete, ChangeStatus, ManageMembers
│   ├── logs/
│   │   ├── models.py              # ActivityLog, SecurityEvent
│   │   └── services/              # ← 13 files ~8,500 LOC. Primary Phase 3 target.
│   │       ├── activity_service.py       # 1,123 LOC — split this first
│   │       ├── security_event_logger.py  # 931 LOC
│   │       ├── activity_adapter.py       # 845 LOC — likely overlaps with log_adapter
│   │       └── ...
│   ├── security/
│   │   ├── models.py              # SecurityAudit, RateLimit
│   │   └── middleware/            # Rate limiting, auth event tracking
│   └── frontend/
│       ├── views/                 # UI views per domain (8 files)
│       ├── services.py            # 804 LOC aggregation service
│       └── forms.py               # Django forms
├── templates/frontend/            # 23 HTML templates
│   ├── base.html                  # Master layout with Tailwind dark theme
│   ├── partials/                  # Reusable components
│   └── {entity}_*.html            # CRUD per domain
├── static/
│   ├── css/                       # Compiled Tailwind
│   └── js/
├── requirements.txt
├── render.yaml                    # Render.com deploy config
└── tailwind.config.js

pythonanywhere_wsgi.py             # PythonAnywhere WSGI entry point (root level)
```

---

## SCORECARD

| Area | Start | Now | Notes |
|------|-------|-----|-------|
| Architecture | 8/10 | 8/10 | Strong CQRS, clean domain model — unchanged |
| Code quality | 6/10 | 8/10 | Dead code removed, role checks consistent, no magic strings |
| Test coverage | 2/10 | 6/10 | 160 tests across all domain authority + CQRS commands |
| Documentation | 7/10 | 9/10 | CLAUDE.md is the single source of truth |
| Deployment readiness | 7/10 | 9/10 | render.yaml fixed, conn_max_age fixed, migrations automated |
| Security | 7/10 | 8/10 | All role checks via domain authority, no legacy string comparisons |
| Maintainability | 6/10 | 8/10 | Consistent patterns, no duplication, clear file structure |
| **Overall** | **6.5/10** | **8.5/10** | Ready to deploy and extend |

**Key metrics (start → now):**
- Estimated LOC: ~56,000 → ~43,000 (~23% reduction from dead code purge alone)
- Bugs fixed: 8 real bugs (4 infinite recursion, 1 missing function, 1 type mismatch, 1 invalid DB param, 1 wrong rootDir)
- Inline `role in [...]` checks: 40+ → **0** everywhere
- `logs/services/`: 13 files / 8,500 LOC → **7 files / 3,431 LOC (60% reduction)**
- `activity_service.py`: 1,124 → 489 LOC (56% reduction)
- Permission files: 1,929 LOC → 775 LOC (60% reduction)  
- Dead files deleted: logs/dto.py (696), logs/application/ (~500), logs/infrastructure/ (~315), frontend/permissions.py (425), core/idempotent.py (473), tickets/queries/ (159), + 5 log services (~3,494 total)
- Tests: 0 → **160 passing**
- Zero `role in [...]` magic strings anywhere
