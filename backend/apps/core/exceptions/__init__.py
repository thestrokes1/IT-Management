# Domain exceptions package.
# Contains domain-specific exception classes for the IT Management Platform.
# These exceptions are used throughout the application layer.

from typing import Optional, Any


class DomainException(Exception):
    """
    Base class for all domain exceptions.
    All domain exceptions inherit from this class.
    """
    
    def __init__(
        self,
        message: str,
        code: str = "DOMAIN_ERROR",
        details: Optional[dict] = None,
        *args,
        **kwargs
    ):
        super().__init__(message, *args, **kwargs)
        self.message = message
        self.code = code
        self.details = details or {}
    
    def __str__(self):
        return f"[{self.code}] {self.message}"
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for JSON serialization."""
        return {
            'error': {
                'code': self.code,
                'message': self.message,
                'details': self.details
            }
        }


class NotFoundError(DomainException):
    """
    Raised when a requested resource is not found.
    Maps to HTTP 404.
    """
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[Any] = None,
        message: Optional[str] = None,
        *args,
        **kwargs
    ):
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        if message is None:
            if resource_id is not None:
                message = f"{resource_type} with id '{resource_id}' not found"
            else:
                message = f"{resource_type} not found"
        
        super().__init__(
            message=message,
            code="NOT_FOUND",
            details={
                'resource_type': resource_type,
                'resource_id': str(resource_id) if resource_id else None
            },
            *args,
            **kwargs
        )


class ValidationError(DomainException):
    """
    Raised when input validation fails.
    Maps to HTTP 400.
    """
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        errors: Optional[dict] = None,
        *args,
        **kwargs
    ):
        details = kwargs.get('details', {}) or {}
        if field:
            details['field'] = field
        if errors:
            details['validation_errors'] = errors
        
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            *args,
            **kwargs
        )
        self.field = field
        self.errors = errors or {}


class PermissionDeniedError(DomainException):
    """
    Raised when user lacks permission to perform an action.
    Maps to HTTP 403.
    """
    
    def __init__(
        self,
        message: Optional[str] = None,
        required_roles: Optional[list] = None,
        details: Optional[dict] = None,
        *args,
        **kwargs
    ):
        # Start with provided details or empty dict
        final_details = details.copy() if details else {}
        
        # Add required_roles if provided
        if required_roles:
            final_details['required_roles'] = required_roles
        
        super().__init__(
            message=message or "You do not have permission to perform this action",
            code="PERMISSION_DENIED",
            details=final_details,
            *args,
            **kwargs
        )
        self.required_roles = required_roles


class ConflictError(DomainException):
    """
    Raised when there's a conflict with the current state of the resource.
    Maps to HTTP 409.
    """
    
    def __init__(
        self,
        message: str,
        conflict_type: Optional[str] = None,
        *args,
        **kwargs
    ):
        details = kwargs.get('details', {}) or {}
        if conflict_type:
            details['conflict_type'] = conflict_type
        
        super().__init__(
            message=message,
            code="CONFLICT",
            details=details,
            *args,
            **kwargs
        )
        self.conflict_type = conflict_type


class AuthenticationError(DomainException):
    """
    Raised when authentication fails or is required.
    Maps to HTTP 401.
    """
    
    def __init__(
        self,
        message: Optional[str] = None,
        *args,
        **kwargs
    ):
        super().__init__(
            message=message or "Authentication required",
            code="AUTHENTICATION_ERROR",
            *args,
            **kwargs
        )


class BusinessRuleError(DomainException):
    """
    Raised when a business rule is violated.
    Maps to HTTP 422 (Unprocessable Entity).
    """
    
    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        *args,
        **kwargs
    ):
        details = kwargs.get('details', {}) or {}
        if rule_name:
            details['rule_name'] = rule_name
        
        super().__init__(
            message=message,
            code="BUSINESS_RULE_VIOLATION",
            details=details,
            *args,
            **kwargs
        )
        self.rule_name = rule_name

