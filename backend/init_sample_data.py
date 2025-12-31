#!/usr/bin/env python
"""
Initialize IT Management Platform with sample data
Run this after first migrations to populate the database
"""

import os
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from apps.assets.models import Asset, AssetCategory, AssetAssignment
from apps.projects.models import Project, Task, ProjectCategory, TaskCategory
from apps.tickets.models import Ticket, TicketCategory, TicketType, TicketComment
from apps.logs.models import ActivityLog, SecurityEvent
from apps.security.models import SecurityIncident

User = get_user_model()

def create_sample_users():
    """Create sample users"""
    print("Creating sample users...")
    
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@example.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True
        },
        {
            'username': 'manager',
            'email': 'manager@example.com',
            'first_name': 'Project',
            'last_name': 'Manager',
            'is_staff': True
        },
        {
            'username': 'technician',
            'email': 'tech@example.com',
            'first_name': 'IT',
            'last_name': 'Technician'
        },
        {
            'username': 'support',
            'email': 'support@example.com',
            'first_name': 'Support',
            'last_name': 'Agent'
        }
    ]
    
    created_count = 0
    for user_data in users_data:
        if not User.objects.filter(username=user_data['username']).exists():
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password='password123',  # Default password
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', '')
            )
            if user_data.get('is_staff'):
                user.is_staff = True
            if user_data.get('is_superuser'):
                user.is_superuser = True
            user.save()
            created_count += 1
            print(f"  ✓ Created: {user_data['username']}")
        else:
            print(f"  - Skipped: {user_data['username']} (already exists)")
    
    return created_count

def create_asset_categories():
    """Create sample asset categories"""
    print("\nCreating asset categories...")
    
    categories_data = [
        {'name': 'Desktop Computer', 'description': 'Desktop workstations and PCs'},
        {'name': 'Laptop/Mobile Computer', 'description': 'Laptops, notebooks, and mobile workstations'},
        {'name': 'Server/Storage', 'description': 'Servers, storage systems, and data center equipment'},
        {'name': 'Network Equipment', 'description': 'Routers, switches, firewalls, and network devices'},
        {'name': 'Printer/Peripheral', 'description': 'Printers, scanners, and other peripherals'},
        {'name': 'Monitor/Display', 'description': 'Monitors, displays, and projectors'},
        {'name': 'Operating System', 'description': 'Operating system licenses'},
        {'name': 'Productivity Software', 'description': 'Office suites and productivity tools'},
        {'name': 'Development Tools', 'description': 'IDEs, compilers, and development software'},
        {'name': 'Security Software', 'description': 'Antivirus, firewalls, and security tools'},
        {'name': 'Database Software', 'description': 'Database management systems'},
        {'name': 'Communication Software', 'description': 'Email, messaging, and collaboration tools'},
    ]
    
    created_count = 0
    for cat_data in categories_data:
        if not AssetCategory.objects.filter(name=cat_data['name']).exists():
            category = AssetCategory.objects.create(
                name=cat_data['name'],
                description=cat_data['description']
            )
            created_count += 1
            print(f"  ✓ Created: {cat_data['name']}")
        else:
            print(f"  - Skipped: {cat_data['name']} (already exists)")
    
    return created_count

def create_sample_assets():
    """Create sample assets"""
    print("\nCreating sample assets...")
    
    # Get or create a category for assets
    category = AssetCategory.objects.first()
    if not category:
        category = AssetCategory.objects.create(
            name='Desktop Computer',
            description='Desktop workstations and PCs'
        )
        print(f"  ✓ Created default category: {category.name}")
    
    assets_data = [
        {'name': 'Dell Laptop 1', 'serial_number': 'DL001', 'location': 'Office A'},
        {'name': 'HP Desktop 1', 'serial_number': 'HP001', 'location': 'Office B'},
        {'name': 'Cisco Router', 'serial_number': 'CISCO001', 'location': 'Server Room'},
        {'name': 'Printer Xerox', 'serial_number': 'XER001', 'location': 'Main Floor'},
        {'name': 'Backup Server', 'serial_number': 'BACKUP001', 'location': 'Server Room'},
    ]
    
    created_count = 0
    for asset_data in assets_data:
        if not Asset.objects.filter(serial_number=asset_data['serial_number']).exists():
            asset = Asset.objects.create(
                name=asset_data['name'],
                serial_number=asset_data['serial_number'],
                location=asset_data['location'],
                asset_type='HARDWARE',
                category=category,
                status='ACTIVE'
            )
            created_count += 1
            print(f"  ✓ Created: {asset_data['name']}")
        else:
            print(f"  - Skipped: {asset_data['name']} (already exists)")
    
    return created_count

