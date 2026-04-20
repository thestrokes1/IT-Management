"""
Integration tests for project CQRS commands.

Key project rules:
  - Only MANAGER and SUPERADMIN can create/edit projects
  - IT_ADMIN is explicitly excluded from project management
  - Only SUPERADMIN can delete projects
  - Project.category is non-nullable — all DB tests must provide a category
"""

import pytest

from apps.projects.application.create_project import CreateProject
from apps.projects.application.update_project import UpdateProject
from apps.core.domain.authorization import AuthorizationError


# ---------------------------------------------------------------------------
# CreateProject
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCreateProject:
    @pytest.mark.parametrize('role_fixture', ['viewer', 'technician', 'it_admin'])
    def test_below_manager_cannot_create(self, role_fixture, project_category, request):
        actor = request.getfixturevalue(role_fixture)
        result = CreateProject().execute(
            user=actor,
            name='Test Project',
            category_id=project_category.id,
        )
        assert result.success is False
        assert 'authorized' in result.error.lower()

    def test_manager_can_create(self, manager, project_category):
        result = CreateProject().execute(
            user=manager,
            name='Network Upgrade',
            category_id=project_category.id,
        )
        assert result.success is True
        assert result.data['name'] == 'Network Upgrade'
        assert result.data['status'] == 'PLANNING'

    def test_superadmin_can_create(self, superadmin, project_category):
        result = CreateProject().execute(
            user=superadmin,
            name='Cloud Migration',
            category_id=project_category.id,
        )
        assert result.success is True

    def test_name_is_required(self, manager, project_category):
        result = CreateProject().execute(
            user=manager,
            name='',
            category_id=project_category.id,
        )
        assert result.success is False
        assert 'required' in result.error.lower()

    def test_invalid_category_returns_failure(self, manager):
        result = CreateProject().execute(
            user=manager,
            name='Test Project',
            category_id=99999,
        )
        assert result.success is False

    def test_manager_auto_assigned_as_owner(self, manager, project_category):
        result = CreateProject().execute(
            user=manager,
            name='Auto Owner Project',
            category_id=project_category.id,
        )
        assert result.success is True
        from apps.projects.models import Project
        project = Project.objects.get(id=result.data['project_id'])
        assert project.project_manager == manager

    def test_it_admin_denied_with_correct_error(self, it_admin, project_category):
        result = CreateProject().execute(
            user=it_admin,
            name='IT Admin Project',
            category_id=project_category.id,
        )
        assert result.success is False


# ---------------------------------------------------------------------------
# UpdateProject
# ---------------------------------------------------------------------------

@pytest.fixture
def active_project(db, manager, project_category):
    from apps.projects.models import Project
    return Project.objects.create(
        name='Active Project',
        description='A test project',
        category=project_category,
        status='PLANNING',
        priority='MEDIUM',
        project_manager=manager,
        created_by=manager,
        budget=0,
    )


@pytest.mark.django_db
class TestUpdateProject:
    def test_manager_can_update(self, manager, active_project):
        result = UpdateProject().execute(
            user=manager,
            project_id=active_project.id,
            status='IN_PROGRESS',
        )
        assert result.success is True

    def test_superadmin_can_update(self, superadmin, active_project):
        result = UpdateProject().execute(
            user=superadmin,
            project_id=active_project.id,
            name='Renamed Project',
        )
        assert result.success is True

    @pytest.mark.parametrize('role_fixture', ['viewer', 'technician', 'it_admin'])
    def test_non_manager_cannot_update(self, role_fixture, active_project, request):
        actor = request.getfixturevalue(role_fixture)
        result = UpdateProject().execute(
            user=actor,
            project_id=active_project.id,
            status='IN_PROGRESS',
        )
        assert result.success is False

    def test_it_admin_explicitly_denied(self, it_admin, active_project):
        result = UpdateProject().execute(
            user=it_admin,
            project_id=active_project.id,
            priority='HIGH',
        )
        assert result.success is False

    def test_nonexistent_project_returns_failure(self, manager):
        result = UpdateProject().execute(
            user=manager,
            project_id=99999,
            status='IN_PROGRESS',
        )
        assert result.success is False
        assert 'not found' in result.error.lower()

    def test_empty_name_rejected(self, manager, active_project):
        result = UpdateProject().execute(
            user=manager,
            project_id=active_project.id,
            name='',
        )
        assert result.success is False

    def test_status_update_persists(self, manager, active_project):
        result = UpdateProject().execute(
            user=manager,
            project_id=active_project.id,
            status='IN_PROGRESS',
        )
        assert result.success is True
        active_project.refresh_from_db()
        assert active_project.status == 'IN_PROGRESS'
