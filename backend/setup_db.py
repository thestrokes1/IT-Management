#!/usr/bin/env python3
"""
IT Management Platform - Complete Database Setup Script
This script applies migrations and seeds sample data.
"""

import os
import sys
import django

# Set up Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import connection
from datetime import datetime, timedelta
import random

User = get_user_model()

def check_migrations_applied():
    """Check which migrations have been applied."""
    print("=" * 60)
    print("CHECKING MIGRATION STATUS")
    print("=" * 60)
    
    from django.db.migrations.executor import MigrationExecutor
    from django.db.migrations.state import ProjectState
    
    executor = MigrationExecutor(connection)
    
    # Get applied migrations
    applied_migrations = executor.migrated_migrations
    plan = executor.migration_plan(executor.loader.disk_migrations)
    
    print(f"\nApplied migrations count: {len(applied_migrations)}")
    
    # Check for unapplied migrations
    unapplied = []
    for app_label, migrations in executor.loader.disk_migrations.items():
        for migration_name, migration in migrations.items():
            if migration_name not in executor.loader.applied_migrations:
                unapplied.append(f"  {app_label}: {migration_name}")
    
    if unapplied:
        print(f"\nUnapplied migrations ({len(unapplied)}):")
        for m in unapplied:
            print(m)
    else:
        print("\n✓ All migrations are applied!")
    
    return unapplied

def apply_migrations():
    """Apply all database migrations."""
    print("\n" + "=" * 60)
    print("APPLYING DATABASE MIGRATIONS")
    print("=" * 60)
    
    try:
        call_command('makemigrations', '--dry-run', verbosity=1)
        print("\n✓ No new migrations needed (all migrations exist)")
        
        call_command('migrate', verbosity=1)
        print("\n✓ All migrations applied successfully!")
        return True
    except Exception as e:
        print(f"\n✗ Error applying migrations: {e}")
        return False

def create_admin_user():
    """Create admin superuser."""
    print("\n" + "=" * 60)
    print("CREATING ADMIN SUPERUSER")
    print("=" * 60)
    
    admin_username = 'admin'
    admin_email = 'admin@itplatform.local'
    admin_password = 'admin123'
    
    if User.objects.filter(username=admin_username).exists():
        print(f"✓ Admin user '{admin_username}' already exists")
        admin = User.objects.get(username=admin_username)
        if not admin.is_superuser:
            admin.is_superuser = True
            admin.is_staff = True
            admin.save()
            print(f"✓ Updated admin user with superuser privileges")
        return admin
    else:
        admin = User.objects.create_superuser(
            username=admin_username,
            email=admin_email,
            password=admin_password,
            role='SUPERADMIN'
        )
        print(f"✓ Created admin user: {admin_username} / {admin_password}")
        return admin

