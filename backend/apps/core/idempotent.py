# Idempotent command handling module.
# Provides idempotency support for command services to prevent duplicate execution.
# Uses Django ORM to persist command execution results.
# Supports idempotency_key to ensure safe retries.

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Type, TypeVar
import json
import uuid

from django.db import models
from django.utils import timezone


# =============================================================================
# Command Execution Result Model
# =============================================================================

class CommandExecutionStatus(models.TextChoices):
    """Status choices for command execution."""
    PENDING = 'PENDING', 'Pending'
    RUNNING = 'RUNNING', 'Running'
    COMPLETED = 'COMPLETED', 'Completed'
    FAILED = 'FAILED', 'Failed'


class CommandExecution(models.Model):
    """
    Model to track and persist command execution results.
    
    Used by IdempotentService to ensure commands are executed only once
    for a given idempotency_key. If the same key is reused, the previous
    result is returned instead of re-executing the command.
    
    Attributes:
        idempotency_key: Unique key identifying the command
        service_name: Name of the service that executed the command
        command_type: Type of command (e.g., 'create_project')
        status: Execution status
        input_data: JSON representation of input parameters
        result_data: JSON representation of the result (only on success)
        error_message: Error message (only on failure)
        created_at: When the command was first created
        updated_at: When the status was last updated
        completed_at: When the command finished (success or failure)
    """
    
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique key to prevent duplicate command execution"
    )
    service_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Name of the service (e.g., 'ProjectService')"
    )
    command_type = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Type of command (e.g., 'create_project')"
    )
    status = models.CharField(
        max_length=20,
        choices=CommandExecutionStatus.choices,
        default=CommandExecutionStatus.PENDING,
        db_index=True,
        help_text="Execution status"
    )
    input_data = models.JSONField(
        default=dict,
        help_text="JSON representation of input parameters"
    )
    result_data = models.JSONField(
        null=True,
        blank=True,
        help_text="JSON representation of the result (only on success)"
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message (only on failure)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the command was first created"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When the status was last updated"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the command finished"
    )
    
    class Meta:
        db_table = 'core_command_execution'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['service_name', 'command_type', 'status']),
            models.Index(fields=['idempotency_key', 'status']),
        ]
    
    def __str__(self) -> str:
        return f"[{self.service_name}.{self.command_type}] {self.idempotency_key} ({self.status})"
    
    def mark_running(self) -> None:
        """Mark execution as running."""
        self.status = CommandExecutionStatus.RUNNING
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_completed(self, result_data: Dict) -> None:
        """Mark execution as completed with result."""
        self.status = CommandExecutionStatus.COMPLETED
        self.result_data = result_data
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'result_data', 'completed_at', 'updated_at'])
    
    def mark_failed(self, error_message: str) -> None:
        """Mark execution as failed with error."""
        self.status = CommandExecutionStatus.FAILED
        self.error_message = error_message
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'error_message', 'completed_at', 'updated_at'])
    
    def to_result(self) -> Dict:
        """Convert to result dictionary for returning to caller."""
        return {
            'idempotency_key': self.idempotency_key,
            'status': self.status,
            'result': self.result_data,
            'cached': self.status == CommandExecutionStatus.COMPLETED,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    @classmethod
    def get_or_create_execution(
        cls,
        idempotency_key: str,
        service_name: str,
        command_type: str,
        input_data: Dict
    ) -> tuple['CommandExecution', bool]:
        """
        Get existing execution or create new one.
        
        Args:
            idempotency_key: Unique key for the command
            service_name: Name of the service
            command_type: Type of command
            input_data: Input parameters
            
        Returns:
            Tuple of (execution, is_new) where is_new is True if created
        """
        execution, is_new = cls.objects.get_or_create(
            idempotency_key=idempotency_key,
            defaults={
                'service_name': service_name,
                'command_type': command_type,
                'input_data': input_data,
                'status': CommandExecutionStatus.PENDING,
            }
        )
        return execution, is_new


# =============================================================================
# Command Result DataClass
# =============================================================================

@dataclass
class CommandResult:
    """
    Result of a command execution.
    
    Attributes:
        success: Whether the command succeeded
        data: Result data (for successful commands)
        error: Error message (for failed commands)
        cached: Whether this result was from cache (previous execution)
    """
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    cached: bool = False
    
    @classmethod
    def success_result(cls, data: Dict, cached: bool = False) -> 'CommandResult':
        """Create a successful result."""
        return cls(success=True, data=data, cached=cached)
    
    @classmethod
    def error_result(cls, error: str) -> 'CommandResult':
        """Create an error result."""
        return cls(success=False, error=error)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'cached': self.cached,
        }


# =============================================================================
# Idempotent Service Mixin
# =============================================================================

T = TypeVar('T', bound='IdempotentService')


