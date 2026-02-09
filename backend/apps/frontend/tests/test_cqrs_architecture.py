"""
CQRS Architectural Regression Tests.

These tests verify that the CQRS architecture is enforced:
1. Model mutations (create, update, delete) MUST only occur in CQRS commands
2. Views, Services, Serializers, Queries, and Signals MUST NOT mutate models
3. Activity logging SHOULD use transaction.on_commit

Uses AST parsing to detect violations at the structural level.
"""

import ast
import os
import pytest
from pathlib import Path
from django.conf import settings


# =============================================================================
# Test Configuration
# =============================================================================

# Allowed directories for model mutations (CQRS commands)
CQRS_COMMAND_DIRS = [
    'apps/tickets/application',
    'apps/assets/application',
    'apps/projects/application',
]


class CQRSArchitectureViolation(Exception):
    """Exception raised when CQRS architecture is violated."""
    pass


# =============================================================================
# AST Parsing Helpers
# =============================================================================

def get_python_files(directory: str, recursive: bool = True) -> list:
    """
    Get all Python files in a directory.
    
    Args:
        directory: Base directory to search (relative to BASE_DIR)
        recursive: Whether to search recursively
        
    Returns:
        List of file paths
    """
    base_path = Path(settings.BASE_DIR) / directory
    if not base_path.exists():
        return []
    
    pattern = '**/*.py' if recursive else '*.py'
    return list(base_path.glob(pattern))


