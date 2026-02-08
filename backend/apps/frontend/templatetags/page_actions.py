"""
Page-specific action template tags.
Provides context-aware actions for the sidebar based on current page.

Usage:
    {% load page_actions %}
    {% render_page_actions actions %}
    {% if action_allowed 'create_ticket' %}...{% endif %}
"""

from django import template
from django.template import Library, TemplateSyntaxError

register = template.Library()

# Action definitions: (action_key, display_name, icon, url_name, required_permissions)
# Required permissions is a list of role strings that can perform the action
PAGE_ACTIONS = {
    'dashboard': [
        {'key': 'view_reports', 'label': 'View Reports', 'icon': 'fa-chart-bar', 'url': 'frontend:reports', 'roles': ['SUPERADMIN', 'MANAGER']},
        {'key': 'export_data', 'label': 'Export Data', 'icon': 'fa-download', 'url': 'frontend:reports', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']},
    ],
    'tickets': [
        {'key': 'create_ticket', 'label': 'Create Ticket', 'icon': 'fa-plus', 'url': 'frontend:create-ticket', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER']},
        {'key': 'view_all_tickets', 'label': 'All Tickets', 'icon': 'fa-list', 'url': 'frontend:tickets', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER']},
        {'key': 'my_tickets', 'label': 'My Tickets', 'icon': 'fa-user', 'url': 'frontend:tickets', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER']},
    ],
    'ticket_detail': [
        {'key': 'edit_ticket', 'label': 'Edit Ticket', 'icon': 'fa-edit', 'url': 'frontend:edit-ticket', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN']},
        {'key': 'assign_ticket', 'label': 'Assign', 'icon': 'fa-user-plus', 'url': 'frontend:ticket_assign_self', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN']},
        {'key': 'close_ticket', 'label': 'Close Ticket', 'icon': 'fa-check', 'url': 'frontend:cancel-ticket', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']},
        {'key': 'add_comment', 'label': 'Add Comment', 'icon': 'fa-comment', 'url': 'frontend:ticket-detail', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER']},
    ],
    'assets': [
        {'key': 'create_asset', 'label': 'Add Asset', 'icon': 'fa-plus', 'url': 'frontend:create-asset', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']},
        {'key': 'view_all_assets', 'label': 'All Assets', 'icon': 'fa-desktop', 'url': 'frontend:assets', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER']},
        {'key': 'my_assets', 'label': 'My Assets', 'icon': 'fa-user', 'url': 'frontend:assets', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER']},
    ],
    'asset_detail': [
        {'key': 'edit_asset', 'label': 'Edit Asset', 'icon': 'fa-edit', 'url': 'frontend:edit-asset', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']},
        {'key': 'assign_asset', 'label': 'Assign', 'icon': 'fa-user-plus', 'url': 'frontend:asset_assign_self', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN']},
        {'key': 'decommission', 'label': 'Decommission', 'icon': 'fa-trash', 'url': 'frontend:asset_delete', 'roles': ['SUPERADMIN', 'IT_ADMIN']},
    ],
    'projects': [
        {'key': 'create_project', 'label': 'New Project', 'icon': 'fa-plus', 'url': 'frontend:create-project', 'roles': ['SUPERADMIN', 'MANAGER']},
        {'key': 'view_all_projects', 'label': 'All Projects', 'icon': 'fa-project-diagram', 'url': 'frontend:projects', 'roles': ['SUPERADMIN', 'MANAGER']},
    ],
    'project_detail': [
        {'key': 'edit_project', 'label': 'Edit Project', 'icon': 'fa-edit', 'url': 'frontend:edit-project', 'roles': ['SUPERADMIN', 'MANAGER']},
        {'key': 'delete_project', 'label': 'Delete', 'icon': 'fa-trash', 'url': 'frontend:delete-project', 'roles': ['SUPERADMIN', 'MANAGER']},
        {'key': 'manage_members', 'label': 'Manage Team', 'icon': 'fa-users', 'url': 'frontend:project-detail', 'roles': ['SUPERADMIN', 'MANAGER']},
    ],
    'users': [
        {'key': 'create_user', 'label': 'Add User', 'icon': 'fa-user-plus', 'url': 'frontend:create-user', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']},
        {'key': 'view_all_users', 'label': 'All Users', 'icon': 'fa-users', 'url': 'frontend:users', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']},
    ],
    'user_detail': [
        {'key': 'edit_user', 'label': 'Edit User', 'icon': 'fa-edit', 'url': 'frontend:edit-user', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']},
        {'key': 'change_role', 'label': 'Change Role', 'icon': 'fa-user-cog', 'url': 'frontend:change-user-role', 'roles': ['SUPERADMIN', 'IT_ADMIN']},
        {'key': 'deactivate_user', 'label': 'Deactivate', 'icon': 'fa-user-slash', 'url': 'frontend:users', 'roles': ['SUPERADMIN', 'IT_ADMIN']},
    ],
    'logs': [
        {'key': 'export_logs', 'label': 'Export Logs', 'icon': 'fa-download', 'url': 'frontend:logs', 'roles': ['SUPERADMIN', 'MANAGER']},
        {'key': 'clear_logs', 'label': 'Clear Filters', 'icon': 'fa-times', 'url': 'frontend:logs', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']},
    ],
    'reports': [
        {'key': 'export_csv', 'label': 'Export CSV', 'icon': 'fa-file-csv', 'url': 'frontend:export-reports', 'roles': ['SUPERADMIN', 'MANAGER']},
        {'key': 'export_pdf', 'label': 'Export PDF', 'icon': 'fa-file-pdf', 'url': 'frontend:export-reports', 'roles': ['SUPERADMIN', 'MANAGER']},
        {'key': 'filter_reports', 'label': 'Filters', 'icon': 'fa-filter', 'url': 'frontend:reports', 'roles': ['SUPERADMIN', 'MANAGER']},
    ],
    'profile': [
        {'key': 'edit_profile', 'label': 'Edit Profile', 'icon': 'fa-user-edit', 'url': 'frontend:profile', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER']},
        {'key': 'view_ticket_history', 'label': 'Ticket History', 'icon': 'fa-history', 'url': 'frontend:profile', 'roles': ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER']},
    ],
}


def get_user_role(user):
    """Get user's role string."""
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    if getattr(user, 'is_superuser', False):
        return 'SUPERADMIN'
    return getattr(user, 'role', 'VIEWER')


def filter_actions_by_role(actions, user_role):
    """Filter actions based on user's role."""
    filtered = []
    for action in actions:
        if user_role in action.get('roles', []):
            filtered.append(action)
    return filtered


@register.simple_tag
def get_page_actions(page_key, user):
    """
    Get filtered actions for a page based on user's role.
    
    Usage: {% get_page_actions 'tickets' user as actions %}
    """
    user_role = get_user_role(user)
    if not user_role:
        return []
    
    if page_key not in PAGE_ACTIONS:
        return []
    
    return filter_actions_by_role(PAGE_ACTIONS[page_key], user_role)


@register.simple_tag
def action_allowed(action_key, user):
    """
    Check if a specific action is allowed for the user.
    
    Usage: {% if action_allowed 'create_ticket' user %}...{% endif %}
    """
    user_role = get_user_role(user)
    if not user_role:
        return False
    
    # Search all pages for the action
    for page_key, actions in PAGE_ACTIONS.items():
        for action in actions:
            if action['key'] == action_key and user_role in action.get('roles', []):
                return True
    return False


class RenderPageActionsNode(template.Node):
    def __init__(self, actions_var, nodelist=None):
        self.actions_var = actions_var
        self.nodelist = nodelist
    
    def render(self, context):
        try:
            actions = template.Variable(self.actions_var).resolve(context)
            if not actions:
                return ''
            
            html = '<div class="page-actions space-y-2 mt-4">'
            for action in actions:
                url = action.get('url', '#')
                label = action.get('label', '')
                icon = action.get('icon', 'fa-circle')
                
                # Build URL if it's a URL name
                from django.urls import reverse, NoReverseMatch
                try:
                    if url and not url.startswith('#'):
                        url = reverse(url)
                except (NoReverseMatch, TypeError):
                    url = '#'
                
                html += f'''
                <a href="{url}" class="flex items-center gap-2 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
                    <i class="fas {icon} text-gray-400 w-4"></i>
                    <span>{label}</span>
                </a>
                '''
            html += '</div>'
            return html
        except Exception as e:
            return ''


@register.tag
def render_page_actions(parser, token):
    """
    Render a list of page actions.
    
    Usage:
        {% get_page_actions 'tickets' user as actions %}
        {% render_page_actions actions %}
    """
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError(f"'{token.contents.split()[0]}' tag requires at least 1 argument")
    actions_var = bits[1]
    nodelist = parser.parse(('endrender_page_actions',))
    parser.delete_first_token()
    return RenderPageActionsNode(actions_var, nodelist)


@register.simple_tag
def get_breadcrumbs(current_page, user, **kwargs):
    """
    Generate breadcrumbs for the current page.
    
    Usage: {% get_breadcrumbs 'tickets' user as breadcrumbs %}
    """
    breadcrumbs = [
        {'label': 'Dashboard', 'url': 'frontend:dashboard', 'icon': 'fa-home'}
    ]
    
    page_titles = {
        'tickets': 'Tickets',
        'assets': 'Assets',
        'projects': 'Projects',
        'users': 'Users',
        'logs': 'Activity Logs',
        'reports': 'Reports',
        'profile': 'Profile',
        'ticket_detail': 'Ticket Details',
        'asset_detail': 'Asset Details',
        'project_detail': 'Project Details',
        'user_detail': 'User Details',
        'create-ticket': 'Create Ticket',
        'create-asset': 'Create Asset',
        'create-project': 'Create Project',
        'create-user': 'Create User',
        'edit-ticket': 'Edit Ticket',
        'edit-asset': 'Edit Asset',
        'edit-project': 'Edit Project',
        'edit-user': 'Edit User',
    }
    
    if current_page in page_titles:
        breadcrumbs.append({
            'label': page_titles[current_page],
            'url': None,
            'icon': None
        })
    
    return breadcrumbs
