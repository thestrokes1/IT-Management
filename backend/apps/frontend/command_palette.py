"""
Command Palette Architecture for IT Management Platform.

Following Clean Architecture principles:
- Domain Layer: Command definitions and metadata
- Application Layer: Command resolution based on user permissions
- Interface Adapters: API endpoint and template tag for frontend

Commands:
- Navigate to entity by ID (tickets, assets, projects, users)
- Create Ticket / Asset
- View Logs
- Export Reports
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class CommandCategory(Enum):
    """Command categories for organization."""
    NAVIGATION = "navigation"
    CREATE = "create"
    VIEW = "view"
    EXPORT = "export"
    ADMIN = "admin"


@dataclass
class Command:
    """
    Domain entity representing a command.
    
    Attributes:
        key: Unique identifier for the command
        label: Display name shown in palette
        description: Brief help text
        category: Command category for organization
        url: URL to navigate to (None for actions requiring input)
        url_params: Optional dict of URL parameters
        required_roles: List of roles that can execute this command
        keyboard_shortcut: Optional keyboard shortcut (e.g., "Ctrl+K")
        icon: Font Awesome icon class
        input_type: Type of input required (None, "number", "text")
        input_placeholder: Placeholder for input field
        input_validation: Optional validation function name
    """
    key: str
    label: str
    description: str
    category: CommandCategory
    url: Optional[str] = None
    url_params: Dict[str, Any] = field(default_factory=dict)
    required_roles: List[str] = field(default_factory=list)
    keyboard_shortcut: Optional[str] = None
    icon: str = "fa-bolt"
    input_type: Optional[str] = None
    input_placeholder: str = ""
    input_validation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'key': self.key,
            'label': self.label,
            'description': self.description,
            'category': self.category.value,
            'url': self.url,
            'url_params': self.url_params,
            'icon': self.icon,
            'input_type': self.input_type,
            'input_placeholder': self.input_placeholder,
        }


# =============================================================================
# COMMAND REGISTRY
# =============================================================================

# All available commands in the system
COMMAND_REGISTRY: Dict[str, Command] = {
    # Navigation Commands
    'navigate_ticket': Command(
        key='navigate_ticket',
        label='Go to Ticket',
        description='Navigate to a ticket by ID',
        category=CommandCategory.NAVIGATION,
        url='/tickets/{ticket_id}/',
        url_params={'ticket_id': None},
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER'],
        icon='fa-ticket-alt',
        input_type='number',
        input_placeholder='Enter ticket ID',
        input_validation='positive_integer'
    ),
    'navigate_asset': Command(
        key='navigate_asset',
        label='Go to Asset',
        description='Navigate to an asset by ID',
        category=CommandCategory.NAVIGATION,
        url='/assets/{asset_id}/',
        url_params={'asset_id': None},
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER'],
        icon='fa-desktop',
        input_type='number',
        input_placeholder='Enter asset ID',
        input_validation='positive_integer'
    ),
    'navigate_project': Command(
        key='navigate_project',
        label='Go to Project',
        description='Navigate to a project by ID',
        category=CommandCategory.NAVIGATION,
        url='/projects/{project_id}/',
        url_params={'project_id': None},
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER'],
        icon='fa-project-diagram',
        input_type='number',
        input_placeholder='Enter project ID',
        input_validation='positive_integer'
    ),
    'navigate_user': Command(
        key='navigate_user',
        label='Go to User',
        description='Navigate to a user profile by ID',
        category=CommandCategory.NAVIGATION,
        url='/users/{user_id}/',
        url_params={'user_id': None},
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER'],
        icon='fa-user',
        input_type='number',
        input_placeholder='Enter user ID',
        input_validation='positive_integer'
    ),
    'navigate_dashboard': Command(
        key='navigate_dashboard',
        label='Dashboard',
        description='Go to the main dashboard',
        category=CommandCategory.NAVIGATION,
        url='/',
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER'],
        icon='fa-home',
    ),
    'navigate_tickets': Command(
        key='navigate_tickets',
        label='All Tickets',
        description='View all tickets',
        category=CommandCategory.NAVIGATION,
        url='/tickets/',
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER'],
        icon='fa-list',
    ),
    'navigate_assets': Command(
        key='navigate_assets',
        label='All Assets',
        description='View all assets',
        category=CommandCategory.NAVIGATION,
        url='/assets/',
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER'],
        icon='fa-desktop',
    ),
    'navigate_projects': Command(
        key='navigate_projects',
        label='All Projects',
        description='View all projects',
        category=CommandCategory.NAVIGATION,
        url='/projects/',
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER'],
        icon='fa-project-diagram',
    ),
    'navigate_users': Command(
        key='navigate_users',
        label='All Users',
        description='View all users',
        category=CommandCategory.NAVIGATION,
        url='/users/',
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER'],
        icon='fa-users',
    ),
    'navigate_logs': Command(
        key='navigate_logs',
        label='Activity Logs',
        description='View system activity logs',
        category=CommandCategory.NAVIGATION,
        url='/logs/',
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER'],
        icon='fa-list-alt',
    ),
    'navigate_reports': Command(
        key='navigate_reports',
        label='Reports',
        description='View reports and analytics',
        category=CommandCategory.NAVIGATION,
        url='/reports/',
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER'],
        icon='fa-chart-bar',
    ),
    'navigate_profile': Command(
        key='navigate_profile',
        label='My Profile',
        description='View your profile',
        category=CommandCategory.NAVIGATION,
        url='/profile/',
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER'],
        icon='fa-user',
    ),
    
    # Create Commands
    'create_ticket': Command(
        key='create_ticket',
        label='Create Ticket',
        description='Create a new support ticket',
        category=CommandCategory.CREATE,
        url='/create-ticket/',
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN', 'VIEWER'],
        icon='fa-plus',
    ),
    'create_asset': Command(
        key='create_asset',
        label='Add Asset',
        description='Register a new asset',
        category=CommandCategory.CREATE,
        url='/create-asset/',
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER'],
        icon='fa-plus',
    ),
    'create_project': Command(
        key='create_project',
        label='New Project',
        description='Create a new project',
        category=CommandCategory.CREATE,
        url='/create-project/',
        required_roles=['SUPERADMIN', 'MANAGER'],
        icon='fa-plus',
    ),
    'create_user': Command(
        key='create_user',
        label='Add User',
        description='Create a new user account',
        category=CommandCategory.CREATE,
        url='/create-user/',
        required_roles=['SUPERADMIN', 'IT_ADMIN'],
        icon='fa-user-plus',
    ),
    
    # View Commands
    'view_logs': Command(
        key='view_logs',
        label='View Logs',
        description='View system activity and security logs',
        category=CommandCategory.VIEW,
        url='/logs/',
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER'],
        icon='fa-list-alt',
    ),
    'view_reports': Command(
        key='view_reports',
        label='View Reports',
        description='View reports and analytics',
        category=CommandCategory.VIEW,
        url='/reports/',
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER'],
        icon='fa-chart-bar',
    ),
    
    # Export Commands
    'export_reports': Command(
        key='export_reports',
        label='Export Reports',
        description='Export data in CSV, Excel, or PDF format',
        category=CommandCategory.EXPORT,
        url='/reports/export/',
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER'],
        icon='fa-file-export',
    ),
    'export_tickets': Command(
        key='export_tickets',
        label='Export Tickets',
        description='Export tickets to CSV',
        category=CommandCategory.EXPORT,
        url='/reports/',
        required_roles=['SUPERADMIN', 'IT_ADMIN', 'MANAGER'],
        icon='fa-file-csv',
    ),
}


# =============================================================================
# COMMAND RESOLVER (Application Layer)
# =============================================================================

class CommandResolver:
    """
    Application service for resolving available commands based on user permissions.
    
    Follows Clean Architecture - this is the application layer that:
    - Knows about user roles (from domain)
    - Filters commands (application logic)
    - Returns safe-to-render data (no business logic in templates)
    """
    
    @staticmethod
    def get_user_role(user) -> Optional[str]:
        """Get user's role string."""
        if not user or not getattr(user, 'is_authenticated', False):
            return None
        if getattr(user, 'is_superuser', False):
            return 'SUPERADMIN'
        return getattr(user, 'role', 'VIEWER')
    
    @staticmethod
    def can_execute_command(command: Command, user_role: str) -> bool:
        """Check if user role can execute the command."""
        if not command.required_roles:
            return True
        return user_role in command.required_roles
    
    @classmethod
    def get_available_commands(cls, user) -> List[Dict[str, Any]]:
        """
        Get all commands available to the user.
        
        Returns:
            List of command dictionaries safe for JSON serialization
            No business logic in templates - all filtering done here
        """
        user_role = cls.get_user_role(user)
        if not user_role:
            return []
        
        available = []
        for command in COMMAND_REGISTRY.values():
            if cls.can_execute_command(command, user_role):
                available.append(command.to_dict())
        
        return available
    
    @classmethod
    def get_commands_by_category(cls, user) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get available commands organized by category.
        
        Returns:
            Dictionary with category as key and list of commands as value
        """
        user_role = cls.get_user_role(user)
        if not user_role:
            return {}
        
        categorized: Dict[str, List[Dict[str, Any]]] = {}
        for command in COMMAND_REGISTRY.values():
            if cls.can_execute_command(command, user_role):
                category = command.category.value
                if category not in categorized:
                    categorized[category] = []
                categorized[category].append(command.to_dict())
        
        return categorized
    
    @classmethod
    def resolve_navigation(cls, command_key: str, input_value: Any) -> Optional[str]:
        """
        Resolve a navigation command with input value.
        
        Args:
            command_key: The command key (e.g., 'navigate_ticket')
            input_value: The user input (e.g., ticket ID)
            
        Returns:
            Resolved URL or None if invalid
        """
        command = COMMAND_REGISTRY.get(command_key)
        if not command or command.category != CommandCategory.NAVIGATION:
            return None
        
        # Validate input based on command type
        if command.input_type == 'number':
            try:
                value = int(input_value)
                if value <= 0:
                    return None
            except (ValueError, TypeError):
                return None
        elif command.input_type == 'text':
            if not input_value or not input_value.strip():
                return None
            value = input_value.strip()
        else:
            return None
        
        # Build URL with parameter
        url = command.url
        if command.url_params:
            param_name = list(command.url_params.keys())[0]
            url = url.replace(f'{{{param_name}}}', str(value))
        
        return url


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_command_palette_data(user) -> Dict[str, Any]:
    """
    Get all data needed for the command palette.
    
    This is the main entry point for the frontend.
    
    Args:
        user: The current user object
        
    Returns:
        Dictionary with:
        - commands: List of available commands
        - categories: Commands organized by category
        - keyboard_shortcut: Default keyboard shortcut
    """
    return {
        'commands': CommandResolver.get_available_commands(user),
        'categories': CommandResolver.get_commands_by_category(user),
        'keyboard_shortcut': 'Ctrl+K',
        'categories_order': [
            'navigation',
            'create',
            'view',
            'export',
            'admin'
        ]
    }


def resolve_command(command_key: str, input_value: Any = None) -> Dict[str, Any]:
    """
    Resolve a command to its action.
    
    Args:
        command_key: The command key
        input_value: Optional input for commands requiring it
        
    Returns:
        Dictionary with:
        - type: 'navigation', 'action', or 'error'
        - url: Target URL (for navigation)
        - message: Status message
    """
    command = COMMAND_REGISTRY.get(command_key)
    if not command:
        return {
            'type': 'error',
            'message': f'Unknown command: {command_key}'
        }
    
    if command.category == CommandCategory.NAVIGATION:
        if command.input_type and input_value is None:
            return {
                'type': 'error',
                'message': f'Input required for: {command.label}'
            }
        
        url = CommandResolver.resolve_navigation(command_key, input_value)
        if not url:
            return {
                'type': 'error',
                'message': f'Invalid input for: {command.label}'
            }
        
        return {
            'type': 'navigation',
            'url': url,
            'message': f'Navigating to: {command.label}'
        }
    
    # For non-navigation commands, just return the URL
    return {
        'type': 'action',
        'url': command.url,
        'message': f'Opening: {command.label}'
    }
