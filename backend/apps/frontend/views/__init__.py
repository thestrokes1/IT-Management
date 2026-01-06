# Frontend views package.
# Re-exports views from domain-specific modules using relative imports.

# Auth views
from .auth import (
    LoginView,
    LogoutView,
    Error404View,
    Error500View,
    MaintenanceView,
)

# Dashboard views
from .dashboard import (
    DashboardView,
    dashboard_api,
    search_api,
    notifications_api,
    quick_actions,
    frontend_context,
    dashboard_stats_context,
)

# Ticket views
from .tickets import (
    TicketsView,
    CreateTicketView,
    EditTicketView,
    ticket_crud,
)

# Project views
from .projects import (
    ProjectsView,
    CreateProjectView,
    EditProjectView,
    delete_project,
)

# Asset views
from .assets import (
    AssetsView,
    CreateAssetView,
    EditAssetView,
    delete_asset,
)

# User views
from .users import (
    UsersView,
    CreateUserView,
    EditUserView,
    delete_user,
)

# Profile views
from .profile import (
    ProfileView,
    LogsView,
    ReportsView,
)

