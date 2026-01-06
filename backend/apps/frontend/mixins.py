"""
Custom mixins for frontend views.
Provides reusable permission handling and common functionality.
"""

from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse


class AdminRequiredMixin:
    """
    Mixin that requires the user to have admin role.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Authentication required.'}, status=401)
            return redirect('frontend:login')
        
        if not hasattr(request.user, 'role') or request.user.role not in ['ADMIN', 'SUPERADMIN', 'IT_ADMIN']:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Permission denied.'}, status=403)
            messages.error(request, 'You do not have permission to perform this action.')
            return redirect('frontend:dashboard')
        
        return super().dispatch(request, *args, **kwargs)


class CanManageUsersMixin:
    """
    Mixin that requires the user to have user management permissions.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Authentication required.'}, status=401)
            return redirect('frontend:login')
        
        if not request.user.can_manage_users:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Permission denied.'}, status=403)
            messages.error(request, 'You do not have permission to manage users.')
            return redirect('frontend:dashboard')
        
        return super().dispatch(request, *args, **kwargs)


class CanManageTicketsMixin:
    """
    Mixin that requires the user to have ticket management permissions.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Authentication required.'}, status=401)
            return redirect('frontend:login')
        
        if not request.user.can_manage_tickets:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Permission denied.'}, status=403)
            messages.error(request, 'You do not have permission to manage tickets.')
            return redirect('frontend:tickets')
        
        return super().dispatch(request, *args, **kwargs)


class CanManageProjectsMixin:
    """
    Mixin that requires the user to have project management permissions.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Authentication required.'}, status=401)
            return redirect('frontend:login')
        
        if not request.user.can_manage_projects:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Permission denied.'}, status=403)
            messages.error(request, 'You do not have permission to manage projects.')
            return redirect('frontend:projects')
        
        return super().dispatch(request, *args, **kwargs)


class CanManageAssetsMixin:
    """
    Mixin that requires the user to have asset management permissions.
    """
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Authentication required.'}, status=401)
            return redirect('frontend:login')
        
        if not request.user.can_manage_assets:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Permission denied.'}, status=403)
            messages.error(request, 'You do not have permission to manage assets.')
            return redirect('frontend:assets')
        
        return super().dispatch(request, *args, **kwargs)


class BaseListView(LoginRequiredMixin):
    """
    Base mixin for list views with pagination and ordering.
    """
    template_name = None
    model = None
    paginate_by = 50
    ordering = '-created_at'
    
    def get_queryset(self):
        if self.model is None:
            return []
        return self.model.objects.select_related().order_by(self.ordering)[:self.paginate_by]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[self.context_object_name] = self.get_queryset()
        return context


class BaseCreateView(LoginRequiredMixin):
    """
    Base mixin for create views with form handling.
    """
    template_name = None
    model = None
    success_url = None
    context_object_name = None
    
    def get(self, request, *args, **kwargs):
        # Override to add any pre-GET logic (like permission checks)
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """Handle form submission."""
        return self._process_form(request)
    
    def _process_form(self, request):
        """Process form data and create object."""
        raise NotImplementedError("Subclasses must implement _process_form")
    
    def get_success_url(self):
        return self.success_url


class BaseEditView(LoginRequiredMixin):
    """
    Base mixin for edit views with common patterns.
    """
    template_name = None
    model = None
    pk_url_kwarg = 'pk'
    success_url = None
    
    def get_object(self, queryset=None):
        """Get the object using get_object_or_404."""
        pk = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(self.model, pk=pk)
    
    def get(self, request, *args, **kwargs):
        context = self.get_context_data()
        context[self.context_object_name] = self.get_object()
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        """Handle form submission."""
        return self._process_form(request)
    
    def _process_form(self, request):
        """Process form data and update object."""
        raise NotImplementedError("Subclasses must implement _process_form")
    
    def get_success_url(self):
        return self.success_url


class BaseDeleteView(LoginRequiredMixin):
    """
    Base mixin for delete views.
    """
    model = None
    pk_url_kwarg = 'pk'
    success_url = None
    
    def get_object(self, queryset=None):
        """Get the object using get_object_or_404."""
        pk = self.kwargs.get(self.pk_url_kwarg)
        return get_object_or_404(self.model, pk=pk)
    
    def delete(self, request, *args, **kwargs):
        """Delete the object and return success response."""
        obj = self.get_object()
        obj.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Deleted successfully.'})
        messages.success(request, 'Deleted successfully.')
        return redirect(self.get_success_url())
    
    def get_success_url(self):
        return self.success_url


class Handle403Mixin:
    """
    Mixin to handle 403 Forbidden responses consistently.
    """
    
    def handle_permission_denied(self, request, message=None):
        """Handle permission denied situation."""
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': message or 'Permission denied.'}, status=403)
        messages.error(request, message or 'You do not have permission to perform this action.')
        return redirect(self.get_redirect_url())
    
    def get_redirect_url(self):
        """Get the redirect URL for permission denied."""
        return 'frontend:dashboard'

