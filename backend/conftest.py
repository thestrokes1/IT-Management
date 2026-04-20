"""
Shared pytest fixtures for the IT Management Platform test suite.
All DB fixtures are scoped to function (default) for clean isolation.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


def _make_user(username, role, n):
    return User.objects.create_user(
        username=username,
        email=f'{username}@test.local',
        password='testpass123',
        role=role,
        employee_id=f'EMP{n:04d}',
    )


@pytest.fixture
def viewer(db):
    return _make_user('viewer', 'VIEWER', 1)


@pytest.fixture
def technician(db):
    return _make_user('technician', 'TECHNICIAN', 2)


@pytest.fixture
def manager(db):
    return _make_user('manager', 'MANAGER', 3)


@pytest.fixture
def it_admin(db):
    return _make_user('it_admin', 'IT_ADMIN', 4)


@pytest.fixture
def superadmin(db):
    return _make_user('superadmin', 'SUPERADMIN', 5)


@pytest.fixture
def all_roles(viewer, technician, manager, it_admin, superadmin):
    return {
        'VIEWER': viewer,
        'TECHNICIAN': technician,
        'MANAGER': manager,
        'IT_ADMIN': it_admin,
        'SUPERADMIN': superadmin,
    }


# ---------------------------------------------------------------------------
# Domain object fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ticket_category(db):
    from apps.tickets.models import TicketCategory
    return TicketCategory.objects.create(name='General', description='General tickets')


@pytest.fixture
def ticket_type(db, ticket_category):
    from apps.tickets.models import TicketType
    return TicketType.objects.create(
        name='Standard',
        category=ticket_category,
        sla_hours=24,
    )


@pytest.fixture
def asset_category(db):
    from apps.assets.models import AssetCategory
    return AssetCategory.objects.create(name='Hardware', description='Physical devices')


@pytest.fixture
def project_category(db):
    from apps.projects.models import ProjectCategory
    return ProjectCategory.objects.create(name='IT Infrastructure', description='Infrastructure projects')