def create_project_categories():
    """Create sample project categories"""
    print("\nCreating project categories...")
    
    categories_data = [
        {'name': 'Software Development', 'description': 'Application and software development projects', 'color': '#3B82F6'},
        {'name': 'Infrastructure & Network', 'description': 'IT infrastructure and network improvements', 'color': '#10B981'},
        {'name': 'Security & Compliance', 'description': 'Security audits and compliance projects', 'color': '#EF4444'},
        {'name': 'Cloud Migration', 'description': 'Cloud adoption and migration projects', 'color': '#8B5CF6'},
        {'name': 'Data Management', 'description': 'Data migration and data management projects', 'color': '#F59E0B'},
        {'name': 'User Support & Training', 'description': 'Training and user support initiatives', 'color': '#EC4899'},
        {'name': 'System Maintenance', 'description': 'System updates and maintenance projects', 'color': '#6366F1'},
        {'name': 'Research & Innovation', 'description': 'R&D and innovation projects', 'color': '#14B8A6'},
    ]
    
    created_count = 0
    for cat_data in categories_data:
        if not ProjectCategory.objects.filter(name=cat_data['name']).exists():
            category = ProjectCategory.objects.create(
                name=cat_data['name'],
                description=cat_data['description'],
                color=cat_data.get('color', '#3B82F6')
            )
            created_count += 1
            print(f"  ✓ Created: {cat_data['name']}")
        else:
            print(f"  - Skipped: {cat_data['name']} (already exists)")
    
    return created_count

def create_task_categories():
    """Create sample task categories"""
    print("\nCreating task categories...")
    
    categories_data = [
        {'name': 'Development', 'description': 'Software development tasks', 'color': '#3B82F6'},
        {'name': 'Testing', 'description': 'Testing and QA tasks', 'color': '#10B981'},
        {'name': 'Documentation', 'description': 'Documentation tasks', 'color': '#F59E0B'},
        {'name': 'Deployment', 'description': 'Deployment and release tasks', 'color': '#8B5CF6'},
        {'name': 'Maintenance', 'description': 'Maintenance and support tasks', 'color': '#EF4444'},
        {'name': 'Analysis', 'description': 'Analysis and planning tasks', 'color': '#6366F1'},
    ]
    
    created_count = 0
    for cat_data in categories_data:
        if not TaskCategory.objects.filter(name=cat_data['name']).exists():
            category = TaskCategory.objects.create(
                name=cat_data['name'],
                description=cat_data['description'],
                color=cat_data.get('color', '#3B82F6')
            )
            created_count += 1
            print(f"  ✓ Created: {cat_data['name']}")
        else:
            print(f"  - Skipped: {cat_data['name']} (already exists)")
    
    return created_count

def create_sample_projects():
    """Create sample projects"""
    print("\nCreating sample projects...")
    
    try:
        manager = User.objects.filter(username='manager').first() or User.objects.first()
        category = ProjectCategory.objects.first()
        
        if not category:
            category = ProjectCategory.objects.create(
                name='Software Development',
                description='Application and software development projects',
                color='#3B82F6'
            )
            print(f"  ✓ Created default category: {category.name}")
        
        projects_data = [
            {
                'name': 'Network Infrastructure Upgrade',
                'description': 'Upgrade all network infrastructure to modern standards',
                'status': 'IN_PROGRESS',
                'priority': 'HIGH'
            },
            {
                'name': 'Data Migration',
                'description': 'Migrate legacy system data to new platform',
                'status': 'PLANNING',
                'priority': 'HIGH'
            },
            {
                'name': 'Security Audit',
                'description': 'Comprehensive security audit of all systems',
                'status': 'IN_PROGRESS',
                'priority': 'CRITICAL'
            },
            {
                'name': 'Cloud Integration',
                'description': 'Integrate cloud services with on-premises infrastructure',
                'status': 'PLANNING',
                'priority': 'MEDIUM'
            }
        ]
        
        created_count = 0
        for proj_data in projects_data:
            if not Project.objects.filter(name=proj_data['name']).exists():
                project = Project.objects.create(
                    name=proj_data['name'],
                    description=proj_data['description'],
                    status=proj_data['status'],
                    priority=proj_data['priority'],
                    category=category,
                    project_manager=manager,
                    created_by=manager,
                    start_date=timezone.now().date(),
                    end_date=(timezone.now() + timedelta(days=30)).date()
                )
                created_count += 1
                print(f"  ✓ Created: {proj_data['name']}")
            else:
                print(f"  - Skipped: {proj_data['name']} (already exists)")
        
        return created_count
    except Exception as e:
        print(f"  ✗ Error creating projects: {str(e)}")
        return 0

