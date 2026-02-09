"""
Involved Usernames Normalization for Activity Logs

This module provides:
1. Helper function to extract usernames from extra_data for backfilling
2. Consistent username extraction for new activity logs
3. Search functionality using involved_usernames field

Usage:
    # Extract usernames from existing extra_data
    from apps.logs.services.involved_usernames_fix import extract_usernames_from_extra_data
    usernames = extract_usernames_from_extra_data(extra_data_dict)

    # Build involved_usernames for new logs
    from apps.logs.services.involved_usernames_fix import build_involved_usernames
    involved = build_involved_usernames(
        actor_username="admin",
        assignee_username="technician",
        previous_assignee_username="old_tech"
    )
    # Result: ["admin", "technician", "old_tech"]
"""

from typing import Optional, List, Set, Dict, Any


# =============================================================================
# Username Extraction from extra_data (for backfilling)
# =============================================================================

def extract_usernames_from_extra_data(extra_data: Dict[str, Any]) -> Set[str]:
    """
    Extract all usernames from an extra_data dictionary.
    
    This function searches through all known keys that might contain usernames
    and returns a set of unique usernames found.
    
    Args:
        extra_data: Dictionary containing activity metadata
        
    Returns:
        Set of unique usernames found in the extra_data
        
    Examples:
        >>> extra_data = {"assignee_username": "john", "actor_username": "admin"}
        >>> extract_usernames_from_extra_data(extra_data)
        {'john', 'admin'}
    """
    if not extra_data:
        return set()
    
    usernames = set()
    
    # Direct username fields
    username_fields = [
        'username',
        'actor_username',
        'assignee_username',
        'previous_assignee_username',
        'unassigned_username',
        'affected_username',
        'target_username',
        'created_by_username',
        'updated_by_username',
        'deleted_by_username',
        'assigned_by_username',
        'requester_username',
        'owner_username',
        'member_username',
        'removed_member_username',
        'added_member_username',
    ]
    
    for field in username_fields:
        value = extra_data.get(field)
        if value and isinstance(value, str):
            usernames.add(value.strip().lower())
    
    # Nested object fields (e.g., assignee.username, previous_assignee.username)
    nested_user_fields = [
        ('assignee', 'username'),
        ('previous_assignee', 'username'),
        ('actor', 'username'),
        ('user', 'username'),
        ('target_user', 'username'),
        ('affected_user', 'username'),
        ('created_by', 'username'),
        ('updated_by', 'username'),
        ('deleted_by', 'username'),
        ('assigned_by', 'username'),
        ('requester', 'username'),
        ('owner', 'username'),
        ('added_by', 'username'),
        ('removed_by', 'username'),
    ]
    
    for parent_field, child_field in nested_user_fields:
        parent = extra_data.get(parent_field)
        if parent and isinstance(parent, dict):
            value = parent.get(child_field)
            if value and isinstance(value, str):
                usernames.add(value.strip().lower())
    
    # List fields (e.g., team_members_usernames, assigned_to_usernames)
    list_fields = [
        'team_members_usernames',
        'assigned_to_usernames',
        'cc_usernames',
        'notify_usernames',
        'involved_usernames',  # Already normalized (may exist)
        'member_usernames',
    ]
    
    for field in list_fields:
        value = extra_data.get(field)
        if value and isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    usernames.add(item.strip().lower())
    
    return usernames


def extract_usernames_from_extra_data_json(extra_data_json: str) -> Set[str]:
    """
    Extract usernames from a JSON string extra_data field.
    
    Args:
        extra_data_json: JSON string representation of extra_data
        
    Returns:
        Set of unique usernames found
    """
    import json
    
    if not extra_data_json:
        return set()
    
    try:
        extra_data = json.loads(extra_data_json)
        return extract_usernames_from_extra_data(extra_data)
    except (json.JSONDecodeError, TypeError):
        return set()


# =============================================================================
# Build involved_usernames for new logs
# =============================================================================

