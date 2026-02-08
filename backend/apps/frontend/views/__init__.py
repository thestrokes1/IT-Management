# Frontend views package.
# Re-exports views from domain-specific modules using relative imports.

# Auth views
from .auth import (
    LoginView,
    LogoutView,
    Error404View,
    Error500View,
    MaintenanceView,
    login_view,
    logout_view,
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
    dashboard,
    command_palette_api,
)

# Ticket views
from .tickets import (
    TicketsView,
    CreateTicketView,
    EditTicketView,
    TicketDetailView,
    ticket_crud,
    ticket_assign_self,
    tickets,
    ticket_detail,
    create_ticket,
    edit_ticket,
    cancel_ticket,
    delete_ticket,
    reopen_ticket,
)

# Project views
from .projects import (
    ProjectsView,
    CreateProjectView,
    EditProjectView,
    delete_project,
    project_crud,
    projects,
    project_detail,
    create_project,
    edit_project,
)

# Asset views
from .assets import (
    AssetsView,
    AssetDetailView,
    CreateAssetView,
    EditAssetView,
    delete_asset,
    asset_crud,
    asset_assign_self,
    asset_unassign_self,
    assets,
    asset_detail,
    create_asset,
    edit_asset,
)

# User views
from .users import (
    UsersView,
    CreateUserView,
    EditUserView,
    delete_user,
    users,
    edit_user,
    create_user,
    change_user_role,
)

# Profile views
from .profile import (
    ProfileView,
    LogsView,
    ReportsView,
    profile,
    logs,
    reports,
    export_reports,
    profile_reopen_ticket,
)

# Logs views (Enterprise Timeline UI)
from .logs import (
    LogsView,
    logs,
    logs_api,
    logs_export,
    logs_detail,
)