def create_ticket_categories_with_types():
    """Create sample ticket categories with ticket types"""
    print("\nCreating ticket categories and types...")
    
    created_count = 0
    
    categories_data = [
        {
            'name': 'Hardware Issue',
            'description': 'Problems with computer hardware and devices',
            'color': '#EF4444',
            'types': [
                {'name': 'Desktop Issue', 'sla_hours': 8, 'description': 'Desktop computer problems'},
                {'name': 'Laptop Issue', 'sla_hours': 4, 'description': 'Laptop and mobile device problems'},
                {'name': 'Peripheral Issue', 'sla_hours': 24, 'description': 'Printer, scanner, and peripheral problems'},
                {'name': 'Network Device Issue', 'sla_hours': 4, 'description': 'Network hardware problems'},
            ]
        },
        {
            'name': 'Software Issue',
            'description': 'Problems with software applications',
            'color': '#3B82F6',
            'types': [
                {'name': 'Application Error', 'sla_hours': 8, 'description': 'Application crashes and errors'},
                {'name': 'Installation Request', 'sla_hours': 24, 'description': 'Software installation requests'},
                {'name': 'License Issue', 'sla_hours': 24, 'description': 'Software licensing problems'},
                {'name': 'Update Request', 'sla_hours': 48, 'description': 'Software update requests'},
            ]
        },
        {
            'name': 'Network/Connectivity',
            'description': 'Network and connectivity issues',
            'color': '#10B981',
            'types': [
                {'name': 'Internet Down', 'sla_hours': 1, 'description': 'Internet connectivity problems'},
                {'name': 'Slow Network', 'sla_hours': 4, 'description': 'Network performance issues'},
                {'name': 'WiFi Issue', 'sla_hours': 4, 'description': 'Wireless network problems'},
                {'name': 'VPN Issue', 'sla_hours': 2, 'description': 'VPN connection problems'},
            ]
        },
        {
            'name': 'User Access & Accounts',
            'description': 'User account and access issues',
            'color': '#F59E0B',
            'types': [
                {'name': 'Password Reset', 'sla_hours': 2, 'description': 'Password reset requests'},
                {'name': 'Account Locked', 'sla_hours': 1, 'description': 'Locked account recovery'},
                {'name': 'New Account Request', 'sla_hours': 24, 'description': 'New user account requests'},
                {'name': 'Permission Issue', 'sla_hours': 4, 'description': 'Access permission problems'},
            ]
        },
        {
            'name': 'Security Incident',
            'description': 'Security-related incidents',
            'color': '#DC2626',
            'types': [
                {'name': 'Malware Alert', 'sla_hours': 1, 'description': 'Malware and virus alerts'},
                {'name': 'Phishing Attempt', 'sla_hours': 1, 'description': 'Phishing attempt reports'},
                {'name': 'Suspicious Activity', 'sla_hours': 2, 'description': 'Suspicious activity reports'},
                {'name': 'Data Breach', 'sla_hours': 0.5, 'description': 'Potential data breach reports'},
            ]
        },
        {
            'name': 'System Outage',
            'description': 'System and service outages',
            'color': '#7C3AED',
            'types': [
                {'name': 'Server Down', 'sla_hours': 0.5, 'description': 'Server outage reports'},
                {'name': 'Service Unavailable', 'sla_hours': 1, 'description': 'Service availability issues'},
                {'name': 'Database Issue', 'sla_hours': 2, 'description': 'Database problems'},
                {'name': 'Email Down', 'sla_hours': 1, 'description': 'Email service problems'},
            ]
        },
        {
            'name': 'Email/Communication',
            'description': 'Email and communication issues',
            'color': '#0891B2',
            'types': [
                {'name': 'Email Not Sending', 'sla_hours': 2, 'description': 'Email sending problems'},
                {'name': 'Email Not Receiving', 'sla_hours': 2, 'description': 'Email receiving problems'},
                {'name': 'Calendar Issue', 'sla_hours': 4, 'description': 'Calendar synchronization problems'},
                {'name': 'Instant Messaging', 'sla_hours': 4, 'description': 'IM and chat problems'},
            ]
        },
        {
            'name': 'General Inquiry',
            'description': 'General questions and inquiries',
            'color': '#6B7280',
            'types': [
                {'name': 'How-to Question', 'sla_hours': 24, 'description': 'How-to and usage questions'},
                {'name': 'Information Request', 'sla_hours': 48, 'description': 'Information and documentation requests'},
                {'name': 'Feedback', 'sla_hours': 72, 'description': 'Feedback and suggestions'},
                {'name': 'General Support', 'sla_hours': 24, 'description': 'General support questions'},
            ]
        },
    ]
    
    for cat_data in categories_data:
        category, created = TicketCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'description': cat_data['description'],
                'color': cat_data.get('color', '#3B82F6')
            }
        )
        if created:
            created_count += 1
            print(f"  ✓ Created category: {cat_data['name']}")
        else:
            print(f"  - Category exists: {cat_data['name']}")
        
        # Create ticket types for this category
        for type_data in cat_data.get('types', []):
            type_created, _ = TicketType.objects.get_or_create(
                category=category,
                name=type_data['name'],
                defaults={
                    'description': type_data.get('description', ''),
                    'sla_hours': type_data.get('sla_hours', 24)
                }
            )
            if type_created:
                print(f"    ✓ Created type: {type_data['name']}")
    
    return created_count

