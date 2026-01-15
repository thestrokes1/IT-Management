"""
Fixtures for frontend permission tests.
"""
import pytest
from django.urls import reverse


@pytest.fixture
def viewer_user(db):
    """Create a viewer user."""
    from apps.users.models import User
    user = User.objects.create_user(
        username='viewer',
        email='viewer@test.com',
        password='testpass123',
        role='VIEWER'
    )
    return user


@pytest.fixture
def technician_user(db):
    """Create a technician user."""
    from apps.users.models import User
    user = User.objects.create_user(
        username='technician',
        email='tech@test.com',
        password='testpass123',
        role='TECHNICIAN'
    )
    return user


@pytest.fixture
def manager_user(db):
    """Create a manager user."""
    from apps.users.models import User
    user = User.objects.create_user(
        username='manager',
        email='manager@test.com',
        password='testpass123',
        role='MANAGER'
    )
    return user


@pytest.fixture
def superadmin_user(db):
    """Create a superadmin user."""
    from apps.users.models import User
    user = User.objects.create_user(
        username='superadmin',
        email='sa@test.com',
        password='testpass123',
        role='SUPERADMIN'
    )
    return user


@pytest.fixture
def ticket_category(db):
    """Create a ticket category for testing."""
    from apps.tickets.models import TicketCategory
    return TicketCategory.objects.create(
        name='Test Category',
        description='A test category'
    )


@pytest.fixture
def ticket(ticket_category, technician_user):
    """Create a ticket for testing."""
    from apps.tickets.models import Ticket
    return Ticket.objects.create(
        title='Test Ticket',
        description='A test ticket',
        category=ticket_category,
        created_by=technician_user,
        priority='MEDIUM',
        status='NEW'
    )


@pytest.fixture
def asset_category(db):
    """Create an asset category for testing."""
    from apps.assets.models import AssetCategory
    return AssetCategory.objects.create(
        name='Test Category',
        description='A test category'
    )


@pytest.fixture
def asset(asset_category, technician_user):
    """Create an asset for testing."""
    from apps.assets.models import Asset
    return Asset.objects.create(
        name='Test Asset',
        description='A test asset',
        asset_type='HARDWARE',
        category=asset_category,
        created_by=technician_user,
        status='AVAILABLE'
    )


@pytest.fixture
def project_category(db):
    """Create a project category for testing."""
    from apps.projects.models import ProjectCategory
    return ProjectCategory.objects.create(
        name='Test Category',
        description='A test category'
    )


@pytest.fixture
def project(project_category, manager_user, technician_user):
    """Create a project for testing."""
    from apps.projects.models import Project
    return Project.objects.create(
        name='Test Project',
        description='A test project',
        category=project_category,
        created_by=technician_user,
        project_manager=manager_user,
        status='PLANNING',
        priority='MEDIUM'
    )


@pytest.fixture
def other_user(db):
    """Create another user for testing."""
    from apps.users.models import User
    user = User.objects.create_user(
        username='otheruser',
        email='other@test.com',
        password='testpass123',
        role='MANAGER'
    )
    return user