def build_involved_usernames(
    actor_username: Optional[str] = None,
    assignee_username: Optional[str] = None,
    previous_assignee_username: Optional[str] = None,
    unassigned_username: Optional[str] = None,
    affected_username: Optional[str] = None,
    target_username: Optional[str] = None,
    requester_username: Optional[str] = None,
    owner_username: Optional[str] = None,
    extra_usernames: Optional[List[str]] = None,
) -> List[str]:
    """
    Build a normalized list of involved usernames for a new activity log.
    
    This function ensures all usernames are:
    1. Lowercase (for consistent searching)
    2. Stripped of whitespace
    3. Deduplicated
    4. Sorted alphabetically
    
    Args:
        actor_username: User who performed the action
        assignee_username: User who was assigned
        previous_assignee_username: Previous assignee (for reassignment)
        unassigned_username: User who was unassigned
        affected_username: User affected by the action
        target_username: Target user of the action
        requester_username: User who requested the action
        owner_username: Owner of the resource
        extra_usernames: Additional usernames to include
        
    Returns:
        List of normalized usernames, sorted alphabetically
        
    Examples:
        >>> build_involved_usernames(
        ...     actor_username="Admin",
        ...     assignee_username="Technician"
        ... )
        ['admin', 'technician']
    """
    usernames = set()
    
    # Add all provided usernames (lowercase, stripped)
    username_params = [
        actor_username,
        assignee_username,
        previous_assignee_username,
        unassigned_username,
        affected_username,
        target_username,
        requester_username,
        owner_username,
    ]
    
    for username in username_params:
        if username and isinstance(username, str):
            usernames.add(username.strip().lower())
    
    # Add extra usernames
    if extra_usernames:
        for username in extra_usernames:
            if username and isinstance(username, str):
                usernames.add(username.strip().lower())
    
    # Return sorted list
    return sorted(list(usernames))