def create_sample_tickets():
    """Create sample tickets"""
    print("\nCreating sample tickets...")
    
    try:
        support_user = User.objects.filter(username='support').first() or User.objects.first()
        ticket_category = TicketCategory.objects.first()
        ticket_type = TicketType.objects.first()
        
        if not ticket_category:
            ticket_category = TicketCategory.objects.create(
                name='Hardware Issue',
                description='Problems with computer hardware and devices',
                color='#EF4444'
            )
            print(f"  ✓ Created default category: {ticket_category.name}")
        
        if not ticket_type:
            ticket_type = TicketType.objects.create(
                category=ticket_category,
                name='Desktop Issue',
                sla_hours=8
            )
            print(f"  ✓ Created default type: {ticket_type.name}")
        
        tickets_data = [
            {
                'title': 'Email server down',
                'description': 'Email service not accessible',
                'status': 'OPEN',
                'priority': 'CRITICAL'
            },
            {
                'title': 'Password reset required',
                'description': 'User cannot reset password',
                'status': 'IN_PROGRESS',
                'priority': 'MEDIUM'
            },
            {
                'title': 'Printer not working',
                'description': 'Office printer offline',
                'status': 'NEW',
                'priority': 'LOW'
            },
            {
                'title': 'Software license expired',
                'description': 'Application license needs renewal',
                'status': 'OPEN',
                'priority': 'MEDIUM'
            }
        ]
        
        created_count = 0
        for ticket_data in tickets_data:
            if not Ticket.objects.filter(title=ticket_data['title']).exists():
                ticket = Ticket.objects.create(
                    title=ticket_data['title'],
                    description=ticket_data['description'],
                    status=ticket_data['status'],
                    priority=ticket_data['priority'],
                    category=ticket_category,
                    ticket_type=ticket_type,
                    requester=support_user,
                    assigned_to=support_user
                )
                created_count += 1
                print(f"  ✓ Created: {ticket_data['title']}")
            else:
                print(f"  - Skipped: {ticket_data['title']} (already exists)")
        
        return created_count
    except Exception as e:
        print(f"  ✗ Error creating tickets: {str(e)}")
        return 0

def create_activity_logs():
    """Create sample activity logs"""
    print("\nCreating sample activity logs...")
    
    try:
        user = User.objects.first()
        if not user:
            return 0
        
        activities = [
            {'action': 'User login', 'description': 'Admin user logged in'},
            {'action': 'Asset created', 'description': 'New asset added to inventory'},
            {'action': 'Ticket updated', 'description': 'Ticket status changed to resolved'},
            {'action': 'Project started', 'description': 'New project initiated'},
            {'action': 'Configuration change', 'description': 'System settings updated'},
        ]
        
        created_count = 0
        for activity in activities:
            if ActivityLog.objects.filter(
                action=activity['action'],
                user=user
            ).count() < 1:
                ActivityLog.objects.create(
                    action=activity['action'],
                    description=activity['description'],
                    user=user,
                    category='SYSTEM'
                )
                created_count += 1
                print(f"  ✓ Created: {activity['action']}")
        
        return created_count
    except Exception as e:
        print(f"  ✗ Error creating activity logs: {str(e)}")
        return 0

def main():
    """Main initialization function"""
    print("="*60)
    print("IT MANAGEMENT PLATFORM - DATABASE INITIALIZATION")
    print("="*60)
    
    total_created = 0
    
    total_created += create_sample_users()
    total_created += create_asset_categories()
    total_created += create_sample_assets()
    total_created += create_project_categories()
    total_created += create_task_categories()
    total_created += create_sample_projects()
    total_created += create_ticket_categories_with_types()
    total_created += create_sample_tickets()
    total_created += create_activity_logs()
    
    print("\n" + "="*60)
    print(f"✅ Initialization complete! Created {total_created} sample records.")
    print("="*60)
    print("\nDefault Users Created:")
    print("  Username: admin      Password: password123  (Superuser)")
    print("  Username: manager    Password: password123  (Staff)")
    print("  Username: technician Password: password123  (Regular)")
    print("  Username: support    Password: password123  (Regular)")
    print("\nCategories Created:")
    print("  Asset Categories: 12 categories")
    print("  Project Categories: 8 categories")
    print("  Task Categories: 6 categories")
    print("  Ticket Categories: 8 categories with 32 ticket types")
    print("\n⚠️  IMPORTANT: Change passwords in production!")

if __name__ == '__main__':
    main()

