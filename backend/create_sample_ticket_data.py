#!/usr/bin/env python
"""
Create sample ticket categories and types for testing.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.tickets.models import TicketCategory, TicketType

def create_sample_data():
    """Create sample categories and ticket types."""
    
    # Create categories
    categories_data = [
        {'name': 'Hardware', 'description': 'Hardware related issues', 'color': '#3B82F6'},
        {'name': 'Software', 'description': 'Software related issues', 'color': '#10B981'},
        {'name': 'Network', 'description': 'Network connectivity issues', 'color': '#F59E0B'},
        {'name': 'Account', 'description': 'User account and access issues', 'color': '#EF4444'},
        {'name': 'Other', 'description': 'Miscellaneous issues', 'color': '#6B7280'},
    ]
    
    print("Creating Ticket Categories...")
    for cat_data in categories_data:
        category, created = TicketCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        status = "Created" if created else "Already exists"
        print(f"  {status}: {category.name}")
    
    # Create ticket types for each category
    ticket_types_data = [
        # Hardware types
        {'category_name': 'Hardware', 'name': 'Computer Issue', 'description': 'Desktop or laptop problems', 'sla_hours': 8},
        {'category_name': 'Hardware', 'name': 'Printer Issue', 'description': 'Printer not working', 'sla_hours': 4},
        {'category_name': 'Hardware', 'name': 'Monitor Issue', 'description': 'Display problems', 'sla_hours': 8},
        {'category_name': 'Hardware', 'name': 'Peripheral', 'description': 'Keyboard, mouse, etc.', 'sla_hours': 24},
        
        # Software types
        {'category_name': 'Software', 'name': 'Application Error', 'description': 'Application crashes or errors', 'sla_hours': 4},
        {'category_name': 'Software', 'name': 'Installation Request', 'description': 'New software installation', 'sla_hours': 24},
        {'category_name': 'Software', 'name': 'License Issue', 'description': 'Software licensing problems', 'sla_hours': 8},
        {'category_name': 'Software', 'name': 'Update Request', 'description': 'Software update requests', 'sla_hours': 24},
        
        # Network types
        {'category_name': 'Network', 'name': 'Connection Issue', 'description': 'Cannot connect to network', 'sla_hours': 2},
        {'category_name': 'Network', 'name': 'Internet Slow', 'description': 'Slow internet connection', 'sla_hours': 4},
        {'category_name': 'Network', 'name': 'VPN Issue', 'description': 'VPN connection problems', 'sla_hours': 4},
        {'category_name': 'Network', 'name': 'WiFi Issue', 'description': 'Wireless network problems', 'sla_hours': 4},
        
        # Account types
        {'category_name': 'Account', 'name': 'Password Reset', 'description': 'Password reset requests', 'sla_hours': 1},
        {'category_name': 'Account', 'name': 'Access Request', 'description': 'Access to systems/resources', 'sla_hours': 8},
        {'category_name': 'Account', 'name': 'Account Locked', 'description': 'Locked out of account', 'sla_hours': 1},
        {'category_name': 'Account', 'name': 'New User Setup', 'description': 'New user account creation', 'sla_hours': 8},
        
        # Other types
        {'category_name': 'Other', 'name': 'General Inquiry', 'description': 'General questions', 'sla_hours': 24},
        {'category_name': 'Other', 'name': 'Suggestion', 'description': 'Improvement suggestions', 'sla_hours': 48},
    ]
    
    print("\nCreating Ticket Types...")
    for tt_data in ticket_types_data:
        try:
            category = TicketCategory.objects.get(name=tt_data['category_name'])
            tt_data['category'] = category
            del tt_data['category_name']
            
            ticket_type, created = TicketType.objects.get_or_create(
                category=category,
                name=tt_data['name'],
                defaults=tt_data
            )
            status = "Created" if created else "Already exists"
            print(f"  {status}: {ticket_type.name} ({category.name})")
        except TicketCategory.DoesNotExist:
            print(f"  Skipped: Category '{tt_data['category_name']}' not found")
    
    print("\nDone!")

if __name__ == '__main__':
    create_sample_data()