def seed_sample_data(admin_user):
    """Seed the database with sample data."""
    print("\n" + "=" * 60)
    print("SEEDING SAMPLE DATA")
    print("=" * 60)
    
    total_created = 0
    
    # Import models
    from apps.users.models import UserProfile
    from apps.assets.models import Asset, AssetCategory, AssetAssignment, AssetStatus, AssetCondition
    from apps.projects.models import (
        Project, Task, ProjectCategory, ProjectMember
    )
    from apps.tickets.models import (
        Ticket, TicketCategory, TicketType, TicketComment
    )
    from apps.logs.models import ActivityLog, LogCategory
    from apps.security.models import SecurityIncident
    
    # Create sample users
    print("\n📋 Creating sample users...")
    users_data = [
        {'username': 'manager', 'email': 'manager@itplatform.local', 'first_name': 'Sarah', 'last_name': 'Johnson', 'role': 'MANAGER', 'department': 'IT Management'},
        {'username': 'technician1', 'email': 'tech1@itplatform.local', 'first_name': 'Mike', 'last_name': 'Chen', 'role': 'TECHNICIAN', 'department': 'Technical Support'},
        {'username': 'technician2', 'email': 'tech2@itplatform.local', 'first_name': 'Emily', 'last_name': 'Davis', 'role': 'TECHNICIAN', 'department': 'Technical Support'},
        {'username': 'viewer', 'email': 'viewer@itplatform.local', 'first_name': 'John', 'last_name': 'Smith', 'role': 'VIEWER', 'department': 'Operations'},
    ]
    
    users = []
    for user_data in users_data:
        if not User.objects.filter(username=user_data['username']).exists():
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password='password123',
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role=user_data['role'],
                department=user_data.get('department', ''),
                status='ACTIVE'
            )
            # Create user profile
            UserProfile.objects.get_or_create(user=user)
            users.append(user)
            print(f"  ✓ Created user: {user_data['username']}")
            total_created += 1
        else:
            user = User.objects.get(username=user_data['username'])
            users.append(user)
            print(f"  - Skipped: {user_data['username']} (exists)")
    
    # Create asset categories
    print("\n🏷️  Creating asset categories...")
    asset_categories = []
    category_data = [
        {'name': 'Laptop', 'description': 'Portable computers', 'color': '#3B82F6'},
        {'name': 'Desktop', 'description': 'Desktop computers', 'color': '#10B981'},
        {'name': 'Server', 'description': 'Server equipment', 'color': '#F59E0B'},
        {'name': 'Network', 'description': 'Network equipment', 'color': '#EF4444'},
        {'name': 'Printer', 'description': 'Printing devices', 'color': '#8B5CF6'},
        {'name': 'Mobile Device', 'description': 'Mobile phones and tablets', 'color': '#EC4899'},
    ]
    
    for cat in category_data:
        obj, created = AssetCategory.objects.get_or_create(name=cat['name'], defaults=cat)
        asset_categories.append(obj)
        if created:
            print(f"  ✓ Created category: {cat['name']}")
            total_created += 1
    
    # Create assets
    print("\n💻 Creating sample assets...")
    assets_data = [
        {'name': 'Dell Latitude 5420', 'serial_number': 'DELL-2024-001', 'category': asset_categories[0], 'location': 'Office A - Desk 1', 'purchase_date': datetime.now() - timedelta(days=180)},
        {'name': 'HP EliteBook 840', 'serial_number': 'HP-2024-002', 'category': asset_categories[0], 'location': 'Office A - Desk 2', 'purchase_date': datetime.now() - timedelta(days=90)},
        {'name': 'Dell OptiPlex 7000', 'serial_number': 'DELL-2024-003', 'category': asset_categories[1], 'location': 'Server Room', 'purchase_date': datetime.now() - timedelta(days=365)},
        {'name': 'Cisco Catalyst 9300', 'serial_number': 'CISCO-2024-001', 'category': asset_categories[3], 'location': 'Network Closet', 'purchase_date': datetime.now() - timedelta(days=60)},
        {'name': 'HP LaserJet Pro', 'serial_number': 'HP-2024-004', 'category': asset_categories[4], 'location': 'Main Office', 'purchase_date': datetime.now() - timedelta(days=200)},
        {'name': 'Dell PowerEdge R750', 'serial_number': 'DELL-2024-005', 'category': asset_categories[2], 'location': 'Data Center', 'purchase_date': datetime.now() - timedelta(days=30)},
    ]
    
    for asset_info in assets_data:
        if not Asset.objects.filter(serial_number=asset_info['serial_number']).exists():
            asset = Asset.objects.create(
                name=asset_info['name'],
                serial_number=asset_info['serial_number'],
                category=asset_info['category'],
                location=asset_info['location'],
                status='ACTIVE',
                purchase_date=asset_info['purchase_date'],
                purchase_cost=random.randint(500, 5000)
            )
            print(f"  ✓ Created asset: {asset_info['name']}")
            total_created += 1
    
    # Create project categories
    print("\n📁 Creating project categories...")
    project_categories = []
    proj_cat_data = [
        {'name': 'Infrastructure', 'description': 'Infrastructure projects', 'color': '#3B82F6'},
        {'name': 'Development', 'description': 'Software development projects', 'color': '#10B981'},
        {'name': 'Security', 'description': 'Security improvement projects', 'color': '#EF4444'},
        {'name': 'Maintenance', 'description': 'Maintenance and support projects', 'color': '#F59E0B'},
    ]
    
    for cat in proj_cat_data:
        obj, created = ProjectCategory.objects.get_or_create(name=cat['name'], defaults=cat)
        project_categories.append(obj)
        if created:
            print(f"  ✓ Created category: {cat['name']}")
            total_created += 1
    
    # Create sample projects
    print("\n📊 Creating sample projects...")
    projects_data = [
        {'name': 'Network Infrastructure Upgrade', 'description': 'Upgrade network infrastructure to support 10Gbps speeds', 'category': project_categories[0], 'priority': 'HIGH', 'manager_idx': 0},
        {'name': 'Customer Portal V2', 'description': 'Develop new customer portal with modern UI/UX', 'category': project_categories[1], 'priority': 'HIGH', 'manager_idx': 0},
        {'name': 'Security Audit & Hardening', 'description': 'Comprehensive security audit and system hardening', 'category': project_categories[2], 'priority': 'URGENT', 'manager_idx': 0},
        {'name': 'Cloud Migration Phase 1', 'description': 'Migrate on-premise servers to cloud infrastructure', 'category': project_categories[0], 'priority': 'MEDIUM', 'manager_idx': 0},
    ]
    
    for proj_info in projects_data:
        if not Project.objects.filter(name=proj_info['name']).exists():
            project = Project.objects.create(
                name=proj_info['name'],
                description=proj_info['description'],
                category=proj_info['category'],
                priority=proj_info['priority'],
                status='ACTIVE',
                project_manager=users[proj_info['manager_idx']] if users else admin_user,
                start_date=datetime.now().date(),
                end_date=(datetime.now() + timedelta(days=90)).date(),
                created_by=admin_user
            )
            # Add team members
            ProjectMember.objects.create(
                project=project,
                user=admin_user,
                role='MANAGER'
            )
            if len(users) > 1:
                ProjectMember.objects.create(
                    project=project,
                    user=users[1],
                    role='MEMBER'
                )
            print(f"  ✓ Created project: {proj_info['name']}")
            total_created += 1
    
    # Create ticket categories
    print("\n🎫 Creating ticket categories...")
    ticket_categories = []
    ticket_cat_data = [
        {'name': 'Hardware Issue', 'description': 'Hardware related problems', 'color': '#EF4444', 'sla_hours': 8},
        {'name': 'Software Issue', 'description': 'Software related problems', 'color': '#3B82F6', 'sla_hours': 24},
        {'name': 'Network Issue', 'description': 'Network connectivity problems', 'color': '#F59E0B', 'sla_hours': 4},
        {'name': 'Access Request', 'description': 'User access and permissions', 'color': '#10B981', 'sla_hours': 24},
        {'name': 'General Inquiry', 'description': 'General questions and inquiries', 'color': '#8B5CF6', 'sla_hours': 48},
    ]
    
    for cat in ticket_cat_data:
        obj, created = TicketCategory.objects.get_or_create(name=cat['name'], defaults=cat)
        ticket_categories.append(obj)
        if created:
            print(f"  ✓ Created category: {cat['name']}")
            total_created += 1
    
    # Create sample tickets
    print("\n📝 Creating sample tickets...")
    tickets_data = [
        {'title': 'Email not syncing on mobile device', 'description': 'Outlook app not syncing emails on iPhone', 'category': ticket_categories[1], 'priority': 'MEDIUM', 'requester_idx': 3},
        {'title': 'VPN connection failing', 'description': 'Cannot connect to corporate VPN from home office', 'category': ticket_categories[2], 'priority': 'HIGH', 'requester_idx': 0},
        {'title': 'Need new laptop for new hire', 'description': 'Provisioning laptop for new team member starting next week', 'category': ticket_categories[0], 'priority': 'MEDIUM', 'requester_idx': 1},
        {'title': 'Printer paper jam', 'description': 'Main office printer has constant paper jams', 'category': ticket_categories[0], 'priority': 'LOW', 'requester_idx': 2},
        {'title': 'Request admin access to SharePoint', 'description': 'Need admin access to project SharePoint site', 'category': ticket_categories[3], 'priority': 'MEDIUM', 'requester_idx': 3},
    ]
    
    for ticket_info in tickets_data:
        if not Ticket.objects.filter(title=ticket_info['title']).exists():
            ticket = Ticket.objects.create(
                title=ticket_info['title'],
                description=ticket_info['description'],
                category=ticket_info['category'],
                priority=ticket_info['priority'],
                status='NEW',
                requester=users[ticket_info['requester_idx']] if users else admin_user,
                created_by=admin_user,
                sla_due_at=datetime.now() + timedelta(hours=ticket_info['category'].sla_hours)
            )
            print(f"  ✓ Created ticket: {ticket_info['title'][:40]}...")
            total_created += 1
    
    # Create activity logs
    print("\n📜 Creating activity logs...")
    log_categories = []
    for cat_name in ['SYSTEM', 'USER', 'ASSET', 'TICKET', 'PROJECT']:
        obj, created = LogCategory.objects.get_or_create(name=cat_name)
        log_categories.append(obj)
        if created:
            total_created += 1
    
    activities = [
        ('User Login', 'Admin user logged in successfully', 'SYSTEM'),
        ('Asset Created', 'New asset Dell Latitude 5420 added to inventory', 'ASSET'),
        ('Ticket Created', 'New support ticket created: Email not syncing', 'TICKET'),
        ('Project Updated', 'Network Infrastructure Upgrade status changed', 'PROJECT'),
        ('Password Reset', 'Password reset requested for user manager', 'USER'),
    ]
    
    for action, desc, cat_name in activities:
        if not ActivityLog.objects.filter(action=action, description=desc).exists():
            log = ActivityLog.objects.create(
                action=action,
                description=desc,
                category=cat_name,
                user=admin_user,
                ip_address='192.168.1.100'
            )
            print(f"  ✓ Created log: {action}")
            total_created += 1
    
    # Create sample security incidents
    print("\n🔒 Creating sample security incidents...")
    severity_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    incidents_data = [
        {'title': 'Failed login attempt detected', 'description': 'Multiple failed login attempts from IP 45.33.32.156', 'severity': 'LOW'},
        {'title': 'Suspicious file download', 'description': 'Unusual large file download from workstation WS-042', 'severity': 'MEDIUM'},
        {'title': 'Unauthorized access attempt', 'description': 'Attempted access to restricted system component', 'severity': 'HIGH'},
    ]
    
    for incident_info in incidents_data:
        if not SecurityIncident.objects.filter(title=incident_info['title']).exists():
            incident = SecurityIncident.objects.create(
                title=incident_info['title'],
                description=incident_info['description'],
                severity=incident_info['severity'],
                status='OPEN',
                reported_by=admin_user,
                detected_at=datetime.now() - timedelta(hours=random.randint(1, 48))
            )
            print(f"  ✓ Created incident: {incident_info['title'][:40]}...")
            total_created += 1
    
    return total_created

def main():
    """Main setup function."""
    print("\n" + "=" * 60)
    print("  IT MANAGEMENT PLATFORM - DATABASE SETUP")
    print("=" * 60)
    
    # Check migrations
    unapplied = check_migrations_applied()
    
    # Apply migrations
    if unapplied:
        apply_migrations()
    
    # Create admin user
    admin_user = create_admin_user()
    
    # Seed sample data
    total_created = seed_sample_data(admin_user)
    
    # Summary
    print("\n" + "=" * 60)
    print("  SETUP COMPLETE!")
    print("=" * 60)
    print(f"\n✓ Total records created: {total_created}")
    print("\n📋 Login Credentials:")
    print("   Django Admin: http://127.0.0.1:8000/admin/")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n👥 Sample Users:")
    print("   - manager / password123")
    print("   - technician1 / password123")
    print("   - technician2 / password123")
    print("   - viewer / password123")
    print("\n🚀 Run the server with: python manage.py runserver")
    print("=" * 60)

if __name__ == '__main__':
    main()