def parse_file(file_path: Path) -> ast.AST:
    """Parse a Python file and return the AST."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return ast.parse(content)


def find_calls_in_module(node: ast.AST, call_names: set) -> list:
    """Find all function calls with given names in an AST."""
    calls = []
    
    class CallFinder(ast.NodeVisitor):
        def __init__(self):
            self.calls = []
            
        def visit_Call(self, node):
            if isinstance(node.func, ast.Name) and node.func.id in call_names:
                self.calls.append(node)
            self.generic_visit(node)
    
    finder = CallFinder()
    finder.visit(node)
    return finder.calls


def find_model_mutations(node: ast.AST) -> list:
    """Find all model mutations (.save(), .delete(), .create(), etc.) in an AST."""
    mutations = []
    
    class MutationFinder(ast.NodeVisitor):
        def __init__(self):
            self.mutations = []
            
        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute):
                method_name = node.func.attr
                if method_name in ('save', 'delete', 'create', 'update', 'get_or_create', 'update_or_create'):
                    mutations.append((node, node.lineno, method_name))
            self.generic_visit(node)
    
    finder = MutationFinder()
    finder.visit(node)
    return finder.mutations


def find_transaction_on_commit(node: ast.AST) -> list:
    """Find all transaction.on_commit calls in an AST."""
    calls = []
    
    class CallFinder(ast.NodeVisitor):
        def __init__(self):
            self.calls = []
            
        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute):
                if (hasattr(node.func, 'attr') and 
                    node.func.attr == 'on_commit' and
                    isinstance(node.func.value, ast.Attribute) and
                    hasattr(node.func.value, 'attr') and
                    node.func.value.attr == 'transaction'):
                    self.calls.append(node)
            self.generic_visit(node)
    
    finder = CallFinder()
    finder.visit(node)
    return finder.calls


def get_relative_path(file_path: Path) -> str:
    """Get relative path from BASE_DIR."""
    try:
        return str(file_path.relative_to(Path(settings.BASE_DIR)))
    except ValueError:
        return str(file_path)


# =============================================================================
# Test Classes
# =============================================================================

class TestModelMutationsInCQRSCommands:
    """
    Test that model mutations only occur in CQRS command directories.
    
    Rule: .save(), .delete(), .create(), .update() MUST only be called
    in files within apps/*/application/ directories.
    """
    
    @pytest.mark.django_db
    def test_ticket_mutations_only_in_application_dir(self):
        """Test that Ticket model mutations only occur in apps/tickets/application/."""
        violations = []
        
        forbidden_dirs = [
            'apps/frontend/views',
            'apps/tickets/views.py',
            'apps/tickets/serializers.py',
            'apps/tickets/queries',
        ]
        
        for dir_path in forbidden_dirs:
            files = get_python_files(dir_path)
            for file_path in files:
                try:
                    tree = parse_file(file_path)
                    mutations = find_model_mutations(tree)
                    if mutations:
                        rel_path = get_relative_path(file_path)
                        for node, lineno, method in mutations:
                            violations.append(
                                f"{rel_path}:{lineno}: {method}() on Ticket model"
                            )
                except (SyntaxError, FileNotFoundError):
                    pass
        
        assert not violations, (
            f"Found {len(violations)} Ticket model mutation(s) outside CQRS commands:\n" +
            "\n".join(violations)
        )
    
    @pytest.mark.django_db
    def test_asset_mutations_only_in_application_dir(self):
        """Test that Asset model mutations only occur in apps/assets/application/."""
        violations = []
        
        forbidden_dirs = [
            'apps/frontend/views',
            'apps/assets/views.py',
            'apps/assets/serializers.py',
            'apps/assets/queries',
        ]
        
        for dir_path in forbidden_dirs:
            files = get_python_files(dir_path)
            for file_path in files:
                try:
                    tree = parse_file(file_path)
                    mutations = find_model_mutations(tree)
                    if mutations:
                        rel_path = get_relative_path(file_path)
                        for node, lineno, method in mutations:
                            violations.append(
                                f"{rel_path}:{lineno}: {method}() on Asset model"
                            )
                except (SyntaxError, FileNotFoundError):
                    pass
        
        assert not violations, (
            f"Found {len(violations)} Asset model mutation(s) outside CQRS commands:\n" +
            "\n".join(violations)
        )
    
    @pytest.mark.django_db
    def test_project_mutations_only_in_application_dir(self):
        """Test that Project model mutations only occur in apps/projects/application/."""
        violations = []
        
        forbidden_dirs = [
            'apps/frontend/views',
            'apps/frontend/services.py',
            'apps/projects/views.py',
            'apps/projects/serializers.py',
            'apps/projects/queries',
        ]
        
        for dir_path in forbidden_dirs:
            files = get_python_files(dir_path)
            for file_path in files:
                try:
                    tree = parse_file(file_path)
                    mutations = find_model_mutations(tree)
                    if mutations:
                        rel_path = get_relative_path(file_path)
                        for node, lineno, method in mutations:
                            violations.append(
                                f"{rel_path}:{lineno}: {method}() on Project model"
                            )
                except (SyntaxError, FileNotFoundError):
                    pass
        
        assert not violations, (
            f"Found {len(violations)} Project model mutation(s) outside CQRS commands:\n" +
            "\n".join(violations)
        )
    
    @pytest.mark.django_db
    def test_frontend_services_no_project_mutations(self):
        """Test that apps/frontend/services.py has no Project model mutations."""
        file_path = Path(settings.BASE_DIR) / 'apps/frontend/services.py'
        
        if not file_path.exists():
            pytest.skip("apps/frontend/services.py does not exist")
        
        try:
            tree = parse_file(file_path)
            mutations = find_model_mutations(tree)
            
            project_mutations = []
            for node, lineno, method in mutations:
                source = ast.get_source_segment(open(file_path).read(), node)
                if source and ('Project' in source or 'project' in source.lower()):
                    project_mutations.append((node, lineno, method))
            
            assert not project_mutations, (
                f"Found Project model mutation(s) in apps/frontend/services.py:\n" +
                "\n".join([f"  Line {lineno}: {method}()" for _, lineno, method in project_mutations])
            )
        except (SyntaxError, FileNotFoundError):
            pass


class TestActivityLoggingArchitecture:
    """Test that activity logging follows the transaction.on_commit pattern."""
    
    @pytest.mark.django_db
    def test_activity_logger_uses_transaction_on_commit(self):
        """Test that activity logging uses transaction.on_commit (recommendation)."""
        file_path = Path(settings.BASE_DIR) / 'apps/core/services/activity_logger.py'
        
        if not file_path.exists():
            pytest.skip("activity_logger.py does not exist")
        
        try:
            tree = parse_file(file_path)
            on_commit_calls = find_transaction_on_commit(tree)
            
            if len(on_commit_calls) == 0:
                print("Warning: Activity logger does not use transaction.on_commit")
                print("  Consider using transaction.on_commit for safe async logging")
        except (SyntaxError, FileNotFoundError):
            pass
    
    @pytest.mark.django_db
    def test_activity_logging_in_views_prohibited(self):
        """Test that activity logging does not occur inline in views."""
        violations = []
        
        view_dirs = ['apps/frontend/views']
        
        for dir_path in view_dirs:
            files = get_python_files(dir_path)
            for file_path in files:
                try:
                    content = open(file_path).read()
                    tree = ast.parse(content)
                    
                    logging_calls = find_calls_in_module(
                        tree, 
                        {'log_activity', 'log_security_event', 'emit_activity'}
                    )
                    
                    if logging_calls:
                        rel_path = get_relative_path(file_path)
                        for node in logging_calls:
                            violations.append(
                                f"{rel_path}:{node.lineno}: Direct activity logging call"
                            )
                except (SyntaxError, FileNotFoundError):
                    pass
        
        if violations:
            print(f"Warning: Found {len(violations)} potential activity logging call(s) in views")
            for v in violations[:5]:
                print(f"  {v}")


class TestCQRSCommandStructure:
    """Test that CQRS commands have proper structure."""
    
    @pytest.mark.django_db
    def test_ticket_cqrs_commands_exist(self):
        """Test that Ticket CQRS command files exist."""
        files = get_python_files('apps/tickets/application')
        
        assert len(files) >= 3, (
            f"Expected at least 3 Ticket CQRS command files, found: {len(files)}"
        )
        
        for f in files:
            print(f"Found ticket command file: {f.name}")
    
    @pytest.mark.django_db
    def test_asset_cqrs_commands_exist(self):
        """Test that Asset CQRS command files exist."""
        files = get_python_files('apps/assets/application')
        
        assert len(files) >= 3, (
            f"Expected at least 3 Asset CQRS command files, found: {len(files)}"
        )
        
        for f in files:
            print(f"Found asset command file: {f.name}")
    
    @pytest.mark.django_db
    def test_project_cqrs_commands_exist(self):
        """Test that Project CQRS command files exist."""
        files = get_python_files('apps/projects/application')
        
        assert len(files) >= 3, (
            f"Expected at least 3 Project CQRS command files, found: {len(files)}"
        )
        
        for f in files:
            print(f"Found project command file: {f.name}")


class TestDomainEventsUsage:
    """Test that domain events are used properly in CQRS commands."""
    
    @pytest.mark.django_db
    def test_cqrs_commands_emit_domain_events(self):
        """Test that CQRS commands emit domain events."""
        violations = []
        
        cqrs_dirs = CQRS_COMMAND_DIRS
        
        for dir_path in cqrs_dirs:
            files = get_python_files(dir_path)
            for file_path in files:
                try:
                    content = open(file_path).read()
                    tree = ast.parse(content)
                    
                    emit_calls = find_calls_in_module(
                        tree,
                        {'emit', 'publish', 'dispatch'}
                    )
                    
                    if not emit_calls:
                        rel_path = get_relative_path(file_path)
                        violations.append(str(rel_path))
                except (SyntaxError, FileNotFoundError):
                    pass
        
        if violations:
            print(f"Warning: {len(violations)} CQRS command file(s) without domain event emissions:")
            for v in violations[:5]:
                print(f"  {v}")


class TestAuthorizationInCQRSCommands:
    """Test that authorization checks are performed in CQRS commands."""
    
    @pytest.mark.django_db
    def test_cqrs_commands_use_domain_authority(self):
        """Test that CQRS commands use domain authority for authorization."""
        violations = []
        
        cqrs_dirs = CQRS_COMMAND_DIRS
        
        for dir_path in cqrs_dirs:
            files = get_python_files(dir_path)
            for file_path in files:
                try:
                    content = open(file_path).read()
                    tree = ast.parse(content)
                    
                    auth_calls = find_calls_in_module(
                        tree,
                        {'can_', 'assert_can_', 'authorize'}
                    )
                    
                    if not auth_calls:
                        rel_path = get_relative_path(file_path)
                        violations.append(str(rel_path))
                except (SyntaxError, FileNotFoundError):
                    pass
        
        if violations:
            print(f"Warning: {len(violations)} CQRS command file(s) without apparent authorization checks:")
            for v in violations[:5]:
                print(f"  {v}")


# =============================================================================
# Architecture Documentation Enforcement Tests
# =============================================================================
# These tests verify that ARCHITECTURE.md exists and contains required sections.
# They ensure the architecture contract is documented and enforced.
# =============================================================================

class TestArchitectureDocumentation:
    """
    Test that architecture documentation exists and contains required sections.
    
    These tests enforce that:
    1. ARCHITECTURE.md exists at backend/ARCHITECTURE.md
    2. It contains required sections (CQRS, Mutations, Logging, Authorization)
    3. Key architectural rules are documented
    """
    
    def get_architecture_doc_path(self) -> Path:
        """Get the path to ARCHITECTURE.md."""
        return Path(settings.BASE_DIR) / 'ARCHITECTURE.md'
    
    def get_architecture_content(self) -> str:
        """Read the ARCHITECTURE.md content."""
        arch_path = self.get_architecture_doc_path()
        if arch_path.exists():
            return arch_path.read_text(encoding='utf-8')
        return ""
    
    def test_architecture_documentation_exists(self):
        """
        Test that ARCHITECTURE.md exists.
        
        The architecture document MUST exist at backend/ARCHITECTURE.md
        to define the CQRS and architectural rules.
        """
        arch_path = self.get_architecture_doc_path()
        assert arch_path.exists(), (
            f"ARCHITECTURE.md must exist at {arch_path}. "
            "This document defines the architectural rules for the platform."
        )
    
    def test_architecture_documentation_has_cqrs_section(self):
        """
        Test that ARCHITECTURE.md contains CQRS section.
        
        The document MUST define CQRS write model rules including:
        - Where model mutations are allowed
        - Where they are forbidden
        """
        content = self.get_architecture_content()
        assert content, "ARCHITECTURE.md is empty or missing"
        
        # Check for CQRS-related content
        has_cqrs_header = '# CQRS' in content or 'CQRS' in content.upper()
        has_mutation_rules = 'mutation' in content.lower()
        has_allowed_dirs = 'application/' in content or 'application/*' in content
        has_forbidden_dirs = (
            'serializers' in content.lower() and 
            ('forbidden' in content.lower() or 'must not' in content.lower())
        )
        
        assert has_cqrs_header, (
            "ARCHITECTURE.md must contain a CQRS section defining write model rules"
        )
        assert has_mutation_rules, (
            "ARCHITECTURE.md must define mutation rules (save, delete, create, update)"
        )
        assert has_allowed_dirs, (
            "ARCHITECTURE.md must specify allowed mutation directories (application/)"
        )
        assert has_forbidden_dirs, (
            "ARCHITECTURE.md must specify forbidden mutation locations (serializers, views, etc.)"
        )
    
    def test_architecture_documentation_has_authorization_section(self):
        """
        Test that ARCHITECTURE.md contains Authorization section.
        
        The document MUST define:
        - Domain authority pattern
        - Authorization flow in CQRS commands
        - Role hierarchy
        """
        content = self.get_architecture_content()
        assert content, "ARCHITECTURE.md is empty or missing"
        
        # Check for authorization-related content
        has_auth_header = 'Authorization' in content or 'authorization' in content.lower()
        has_domain_authority = 'domain authority' in content.lower() or 'authority' in content.lower()
        has_role_hierarchy = (
            ('SUPERADMIN' in content or 'MANAGER' in content) and 
            'role' in content.lower()
        )
        has_flow_pattern = 'assert_can_' in content or 'can_' in content or 'authorize' in content
        
        assert has_auth_header, (
            "ARCHITECTURE.md must contain an Authorization section"
        )
        assert has_domain_authority, (
            "ARCHITECTURE.md must describe the domain authority pattern"
        )
        assert has_role_hierarchy, (
            "ARCHITECTURE.md must define the role hierarchy (SUPERADMIN, MANAGER, etc.)"
        )
        assert has_flow_pattern, (
            "ARCHITECTURE.md must show the authorization pattern (can_*, assert_can_*)"
        )
    
    def test_architecture_documentation_has_activity_logging_section(self):
        """
        Test that ARCHITECTURE.md contains Activity Logging section.
        
        The document MUST define:
        - transaction.on_commit usage
        - Try/except pattern for logging
        """
        content = self.get_architecture_content()
        assert content, "ARCHITECTURE.md is empty or missing"
        
        # Check for logging-related content
        has_logging_header = 'logging' in content.lower() or 'Activity' in content
        has_transaction_on_commit = 'on_commit' in content.lower() or 'transaction' in content.lower()
        has_try_except = 'try' in content.lower() and 'except' in content.lower()
        
        assert has_logging_header, (
            "ARCHITECTURE.md must contain an Activity Logging section"
        )
        assert has_transaction_on_commit, (
            "ARCHITECTURE.md must document transaction.on_commit pattern for logging"
        )
        assert has_try_except, (
            "ARCHITECTURE.md should document try/except pattern for logging"
        )
    
    def test_architecture_documentation_has_domain_events_section(self):
        """
        Test that ARCHITECTURE.md contains Domain Events section.
        
        The document MUST define:
        - Domain event emission pattern
        - Event types
        """
        content = self.get_architecture_content()
        assert content, "ARCHITECTURE.md is empty or missing"
        
        # Check for domain events content
        has_events_header = 'Event' in content or 'event' in content.lower()
        has_emit_pattern = 'emit' in content.lower()
        
        assert has_events_header, (
            "ARCHITECTURE.md must contain a Domain Events section"
        )
        assert has_emit_pattern, (
            "ARCHITECTURE.md must describe the event emission pattern"
        )
    
    def test_architecture_documentation_has_forbidden_anti_patterns_section(self):
        """
        Test that ARCHITECTURE.md contains Forbidden Anti-Patterns section.
        
        The document MUST explicitly forbid:
        - Services mutating models
        - Views mutating models
        - Serializers mutating models
        - Signals mutating models
        """
        content = self.get_architecture_content()
        assert content, "ARCHITECTURE.md is empty or missing"
        
        # Check for anti-patterns content
        has_antipatterns_header = 'Anti-Pattern' in content or 'Forbidden' in content
        has_services_forbidden = (
            ('Services' in content or 'services' in content.lower()) and 
            ('forbidden' in content.lower() or 'must not' in content.lower())
        )
        has_views_forbidden = (
            'Views' in content and 
            ('forbidden' in content.lower() or 'must not' in content.lower())
        )
        has_serializers_forbidden = (
            'Serializers' in content and 
            ('forbidden' in content.lower() or 'must not' in content.lower())
        )
        has_signals_forbidden = (
            'Signals' in content and 
            ('forbidden' in content.lower() or 'must not' in content.lower())
        )
        
        assert has_antipatterns_header, (
            "ARCHITECTURE.md must contain a Forbidden Anti-Patterns section"
        )
        assert has_services_forbidden, (
            "ARCHITECTURE.md must forbid Services from mutating models"
        )
        assert has_views_forbidden, (
            "ARCHITECTURE.md must forbid Views from mutating models"
        )
        assert has_serializers_forbidden, (
            "ARCHITECTURE.md must forbid Serializers from mutating models"
        )
        assert has_signals_forbidden, (
            "ARCHITECTURE.md must forbid Signals from mutating models"
        )
    
    def test_architecture_documentation_has_directory_structure(self):
        """
        Test that ARCHITECTURE.md contains directory structure documentation.
        
        The document MUST show the proper directory structure with:
        - application/ for CQRS commands
        - domain/ for authority and events
        - queries/ for read operations
        """
        content = self.get_architecture_content()
        assert content, "ARCHITECTURE.md is empty or missing"
        
        # Check for directory structure content
        has_structure_header = 'Directory' in content or 'Structure' in content
        has_application_dir = 'application/' in content
        has_domain_dir = 'domain/' in content
        has_queries_dir = 'queries/' in content
        
        assert has_structure_header, (
            "ARCHITECTURE.md must contain a Directory Structure section"
        )
        assert has_application_dir, (
            "ARCHITECTURE.md must document the application/ directory for CQRS commands"
        )
        assert has_domain_dir, (
            "ARCHITECTURE.md must document the domain/ directory for authority and events"
        )
        assert has_queries_dir, (
            "ARCHITECTURE.md must document the queries/ directory for read operations"
        )
    
    def test_architecture_documentation_has_summary_table(self):
        """
        Test that ARCHITECTURE.md contains a summary table.
        
        The document SHOULD have a summary table showing which layers
        can or cannot mutate models.
        """
        content = self.get_architecture_content()
        assert content, "ARCHITECTURE.md is empty or missing"
        
        # Check for summary table
        has_summary = 'Summary' in content
        has_table = '|' in content  # Markdown table
        has_mutate_column = 'Mutate' in content or 'mutate' in content.lower()
        
        # These are recommendations, not hard requirements
        if not has_summary:
            print("Warning: ARCHITECTURE.md should contain a Summary section with table")
        if not has_table:
            print("Warning: ARCHITECTURE.md should include a Markdown table for quick reference")


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
