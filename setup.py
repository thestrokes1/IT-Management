#!/usr/bin/env python3
"""
Database migration and setup script for IT Management Platform.
Handles initial database setup, migrations, and sample data creation.
"""

import os
import sys
import django
import subprocess
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model
from apps.users.models import User
from apps.assets.models import Asset, AssetCategory, AssetAssignment
from apps.projects.models import Project, Task, ProjectCategory
from apps.tickets.models import Ticket, TicketCategory
from django.utils import timezone
from datetime import timedelta


def create_superuser():
    """Create superuser if it doesn't exist."""
    User = get_user_model()
    
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            role='SUPERADMIN'
        )
        print("✅ Superuser 'admin' created with password 'admin123'")
        return admin
    else:
        print("ℹ️  Superuser 'admin' already exists")
        return User.objects.get(username='admin')


def create_sample_data():
    """Create sample data for testing."""
    print("🔄 Creating sample data...")
    
    # Create Asset Categories
    categories = [
        {'name': 'Laptops', 'description': 'Portable computers'},
        {'name': 'Desktops', 'description': 'Desktop computers'},
        {'name': 'Printers', 'description': 'Printing devices'},
        {'name': 'Software', 'description': 'Software licenses'},
        {'name': 'Mobile Devices', 'description': 'Smartphones and tablets'},
    ]
    
    asset_categories = []
    for cat_data in categories:
        category, created = AssetCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        asset_categories.append(category)
        if created:
            print(f"✅ Created asset category: {category.name}")
    
    # Create Sample Assets
    assets_data = [
        {
            'name': 'Dell Latitude 7420',
            'asset_tag': 'DELL-001',
            'serial_number': 'DL7420001',
            'category': asset_categories[0],  # Laptops
            'status': 'ACTIVE',
            'purchase_date': timezone.now() - timedelta(days=30),
            'warranty_expiry': timezone.now() + timedelta(days=365)
        },
        {
            'name': 'HP EliteDesk 800',
            'asset_tag': 'HP-001',
            'serial_number': 'HPED80001',
            'category': asset_categories[1],  # Desktops
            'status': 'ACTIVE',
            'purchase_date': timezone.now() - timedelta(days=60),
            'warranty_expiry': timezone.now() + timedelta(days=300)
        },
        {
            'name': 'Microsoft Office 365',
            'asset_tag': 'MS-O365-001',
            'category': asset_categories[3],  # Software
            'status': 'ACTIVE',
            'purchase_date': timezone.now() - timedelta(days=90),
            'license_key': 'XXXXX-XXXXX-XXXXX-XXXXX-XXXXX'
        }
    ]
    
    for asset_data in assets_data:
        asset, created = Asset.objects.get_or_create(
            asset_tag=asset_data['asset_tag'],
            defaults=asset_data
        )
        if created:
            print(f"✅ Created asset: {asset.name}")
    
    # Create Project Categories
    project_categories = [
        {'name': 'Infrastructure', 'description': 'IT infrastructure projects'},
        {'name': 'Software Development', 'description': 'Software development projects'},
        {'name': 'Security', 'description': 'Security-related projects'},
        {'name': 'Training', 'description': 'Training and development projects'},
    ]
    
    proj_categories = []
    for cat_data in project_categories:
        category, created = ProjectCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        proj_categories.append(category)
        if created:
            print(f"✅ Created project category: {category.name}")
    
    # Create Sample Projects
    admin_user = User.objects.get(username='admin')
    
    projects_data = [
        {
            'name': 'Network Infrastructure Upgrade',
            'description': 'Upgrade network infrastructure to support new office expansion',
            'category': proj_categories[0],
            'status': 'IN_PROGRESS',
            'priority': 'HIGH',
            'start_date': timezone.now() - timedelta(days=7),
            'due_date': timezone.now() + timedelta(days=21),
            'created_by': admin_user,
            'progress_percentage': 45
        },
        {
            'name': 'Security Audit 2025',
            'description': 'Annual security audit and compliance review',
            'category': proj_categories[2],
            'status': 'PLANNING',
            'priority': 'MEDIUM',
            'start_date': timezone.now() + timedelta(days=3),
            'due_date': timezone.now() + timedelta(days=60),
            'created_by': admin_user,
            'progress_percentage': 0
        }
    ]
    
    for proj_data in projects_data:
        project, created = Project.objects.get_or_create(
            name=proj_data['name'],
            defaults=proj_data
        )
        if created:
            print(f"✅ Created project: {project.name}")
    
    # Create Ticket Categories
    ticket_categories = [
        {'name': 'Hardware', 'description': 'Hardware-related issues'},
        {'name': 'Software', 'description': 'Software-related issues'},
        {'name': 'Network', 'description': 'Network connectivity issues'},
        {'name': 'Security', 'description': 'Security-related tickets'},
        {'name': 'General', 'description': 'General IT support'},
    ]
    
    for cat_data in ticket_categories:
        category, created = TicketCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults={'description': cat_data['description']}
        )
        if created:
            print(f"✅ Created ticket category: {category.name}")
    
    # Create Sample Tickets
    tickets_data = [
        {
            'title': 'Laptop Performance Issues',
            'description': 'Dell laptop running very slowly, needs performance check',
            'category': TicketCategory.objects.get(name='Hardware'),
            'priority': 'MEDIUM',
            'status': 'OPEN',
            'created_by': admin_user,
            'ticket_id': 'TK-001'
        },
        {
            'title': 'Network Connectivity Problems',
            'description': 'Cannot connect to VPN from home office',
            'category': TicketCategory.objects.get(name='Network'),
            'priority': 'HIGH',
            'status': 'IN_PROGRESS',
            'created_by': admin_user,
            'ticket_id': 'TK-002'
        },
        {
            'title': 'Software License Request',
            'description': 'Need Adobe Creative Suite for new designer',
            'category': TicketCategory.objects.get(name='Software'),
            'priority': 'LOW',
            'status': 'NEW',
            'created_by': admin_user,
            'ticket_id': 'TK-003'
        }
    ]
    
    for ticket_data in tickets_data:
        ticket, created = Ticket.objects.get_or_create(
            ticket_id=ticket_data['ticket_id'],
            defaults=ticket_data
        )
        if created:
            print(f"✅ Created ticket: {ticket.title}")
    
    print("✅ Sample data creation completed")


