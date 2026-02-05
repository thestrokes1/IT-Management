from django.urls import path
from django.views.generic import RedirectView
from django.views.generic import TemplateView

app_name = 'frontend'
from apps.frontend.views.tickets import (
    tickets,
    ticket_detail,
    create_ticket,
    edit_ticket,
    ticket_assign_self,
    ticket_assign_to_user,
    ticket_unassign_self,
    cancel_ticket,
    delete_ticket,
    reopen_ticket,
    ticket_crud,
)
from apps.frontend.views.assets import (
    assets,
    asset_detail,
    create_asset,
    edit_asset,
    asset_assign_self,
    asset_assign_to_user,
    asset_unassign_self,
    delete_asset,
    asset_crud,
)
from apps.frontend.views import (
    dashboard,
    login_view,
    logout_view,
    profile,
    profile_reopen_ticket,
    users,
    edit_user,
    create_user,
    change_user_role,
    logs,
    projects,
    project_detail,
    create_project,
    edit_project,
    delete_project,
    reports,
    export_reports,
)

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile, name='profile'),
    path('profile/reopen-ticket/<int:ticket_id>/', profile_reopen_ticket, name='profile_reopen_ticket'),
    
    # Tickets
    path('tickets/', tickets, name='tickets'),
    path('tickets/<int:ticket_id>/', ticket_detail, name='ticket-detail'),
    path('tickets/<int:ticket_id>/assign-self/', ticket_assign_self, name='ticket_assign_self'),
    path('tickets/<int:ticket_id>/assign-to/<int:user_id>/', ticket_assign_to_user, name='ticket_assign_to_user'),
    path('tickets/<int:ticket_id>/unassign-self/', ticket_unassign_self, name='ticket_unassign_self'),
    path('create-ticket/', create_ticket, name='create-ticket'),
    path('edit-ticket/<int:ticket_id>/', edit_ticket, name='edit-ticket'),
    path('cancel-ticket/<int:ticket_id>/', cancel_ticket, name='cancel-ticket'),
    path('delete-ticket/<int:ticket_id>/', delete_ticket, name='delete-ticket'),
    path('reopen-ticket/<int:ticket_id>/', reopen_ticket, name='reopen-ticket'),
    path('ticket-crud/', ticket_crud, name='ticket_crud'),
    
    # Assets
    path('assets/', assets, name='assets'),
    path('assets/<int:asset_id>/', asset_detail, name='asset-detail'),
    path('assets/<int:asset_id>/assign-self/', asset_assign_self, name='asset_assign_self'),
    path('assets/<int:asset_id>/assign-to/<int:user_id>/', asset_assign_to_user, name='asset_assign_to_user'),
    path('assets/<int:asset_id>/unassign-self/', asset_unassign_self, name='asset_unassign_self'),
    path('create-asset/', create_asset, name='create-asset'),
    path('edit-asset/<int:asset_id>/', edit_asset, name='edit-asset'),
    path('delete-asset/<int:asset_id>/', delete_asset, name='delete-asset'),
    path('delete-asset/<int:asset_id>/', delete_asset, name='asset_delete'),  # Alias for template compatibility
    path('asset-crud/<int:asset_id>/', asset_crud, name='asset_crud'),
    
    # Users
    path('users/', users, name='users'),
    path('user/<int:user_id>/', edit_user, name='user-detail'),  # Alias for template compatibility
    path('edit-user/<int:user_id>/', edit_user, name='edit-user'),
    path('create-user/', create_user, name='create-user'),
    path('change-user-role/<int:user_id>/', change_user_role, name='change-user-role'),
    
    # Logs
    path('logs/', logs, name='logs'),
    
    # Projects
    path('projects/', projects, name='projects'),
    path('projects/<int:project_id>/', RedirectView.as_view(url='/project/%(project_id)s/', permanent=True), name='projects-detail'),
    path('project/<int:project_id>/', project_detail, name='project-detail'),
    path('delete-project/<int:project_id>/', delete_project, name='delete-project'),
    path('delete-project/<int:project_id>/', delete_project, name='project_delete'),  # Alias for template compatibility
    path('create-project/', create_project, name='create-project'),
    path('edit-project/<int:project_id>/', edit_project, name='edit-project'),
    
# Reports
    path('reports/', reports, name='reports'),
    path('reports/export/', export_reports, name='export-reports'),
]