class IdempotentService(ABC):
    """
    Mixin that provides idempotent command execution for services.
    
    Ensures commands are executed only once for a given idempotency_key.
    If the same key is reused, returns the previous result instead of
    re-executing the command.
    
    Usage:
        class ProjectService(IdempotentService, TransactionEventPublisher):
            SERVICE_NAME = 'ProjectService'
            
            @classmethod
            def create_project(
                cls,
                idempotency_key: str,
                request,
                name: str,
                ...
            ) -> CommandResult:
                return cls._execute_idempotent(
                    idempotency_key=idempotency_key,
                    command_type='create_project',
                    input_data={'name': name, ...},
                    executor=lambda: cls._do_create_project(request, name, ...),
                )
            
            @classmethod
            def _do_create_project(cls, request, name, ...) -> Dict:
                # Actual implementation
                ...
                return {'id': project.id, 'name': project.name}
    """
    
    # Override in subclass
    SERVICE_NAME: str = 'IdempotentService'
    
    @classmethod
    def _execute_idempotent(
        cls,
        idempotency_key: str,
        command_type: str,
        input_data: Dict,
        executor: callable
    ) -> CommandResult:
        """
        Execute a command with idempotency guarantee.
        
        If the same idempotency_key has been used before, returns the previous
        result instead of re-executing the command.
        
        Args:
            idempotency_key: Unique key to identify this command
            command_type: Type of command (e.g., 'create_project')
            input_data: Input parameters for the command
            executor: Callable that executes the command and returns result dict
            
        Returns:
            CommandResult with success/data or error
        """
        # Get or create execution record
        execution, is_new = CommandExecution.get_or_create_execution(
            idempotency_key=idempotency_key,
            service_name=cls.SERVICE_NAME,
            command_type=command_type,
            input_data=input_data,
        )
        
        # If execution already completed, return cached result
        if execution.status == CommandExecutionStatus.COMPLETED:
            return CommandResult.success_result(
                data=execution.result_data,
                cached=True
            )
        
        # If execution failed, return cached error
        if execution.status == CommandExecutionStatus.FAILED:
            return CommandResult.error_result(error=execution.error_message)
        
        # If execution is already running (concurrent request), wait and check
        if execution.status == CommandExecutionStatus.RUNNING:
            # Wait briefly for concurrent execution to complete
            # Use exponential backoff with max retries
            from django.db import transaction
            
            max_retries = 10
            retry_delay = 0.01  # 10ms base delay
            
            for attempt in range(max_retries):
                transaction.set_rollback(False)  # Don't affect main transaction
                execution.refresh_from_db()
                
                if execution.status == CommandExecutionStatus.COMPLETED:
                    return CommandResult.success_result(
                        data=execution.result_data,
                        cached=True
                    )
                if execution.status == CommandExecutionStatus.FAILED:
                    return CommandResult.error_result(error=execution.error_message)
                
                # Wait with exponential backoff
                import time
                time.sleep(retry_delay * (2 ** attempt))
            
            # If still running after retries, treat as conflict
            return CommandResult.error_result(
                error="Command execution is still in progress"
            )
        
        # New execution - mark as running and execute
        try:
            execution.mark_running()
            
            # Execute the command
            result_data = executor()
            
            # Mark as completed
            execution.mark_completed(result_data=result_data)
            
            return CommandResult.success_result(data=result_data, cached=False)
            
        except Exception as e:
            # Mark as failed
            import traceback
            error_msg = f"{type(e).__name__}: {str(e)}"
            execution.mark_failed(error_message=error_msg)
            
            return CommandResult.error_result(error=error_msg)
    
    @classmethod
    def _generate_idempotency_key(cls, *args, **kwargs) -> str:
        """
        Generate a deterministic idempotency key from arguments.
        
        Override this to provide custom key generation logic.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            UUID string as idempotency key
        """
        # Generate a unique key based on arguments
        key_data = {
            'service': cls.SERVICE_NAME,
            'args': [str(arg) for arg in args],
            'kwargs': {k: str(v) for k, v in sorted(kwargs.items())},
            'timestamp': datetime.utcnow().strftime('%Y%m%d'),
        }
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, json.dumps(key_data, sort_keys=True)))
    
    @classmethod
    def execute_idempotent(
        cls,
        idempotency_key: str,
        command_type: str,
        input_data: Dict,
        executor: callable
    ) -> CommandResult:
        """
        Public method for idempotent execution.
        
        This is an alias for _execute_idempotent for use in services.
        
        Args:
            idempotency_key: Unique key for the command
            command_type: Type of command
            input_data: Input parameters
            executor: Callable that executes the command
            
        Returns:
            CommandResult
        """
        return cls._execute_idempotent(
            idempotency_key=idempotency_key,
            command_type=command_type,
            input_data=input_data,
            executor=executor,
        )


# =============================================================================
# Utility Functions
# =============================================================================

def execute_idempotent(
    service_name: str,
    command_type: str,
    idempotency_key: str,
    input_data: Dict,
    executor: callable
) -> CommandResult:
    """
    Standalone function for idempotent command execution.
    
    Use this when services don't use the IdempotentService mixin.
    
    Args:
        service_name: Name of the service
        command_type: Type of command
        idempotency_key: Unique key for the command
        input_data: Input parameters
        executor: Callable that executes the command
        
    Returns:
        CommandResult
    """
    # Get or create execution record
    execution, is_new = CommandExecution.get_or_create_execution(
        idempotency_key=idempotency_key,
        service_name=service_name,
        command_type=command_type,
        input_data=input_data,
    )
    
    # Return cached result if exists
    if execution.status == CommandExecutionStatus.COMPLETED:
        return CommandResult.success_result(data=execution.result_data, cached=True)
    
    if execution.status == CommandExecutionStatus.FAILED:
        return CommandResult.error_result(error=execution.error_message)
    
    # Execute the command
    try:
        execution.mark_running()
        result_data = executor()
        execution.mark_completed(result_data=result_data)
        return CommandResult.success_result(data=result_data, cached=False)
    except Exception as e:
        import traceback
        error_msg = f"{type(e).__name__}: {str(e)}"
        execution.mark_failed(error_message=error_msg)
        return CommandResult.error_result(error=error_msg)


def create_idempotency_key(*args, **kwargs) -> str:
    """
    Generate a deterministic idempotency key.
    
    Args:
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key
        
    Returns:
        UUID string as idempotency key
    """
    key_data = {
        'args': [str(arg) for arg in args],
        'kwargs': {k: str(v) for k, v in sorted(kwargs.items())},
    }
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, json.dumps(key_data, sort_keys=True)))