def run_migrations():
    """Run database migrations."""
    print("🔄 Running database migrations...")
    
    try:
        # Make migrations
        execute_from_command_line(['manage.py', 'makemigrations'])
        print("✅ Migrations created successfully")
        
        # Apply migrations
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migrations applied successfully")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True


def collect_static():
    """Collect static files."""
    print("🔄 Collecting static files...")
    
    try:
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("✅ Static files collected successfully")
    except Exception as e:
        print(f"❌ Static files collection failed: {e}")
        return False
    
    return True


def check_system_requirements():
    """Check if system requirements are met."""
    print("🔍 Checking system requirements...")
    
    issues = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append("Python 3.8+ is required")
    else:
        print(f"✅ Python version: {sys.version}")
    
    # Check Django installation
    try:
        import django
        print(f"✅ Django version: {django.get_version()}")
    except ImportError:
        issues.append("Django is not installed")
    
    # Check database connection
    try:
        from django.db import connection
        connection.ensure_connection()
        print("✅ Database connection successful")
    except Exception as e:
        issues.append(f"Database connection failed: {e}")
    
    # Check required packages
    required_packages = [
        'rest_framework',
        'django_filters',
        'psycopg2',  # or 'psycopg2-binary' for development
        'python-decouple',
        'drf_spectacular',
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ Package {package} installed")
        except ImportError:
            issues.append(f"Package {package} is missing")
    
    if issues:
        print("\n❌ Issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("\n✅ All system requirements met")
        return True


def create_directories():
    """Create all necessary directories if they don't exist."""
    directories = [
        'logs',
        'static',
        'media',
        'staticfiles'
    ]
    
    for directory in directories:
        dir_path = backend_dir / directory
        dir_path.mkdir(exist_ok=True)
        print(f"✅ Directory created/verified: {dir_path}")
    
    # Create log files
    log_files = ['django.log', 'access.log', 'error.log']
    for log_file in log_files:
        log_path = backend_dir / 'logs' / log_file
        if not log_path.exists():
            log_path.touch()
            print(f"✅ Created log file: {log_path}")
    
    print("✅ All directories setup completed")


def main():
    """Main setup function."""
    print("🚀 IT Management Platform Setup Script")
    print("=" * 50)
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Check requirements
    if not check_system_requirements():
        print("\n❌ System requirements not met. Please fix the issues and try again.")
        sys.exit(1)
    
    print("\n🔄 Running setup steps...")
    
    # Create all necessary directories
    create_directories()
    
    # Run migrations
    if not run_migrations():
        print("\n❌ Setup failed during migrations")
        sys.exit(1)
    
    # Create superuser
    create_superuser()
    
    # Create sample data
    create_sample_data()
    
    # Collect static files
    collect_static()
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the development server: python manage.py runserver")
    print("2. Access the application at: http://127.0.0.1:8000")
    print("3. Login with username: admin, password: admin123")
    print("4. Access admin panel at: http://127.0.0.1:8000/admin/")
    print("\nFor production deployment, see DEPLOYMENT.md")


if __name__ == '__main__':
    main()

