# Exception-to-Response Mapper.
# Centralized handler for converting domain exceptions to Django responses.

from typing import Callable, Any, Optional
from functools import wraps
import logging

from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.contrib import messages
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import TemplateView

from .exceptions import (
    DomainException,
    NotFoundError,
    ValidationError,
    PermissionDeniedError,
    ConflictError,
    AuthenticationError,
    BusinessRuleError,
)

logger = logging.getLogger(__name__)


class ExceptionMapper:
    """
    Centralized exception-to-response mapper.
    Converts domain exceptions to appropriate Django HTTP responses.
    """
    
    # Mapping of exception types to HTTP status codes
    STATUS_MAP = {
        NotFoundError: 404,
        ValidationError: 400,
        PermissionDeniedError: 403,
        ConflictError: 409,
        AuthenticationError: 401,
        BusinessRuleError: 422,
        DomainException: 400,
    }
    
    # Default messages for each exception type
    DEFAULT_MESSAGES = {
        NotFoundError: "The requested resource was not found.",
        ValidationError: "The provided data is invalid.",
        PermissionDeniedError: "You do not have permission to perform this action.",
        ConflictError: "There was a conflict with the current state.",
        AuthenticationError: "Authentication is required.",
        BusinessRuleError: "The request could not be processed due to a business rule violation.",
        DomainException: "An error occurred while processing your request.",
    }
    
    @classmethod
    def get_status_code(cls, exception: Exception) -> int:
        """Get HTTP status code for an exception."""
        for exc_type, status in cls.STATUS_MAP.items():
            if isinstance(exception, exc_type):
                return status
        return 500
    
    @classmethod
    def get_default_message(cls, exception: Exception) -> str:
        """Get default error message for an exception type."""
        for exc_type, message in cls.DEFAULT_MESSAGES.items():
            if isinstance(exception, exc_type):
                return message
        return "An unexpected error occurred."
    
    @classmethod
    def to_json_response(
        cls,
        exception: Exception,
        request: Optional[Any] = None,
        status_code: Optional[int] = None
    ) -> JsonResponse:
        """
        Convert a domain exception to a JSON response.
        
        Args:
            exception: The exception to convert
            request: The current request (optional)
            status_code: Override status code (optional)
        
        Returns:
            JsonResponse with error details
        """
        if status_code is None:
            status_code = cls.get_status_code(exception)
        
        # Get error details
        if isinstance(exception, DomainException):
            error_data = exception.to_dict()
        else:
            error_data = {
                'error': {
                    'code': type(exception).__name__.upper(),
                    'message': str(exception) or cls.get_default_message(exception),
                    'details': {}
                }
            }
        
        # Log the error
        if status_code >= 500:
            logger.error(f"Server error: {exception}", exc_info=True)
        elif status_code >= 400:
            logger.warning(f"Client error: {exception}")
        
        return JsonResponse(error_data, status=status_code)
    
    @classmethod
    def to_message(
        cls,
        exception: Exception,
        request: Optional[Any] = None,
        message_level: str = 'error'
    ) -> str:
        """
        Convert a domain exception to a user-friendly message.
        
        Args:
            exception: The exception to convert
            request: The current request (optional)
            message_level: Django messages level ('error', 'warning', 'info', 'success')
        
        Returns:
            Tuple of (message_level, message_string)
        """
        if isinstance(exception, DomainException):
            message = exception.message
        else:
            message = str(exception) or cls.get_default_message(exception)
        
        # Determine message level
        if isinstance(exception, PermissionDeniedError):
            level = 'warning'
        elif isinstance(exception, ValidationError):
            level = 'warning'
        elif isinstance(exception, NotFoundError):
            level = 'info'
        else:
            level = message_level
        
        return level, message
    
    @classmethod
    def add_django_message(
        cls,
        exception: Exception,
        request: Any,
        message_level: str = 'error'
    ) -> None:
        """
        Add a Django message for the exception.
        
        Args:
            exception: The exception that occurred
            request: The current request
            message_level: Django messages level
        """
        level, message = cls.to_message(exception, request, message_level)
        
        # Use getattr to safely get messages framework
        getattr(messages, level)(request, message)
    
    @classmethod
    def handle_exception(
        cls,
        exception: Exception,
        request: Any,
        default_redirect: str = 'frontend:dashboard'
    ) -> HttpResponse:
        """
        Handle a domain exception and return appropriate response.
        Handles both AJAX and regular requests.
        
        Args:
            exception: The exception that occurred
            request: The current request
            default_redirect: Default redirect URL for non-AJAX requests
        
        Returns:
            HttpResponse (JsonResponse or redirect)
        """
        # Check if AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_ajax:
            # Return JSON response for AJAX requests
            return cls.to_json_response(exception, request)
        else:
            # Add Django message and redirect
            cls.add_django_message(exception, request)
            
            # Check if we have a specific redirect URL in the exception details
            if isinstance(exception, DomainException) and exception.details.get('redirect_url'):
                return redirect(exception.details['redirect_url'])
            
            return redirect(default_redirect)


