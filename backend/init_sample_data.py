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
from apps.projects.models import Project, Task
from apps.tickets.models import Ticket, TicketCategory, TicketComment
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

def create_sample_assets():
    """Create sample assets"""
    print("\nCreating sample assets...")
    
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
                status='ACTIVE',
                condition='GOOD'
            )
            created_count += 1
            print(f"  ✓ Created: {asset_data['name']}")
        else:
            print(f"  - Skipped: {asset_data['name']} (already exists)")
    
    return created_count

def create_sample_projects():
    """Create sample projects"""
    print("\nCreating sample projects...")
    
    try:
        manager = User.objects.filter(username='manager').first() or User.objects.first()
        
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
                    created_by=manager,
                    assigned_to=manager,
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

def create_sample_tickets():
    """Create sample tickets"""
    print("\nCreating sample tickets...")
    
    try:
        support_user = User.objects.filter(username='support').first() or User.objects.first()
        
        tickets_data = [
            {
                'title': 'Email server down',
                'description': 'Email service not accessible',
                'status': 'OPEN',
                'priority': 'CRITICAL',
                'category': 'SYSTEM_OUTAGE'
            },
            {
                'title': 'Password reset required',
                'description': 'User cannot reset password',
                'status': 'IN_PROGRESS',
                'priority': 'MEDIUM',
                'category': 'USER_ACCESS'
            },
            {
                'title': 'Printer not working',
                'description': 'Office printer offline',
                'status': 'NEW',
                'priority': 'LOW',
                'category': 'HARDWARE_ISSUE'
            },
            {
                'title': 'Software license expired',
                'description': 'Application license needs renewal',
                'status': 'OPEN',
                'priority': 'MEDIUM',
                'category': 'LICENSE_MANAGEMENT'
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
                    category=ticket_data['category'],
                    created_by=support_user,
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
    total_created += create_sample_assets()
    total_created += create_sample_projects()
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
    print("\n⚠️  IMPORTANT: Change passwords in production!")

if __name__ == '__main__':
    main()