def add_involved_usernames_to_extra_data(
    extra_data: Dict[str, Any],
    actor_username: Optional[str] = None,
    assignee_username: Optional[str] = None,
    previous_assignee_username: Optional[str] = None,
    unassigned_username: Optional[str] = None,
    affected_username: Optional[str] = None,
    target_username: Optional[str] = None,
    requester_username: Optional[str] = None,
    owner_username: Optional[str] = None,
    extra_usernames: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Add normalized involved_usernames to extra_data dictionary.
    
    This function:
    1. Extracts existing usernames from extra_data
    2. Adds new usernames from parameters
    3. Normalizes and deduplicates
    4. Stores in extra_data['involved_usernames']
    
    Args:
        extra_data: Existing extra_data dictionary
        (other parameters same as build_involved_usernames)
        
    Returns:
        Updated extra_data dictionary with 'involved_usernames' key
        
    Examples:
        >>> extra = {"assignee_username": "john"}
        >>> add_involved_usernames_to_extra_data(
        ...     extra,
        ...     actor_username="admin",
        ...     assignee_username="john"
        ... )
        {'assignee_username': 'john', 'involved_usernames': ['admin', 'john']}
    """
    # Make a copy to avoid mutating original
    result = dict(extra_data) if extra_data else {}
    
    # Extract existing usernames from extra_data
    existing_usernames = extract_usernames_from_extra_data(result)
    
    # Build new usernames
    new_usernames = build_involved_usernames(
        actor_username=actor_username,
        assignee_username=assignee_username,
        previous_assignee_username=previous_assignee_username,
        unassigned_username=unassigned_username,
        affected_username=affected_username,
        target_username=target_username,
        requester_username=requester_username,
        owner_username=owner_username,
        extra_usernames=extra_usernames,
    )
    
    # Combine and deduplicate
    all_usernames = set(existing_usernames) | set(new_usernames)
    
    # Store normalized list
    result['involved_usernames'] = sorted(list(all_usernames))
    
    return result


# =============================================================================
# Search helpers
# =============================================================================

def build_username_search_filter(username: str) -> str:
    """
    Build a search pattern for username matching.
    
    Args:
        username: Username to search for
        
    Returns:
        Lowercase, stripped username for matching
    """
    return username.strip().lower()


def build_involved_usernames_q_filter(username: str):
    """
    Build a Django Q filter for searching by username in involved_usernames.
    
    This is the PRIMARY search method for username filtering.
    
    Args:
        username: Username to search for
        
    Returns:
        Q object for filtering ActivityLog by involved_usernames
        
    Examples:
        >>> from django.db.models import Q
        >>> from apps.logs.services.involved_usernames_fix import build_involved_usernames_q_filter
        >>> qs.filter(build_involved_usernames_q_filter('john'))
        # SELECT * FROM activity_logs WHERE 'john' = ANY(involved_usernames)
    """
    from django.db.models import Q
    
    search_term = build_username_search_filter(username)
    
    # Primary search: involved_usernames field
    # Secondary searches: legacy fields (for back-compatibility during migration)
    return Q(
        Q(extra_data__contains=search_term) |  # PostgreSQL array contains
        Q(extra_data__icontains=search_term)   # JSON contains (fallback)
    )


# =============================================================================
# Backfill utilities
# =============================================================================

def backfill_involved_usernames(
    batch_size: int = 1000,
    dry_run: bool = True,
) -> dict:
    """
    Backfill existing ActivityLog entries with involved_usernames.
    
    This function:
    1. Iterates through all ActivityLog entries
    2. Extracts usernames from extra_data
    3. Populates involved_usernames field
    4. Saves the updated log entry
    
    Args:
        batch_size: Number of entries to process at once
        dry_run: If True, only count what would be updated
        
    Returns:
        Dictionary with statistics:
        {
            'total_processed': int,
            'updated': int,
            'already_had_field': int,
            'errors': int,
        }
    """
    import json
    from apps.logs.models import ActivityLog
    
    stats = {
        'total_processed': 0,
        'updated': 0,
        'already_had_field': 0,
        'errors': 0,
    }
    
    # Get all log IDs for processing
    log_ids = ActivityLog.objects.values_list('id', flat=True).order_by('id')
    total_count = log_ids.count()
    
    print(f"[BACKFILL] Starting backfill for {total_count} ActivityLog entries")
    print(f"[BACKFILL] Dry run: {dry_run}")
    
    for i in range(0, total_count, batch_size):
        batch_ids = list(log_ids[i:i + batch_size])
        
        for log_id in batch_ids:
            try:
                log = ActivityLog.objects.get(id=log_id)
                stats['total_processed'] += 1
                
                # Get current extra_data
                extra_data = log.extra_data or {}
                
                # Check if involved_usernames already exists
                if 'involved_usernames' in extra_data:
                    stats['already_had_field'] += 1
                    continue
                
                # Extract usernames from extra_data
                existing_usernames = extract_usernames_from_extra_data(extra_data)
                
                # Add actor username if exists
                if log.user and log.user.username:
                    existing_usernames.add(log.user.username.strip().lower())
                
                # Build new extra_data with involved_usernames
                if existing_usernames:
                    extra_data['involved_usernames'] = sorted(list(existing_usernames))
                    
                    if not dry_run:
                        log.extra_data = extra_data
                        log.save(update_fields=['extra_data'])
                    
                    stats['updated'] += 1
                    print(f"[BACKFILL] Updated log {log_id}: {extra_data.get('involved_usernames')}")
                else:
                    stats['already_had_field'] += 1
                    
            except Exception as e:
                stats['errors'] += 1
                print(f"[BACKFILL] Error processing log {log_id}: {e}")
        
        # Progress update
        progress = min(i + batch_size, total_count)
        print(f"[BACKFILL] Progress: {progress}/{total_count} ({progress * 100 // total_count}%)")
    
    print(f"[BACKFILL] Complete: {stats}")
    return stats


def backfill_involved_usernames_sql(batch_size: int = 1000, dry_run: bool = True) -> str:
    """
    Generate SQL for backfilling involved_usernames.
    
    This is an alternative to the Python backfill for databases that
    support JSON operations efficiently.
    
    Args:
        batch_size: Not used, included for API consistency
        dry_run: If True, shows SQL without executing
        
    Returns:
        SQL statement string
        
    Note:
        This SQL uses PostgreSQL syntax. Adjust for other databases.
    """
    sql = """
-- Backfill involved_usernames for existing ActivityLog entries
-- This SQL extracts usernames from existing extra_data fields
-- and populates the involved_usernames array

UPDATE activity_logs
SET extra_data = (
    SELECT jsonb_set(
        COALESCE(extra_data, '{}'::jsonb),
        '{involved_usernames}',
        (
            SELECT jsonb_agg(DISTINCT lower(username))
            FROM (
                SELECT DISTINCT trim(lower(value::text)) as username
                FROM jsonb_each_text(COALESCE(activity_logs.extra_data, '{}'::jsonb))
                WHERE key IN (
                    'username', 'actor_username', 'assignee_username',
                    'previous_assignee_username', 'unassigned_username',
                    'affected_username', 'target_username', 'requester_username',
                    'owner_username', 'created_by_username', 'updated_by_username'
                )
                UNION
                SELECT trim(lower(value->>'username'))
                FROM jsonb_each(activity_logs.extra_data)
                WHERE key IN ('assignee', 'previous_assignee', 'actor', 'user')
                AND jsonb_typeof(value) = 'object'
                AND value ? 'username'
            ) AS usernames
        )
    )
)
WHERE 
    extra_data IS NOT NULL
    AND (extra_data->'involved_usernames') IS NULL
    AND (
        extra_data->'assignee_username' IS NOT NULL OR
        extra_data->'username' IS NOT NULL OR
        extra_data->'actor_username' IS NOT NULL OR
        extra_data->'previous_assignee_username' IS NOT NULL OR
        extra_data->'unassigned_username' IS NOT NULL
    );
"""
    
    if dry_run:
        print("[BACKFILL-SQL] Generated SQL (dry run - not executed):")
        print(sql)
        return sql
    else:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows_updated = cursor.rowcount
        print(f"[BACKFILL-SQL] Updated {rows_updated} rows")
        return sql


# =============================================================================
# Validation
# =============================================================================

def validate_involved_usernames(
    sample_size: int = 100,
) -> dict:
    """
    Validate that involved_usernames is properly populated.
    
    Args:
        sample_size: Number of entries to sample
        
    Returns:
        Dictionary with validation results:
        {
            'total_checked': int,
            'valid': int,
            'missing_involved_usernames': int,
            'empty_involved_usernames': int,
            'sample_invalid': list,
        }
    """
    from apps.logs.models import ActivityLog
    
    stats = {
        'total_checked': 0,
        'valid': 0,
        'missing_involved_usernames': 0,
        'empty_involved_usernames': 0,
        'sample_invalid': [],
    }
    
    # Sample logs
    logs = ActivityLog.objects.all()[:sample_size]
    
    for log in logs:
        stats['total_checked'] += 1
        extra_data = log.extra_data or {}
        
        # Check if involved_usernames exists
        if 'involved_usernames' not in extra_data:
            stats['missing_involved_usernames'] += 1
            if len(stats['sample_invalid']) < 5:
                stats['sample_invalid'].append({
                    'log_id': log.id,
                    'action': log.action,
                    'reason': 'missing_involved_usernames',
                })
            continue
        
        # Check if involved_usernames is non-empty list
        involved = extra_data.get('involved_usernames')
        if not involved or not isinstance(involved, list) or len(involved) == 0:
            stats['empty_involved_usernames'] += 1
            if len(stats['sample_invalid']) < 5:
                stats['sample_invalid'].append({
                    'log_id': log.id,
                    'action': log.action,
                    'reason': 'empty_involved_usernames',
                })
            continue
        
        # Validate that actor username is in involved_usernames
        if log.user and log.user.username:
            actor_username = log.user.username.strip().lower()
            if actor_username not in involved:
                if len(stats['sample_invalid']) < 5:
                    stats['sample_invalid'].append({
                        'log_id': log.id,
                        'action': log.action,
                        'reason': 'actor_not_in_involved_usernames',
                        'actor': log.user.username,
                        'involved': involved,
                    })
                continue
        
        stats['valid'] += 1
    
    return stats


# =============================================================================
# Management Command Wrapper
# =============================================================================

def create_backfill_management_command():
    """
    Create a Django management command for backfilling.
    
    This generates the content for a management command file.
    """
    command_content = '''"""
Management command to backfill involved_usernames for ActivityLog.

Usage:
    python manage.py backfill_involved_usernames --batch-size=500
    python manage.py backfill_involved_usernames --dry-run
    python manage.py backfill_involved_usernames --validate
"""
import json
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.logs.models import ActivityLog
from apps.logs.services.involved_usernames_fix import (
    extract_usernames_from_extra_data,
    backfill_involved_usernames,
    validate_involved_usernames,
)


class Command(BaseCommand):
    help = 'Backfill involved_usernames for existing ActivityLog entries'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Number of entries to process at once',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--validate',
            action='store_true',
            help='Validate existing involved_usernames instead of backfilling',
        )
    
    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        validate_only = options['validate']
        
        if validate_only:
            self.stdout.write('Validating involved_usernames...')
            stats = validate_involved_usernames(sample_size=1000)
            self.stdout.write(f"Validation results: {json.dumps(stats, indent=2)}")
            
            if stats['missing_involved_usernames'] > 0:
                self.stdout.warning(
                    f"Found {stats['missing_involved_usernames']} logs without involved_usernames"
                )
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE'))
        
        stats = backfill_involved_usernames(
            batch_size=batch_size,
            dry_run=dry_run,
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Backfill complete: {json.dumps(stats, indent=2)}"
            )
        )
'''
    
    return command_content