def handle_domain_exceptions(
    redirect_url: str = 'frontend:dashboard',
    with_messages: bool = True,
    ajax_error_key: str = 'error'
):
    """
    Decorator to handle domain exceptions in views.
    
    Args:
        redirect_url: URL to redirect to on error (for non-AJAX requests)
        with_messages: Whether to add Django messages
        ajax_error_key: Key for AJAX error response
    
    Returns:
        Decorated function
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                return view_func(request, *args, **kwargs)
            except DomainException as e:
                # Log the exception
                logger.info(f"Domain exception in view: {e}")
                
                # Handle the exception
                return ExceptionMapper.handle_exception(
                    e, request, redirect_url
                )
            except Exception as e:
                # Log unexpected exceptions
                logger.exception(f"Unexpected error in view: {e}")
                
                # Handle as generic error
                return ExceptionMapper.handle_exception(
                    e, request, redirect_url
                )
        
        return wrapper
    return decorator


class DomainExceptionMixin:
    """
    Mixin to add exception handling capabilities to class-based views.
    
    Usage:
        class MyView(DomainExceptionMixin, TemplateView):
            redirect_url = 'frontend:dashboard'
            
            def get(self, request):
                try:
                    # Your code here
                except DomainException as e:
                    return self.handle_exception(e)
    """
    
    redirect_url: str = 'frontend:dashboard'
    add_messages: bool = True
    
    def handle_exception(
        self,
        exception: Exception,
        request: Optional[Any] = None
    ) -> HttpResponse:
        """
        Handle a domain exception.
        
        Args:
            exception: The exception that occurred
            request: The current request (uses self.request if not provided)
        
        Returns:
            HttpResponse
        """
        if request is None:
            request = getattr(self, 'request', None)
        
        return ExceptionMapper.handle_exception(
            exception, request, self.redirect_url
        )
    
    def add_exception_message(
        self,
        exception: Exception,
        message_level: str = 'error'
    ) -> None:
        """
        Add a Django message for the exception.
        
        Args:
            exception: The exception that occurred
            message_level: Django messages level
        """
        if self.add_messages and hasattr(self, 'request'):
            ExceptionMapper.add_django_message(
                exception, self.request, message_level
            )


class SafeTemplateView(DomainExceptionMixin, TemplateView):
    """
    TemplateView with built-in domain exception handling.
    Catches domain exceptions and converts them to appropriate responses.
    
    Usage:
        class MyView(SafeTemplateView):
            template_name = 'my_template.html'
            redirect_url = 'frontend:dashboard'
            
            def get_context_data(self, **kwargs):
                try:
                    # Your code that might raise exceptions
                    data = super().get_context_data(**kwargs)
                    return data
                except DomainException as e:
                    self.add_exception_message(e)
                    return {}
    """
    
    def dispatch(self, request: Any, *args: Any, **kwargs: Any) -> Any:
        """
        Override dispatch to handle exceptions.
        """
        try:
            return super().dispatch(request, *args, **kwargs)
        except DomainException as e:
            return self.handle_exception(e)
        except Exception as e:
            logger.exception(f"Unexpected error in {self.__class__.__name__}: {e}")
            return self.handle_exception(e)


# Convenience function for manual exception handling
def safe_render(
    template_name: str,
    context: dict,
    request: Any,
    exception: Optional[Exception] = None
) -> str:
    """
    Safely render a template, handling exceptions.
    
    Args:
        template_name: Name of the template to render
        context: Template context dictionary
        request: Current request
        exception: Exception to display (optional)
    
    Returns:
        Rendered HTML string
    """
    if exception:
        # Add exception info to context
        context['exception_message'] = str(exception)
        context['exception_code'] = getattr(exception, 'code', 'ERROR')
    
    return render_to_string(template_name, context, request=request)

