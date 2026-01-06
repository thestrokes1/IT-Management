# Asset views for IT Management Platform.
# Contains all asset-related views (list, create, edit, delete).
# Uses CQRS pattern: Queries for reads, Services for writes.

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from apps.frontend.mixins import CanManageAssetsMixin
from apps.frontend.services import AssetService
from apps.assets.queries import AssetQuery


class AssetsView(LoginRequiredMixin, TemplateView):
    """
    Assets management web interface.
    Uses AssetQuery for read operations.
    """
    template_name = 'frontend/assets.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use Query for reads
        assets = AssetQuery.get_all()
        status_choices = AssetQuery.get_status_choices()
        category_choices = AssetQuery.get_categories()
        
        context.update({
            'assets': assets,
            'status_choices': status_choices,
            'category_choices': category_choices
        })
        return context


class CreateAssetView(LoginRequiredMixin, CanManageAssetsMixin, TemplateView):
    """
    Create new asset web interface.
    Uses AssetQuery for reads, AssetService for writes.
    """
    template_name = 'frontend/create-asset.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use Query for reads
        categories = AssetQuery.get_categories()
        available_users = AssetQuery.get_active_users()
        
        context.update({
            'categories': categories,
            'available_users': available_users,
            'form': {}
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle asset creation using Service."""
        try:
            # Use Service for write operation
            asset = AssetService.create_asset(
                request=request,
                name=request.POST.get('name', '').strip(),
                description=request.POST.get('description', '').strip(),
                category_id=request.POST.get('category', ''),
                serial_number=request.POST.get('serial_number', '').strip(),
                asset_tag=request.POST.get('asset_tag', '').strip(),
                status=request.POST.get('status', 'AVAILABLE'),
                location=request.POST.get('location', '').strip(),
                purchase_date=request.POST.get('purchase_date', ''),
                purchase_price=request.POST.get('purchase_price', ''),
                warranty_expiry=request.POST.get('warranty_expiry', ''),
                assigned_to_id=request.POST.get('assigned_to', '')
            )
            
            messages.success(request, f'Asset "{asset.name}" created successfully!')
            return redirect('frontend:assets')
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error creating asset: {str(e)}')
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)


class EditAssetView(CanManageAssetsMixin, TemplateView):
    """
    Edit asset web interface.
    Uses AssetQuery for reads, AssetService for writes.
    """
    template_name = 'frontend/edit-asset.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset_id = self.kwargs.get('asset_id')
        
        # Use Query for reads
        asset = AssetQuery.get_with_details(asset_id)
        
        if asset is None:
            messages.error(self.request, 'Asset not found.')
            return redirect('frontend:assets')
        
        categories = AssetQuery.get_categories()
        available_users = AssetQuery.get_active_users()
        
        context.update({
            'asset': asset,
            'categories': categories,
            'available_users': available_users,
            'form': {}
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle asset edit using Service."""
        try:
            asset_id = self.kwargs.get('asset_id')
            
            # Use Service for write operation
            asset = AssetService.update_asset(
                request=request,
                asset_id=asset_id,
                name=request.POST.get('name', '').strip(),
                description=request.POST.get('description', '').strip(),
                category_id=request.POST.get('category', ''),
                serial_number=request.POST.get('serial_number', '').strip(),
                asset_tag=request.POST.get('asset_tag', '').strip(),
                status=request.POST.get('status', 'AVAILABLE'),
                location=request.POST.get('location', '').strip(),
                purchase_date=request.POST.get('purchase_date', ''),
                purchase_price=request.POST.get('purchase_price', ''),
                warranty_expiry=request.POST.get('warranty_expiry', ''),
                assigned_to_id=request.POST.get('assigned_to', '')
            )
            
            messages.success(request, f'Asset "{asset.name}" updated successfully!')
            return redirect('frontend:assets')
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error updating asset: {str(e)}')
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)


@login_required(login_url='frontend:login')
@require_http_methods(["DELETE", "POST"])
def delete_asset(request, asset_id):
    """
    Delete an asset.
    Uses AssetService for write operation.
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Authentication required. Please log in.'}, status=401)
        return redirect('frontend:login')
    
    # Check permissions
    if not hasattr(request.user, 'role') or request.user.role not in ['ADMIN', 'SUPERADMIN', 'IT_ADMIN']:
        return JsonResponse({
            'error': 'You do not have permission to delete assets. Only ADMIN or SUPERADMIN roles can delete assets.'
        }, status=403)
    
    try:
        # Use Service for write operation
        AssetService.delete_asset(asset_id)
        
        return JsonResponse({'success': True, 'message': f'Asset deleted successfully.'})
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error deleting asset: {str(e)}'}, status=500)


# Re-export asset_crud for backwards compatibility if needed
try:
    from apps.assets.views import asset_crud
    _has_asset_crud = True
except ImportError:
    _has_asset_crud = False

