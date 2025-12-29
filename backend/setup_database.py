#!/usr/bin/env python3
"""
IT Management Platform - Database Setup Script
Run this script to set up the database and create sample data.
"""

import os
import sys
import django

# Set up Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.core.management import execute_from_command_line
from django.contrib.auth.models import User
from datetime import datetime
import random

def setup_database():
    """Set up the database with migrations and sample data."""
    
    print("🚀 Setting up IT Management Platform Database...")
    
    # Run migrations
    print("📊 Running database migrations...")
    execute_from_command_line(['', 'makemigrations'])
    execute_from_command_line(['', 'migrate'])
    
    # Create superuser
    print("👤 Creating superuser...")
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print('✅ Superuser created: admin / admin123')
    else:
        print('ℹ️  Superuser already exists')
    
    # Import models
    try:
        from apps.users.models import UserRole
        from apps.assets.models import Asset, AssetCategory, AssetAssignment
        from apps.projects.models import Project, Task, ProjectCategory
        from apps.tickets.models import Ticket, TicketCategory, TicketComment
        from apps.logs.models import ActivityLog, LogCategory, SecurityEvent, SystemLog
        
        # Create sample roles
        if not UserRole.objects.exists():
            roles = [
                {'name': 'SuperAdmin', 'description': 'System Administrator'},
                {'name': 'IT_Admin', 'description': 'IT Administrator'},
                {'name': 'Manager', 'description': 'Project Manager'},
                {'name': 'Technician', 'description': 'IT Technician'},
                {'name': 'Viewer', 'description': 'Read-only User'}
            ]
            for role in roles:
                UserRole.objects.create(**role)
            print('✅ Sample roles created')
        
        # Create sample categories
        categories = [
            {'name': 'Hardware', 'description': 'Computer Equipment'},
            {'name': 'Software', 'description': 'Software Licenses'},
            {'name': 'Network', 'description': 'Network Equipment'},
        ]
        
        for cat_data in categories:
            AssetCategory.objects.get_or_create(**cat_data)
        
        # Create sample project categories
        project_cats = [
            {'name': 'Infrastructure', 'description': 'Infrastructure Projects'},
            {'name': 'Development', 'description': 'Development Projects'},
            {'name': 'Maintenance', 'description': 'Maintenance Projects'},
        ]
        
        for cat_data in project_cats:
            ProjectCategory.objects.get_or_create(**cat_data)
        
        # Create sample ticket categories
        ticket_cats = [
            {'name': 'Hardware', 'description': 'Hardware Issues'},
            {'name': 'Software', 'description': 'Software Issues'},
            {'name': 'Network', 'description': 'Network Issues'},
            {'name': 'Access', 'description': 'Access/Permission Issues'},
        ]
        
        for cat_data in ticket_cats:
            TicketCategory.objects.get_or_create(**cat_data)
        
        print('✅ Sample categories created')
        
        # Create sample users
        admin = User.objects.get(username='admin')
        users = []
        for i in range(5):
            username = f'user{i+1}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'{username}@example.com',
                    password='password123',
                    role='TECHNICIAN' if i < 3 else 'MANAGER'
                )
                users.append(user)
        print('✅ Sample users created')
        
        # Create sample assets
        asset_categories = AssetCategory.objects.all()
        for i in range(10):
            Asset.objects.get_or_create(
                name=f'Asset {i+1}',
                asset_tag=f'ASSET-{1000+i}',
                category=asset_categories[i % len(asset_categories)],
                status='ACTIVE',
                assigned_to=users[i % len(users)] if users else None,
                purchase_date=datetime.now(),
                warranty_expiry=datetime.now()
            )
        print('✅ Sample assets created')
        
        # Create sample projects
        project_cats = ProjectCategory.objects.all()
        for i in range(5):
            Project.objects.get_or_create(
                name=f'Project {i+1}',
                description=f'Description for project {i+1}',
                category=project_cats[i % len(project_cats)],
                status='ACTIVE',
                priority='HIGH' if i == 0 else 'MEDIUM',
                project_manager=users[0] if users else admin,
                start_date=datetime.now(),
                estimated_end_date=datetime.now()
            )
        print('✅ Sample projects created')
        
        # Create sample tickets
        ticket_cats = TicketCategory.objects.all()
        for i in range(15):
            Ticket.objects.get_or_create(
                title=f'Ticket {i+1}',
                description=f'Description for ticket {i+1}',
                category=ticket_cats[i % len(ticket_cats)],
                status='NEW' if i < 5 else 'OPEN',
                priority='HIGH' if i < 3 else 'MEDIUM',
                created_by=users[i % len(users)] if users else admin,
                assigned_to=users[(i+1) % len(users)] if users else None,
                ticket_id=f'TKT-{2025001+i}'
            )
        print('✅ Sample tickets created')
        
        print('🎉 Database setup completed successfully!')
        
    except ImportError as e:
        print(f"⚠️  Warning: Could not import some models: {e}")
        print("This might be expected during initial setup.")
    
    print("\n🎉 Setup completed!")
    print("\n🌐 Server is ready to start!")
    print("📋 Admin Login:")
    print("   URL: http://127.0.0.1:8000/admin/")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n👥 Sample Users:")
    print("   - user1 (Technician)")
    print("   - user2 (Technician)")
    print("   - user3 (Technician)")
    print("   - user4 (Manager)")
    print("   - user5 (Manager)")
    print("   Password for all: password123")

if __name__ == '__main__':
    setup_database()

