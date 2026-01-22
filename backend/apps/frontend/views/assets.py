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

from apps.frontend.mixins import CanManageAssetsMixin, FrontendAdminReadMixin
from apps.frontend.services import AssetService
from apps.assets.queries import AssetQuery
from apps.assets.domain.services.asset_authority import (
    get_asset_permissions, 
    can_create_asset,
    assert_can_delete_asset,
)
from apps.core.domain.authorization import AuthorizationError


class AssetsView(LoginRequiredMixin, FrontendAdminReadMixin, TemplateView):
    """
    Assets management web interface.
    Uses AssetQuery for read operations with role-based access control.
    Only MANAGER+ roles can view all assets. VIEWER/TECHNICIAN are blocked.
    Uses FrontendAdminReadMixin for consistent permission enforcement.
    """
    template_name = 'frontend/assets.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use Query for reads - only reached if permission granted
        assets = AssetQuery.get_all()
        status_choices = AssetQuery.get_status_choices()
        category_choices = AssetQuery.get_categories()
        
        # Compute permissions map for each asset
        permissions_map = {}
        for asset in assets:
            # Get the actual asset object for permissions check
            asset_obj = asset.to_dict() if hasattr(asset, 'to_dict') else asset
            permissions_map[asset.id] = get_asset_permissions(self.request.user, asset_obj)
        
        context.update({
        'assets': assets,
        'status_choices': status_choices,
        'category_choices': category_choices,
        'permissions_map': permissions_map,
        'permissions': {'can_create': can_create_asset(self.request.user)},
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
        
        # Pass permissions object for template consistency
        permissions = {
        'can_create': can_create_asset(self.request.user),
    }
        
        context.update({
            'categories': categories,
            'available_users': available_users,
            'form': {},
            'permissions': permissions,
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
        
        # Compute permissions for the asset
        asset_dict = asset.to_dict() if hasattr(asset, 'to_dict') else asset
        permissions = get_asset_permissions(self.request.user, asset_dict)
        
        context.update({
            'asset': asset,
            'asset_dict': asset_dict,
            'categories': categories,
            'available_users': available_users,
            'form': {},
            'permissions': permissions,
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
    Uses domain authority for authorization.
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Authentication required. Please log in.'}, status=401)
        return redirect('frontend:login')
    
    try:
        # Get asset for authorization check
        asset = AssetQuery.get_by_id(asset_id)
        if asset is None:
            return JsonResponse({'error': f'Asset with id {asset_id} not found.'}, status=404)
        
        # Convert to dict if it's a DTO
        asset_data = asset.to_dict() if hasattr(asset, 'to_dict') else asset
        
        # Check domain permission
        assert_can_delete_asset(request.user, asset_data)
        
        # Use Service for write operation
        AssetService.delete_asset(asset_id)
        
        return JsonResponse({'success': True, 'message': f'Asset deleted successfully.'})
    
    except AuthorizationError as e:
        return JsonResponse({'error': str(e)}, status=403)
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


@login_required(login_url='frontend:login')
@require_http_methods(["GET", "PATCH", "DELETE"])
def asset_crud(request, asset_id):
    """
    Handle asset CRUD operations (GET, PATCH, DELETE).
    Uses AssetQuery for reads and AssetService for writes.
    """
    try:
        # GET - Retrieve asset details
        if request.method == 'GET':
            asset = AssetQuery.get_with_details(asset_id)
            
            if asset is None:
                return JsonResponse({'error': f'Asset with id {asset_id} not found.'}, status=404)
            
            # Convert to dict if it's a DTO
            if hasattr(asset, 'to_dict'):
                asset_data = asset.to_dict()
            else:
                asset_data = asset
            
            return JsonResponse({'success': True, 'asset': asset_data})
        
        # DELETE - Delete asset
        elif request.method == 'DELETE':
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required. Please log in.'}, status=401)
            
            # Check permissions (same as delete_asset)
            if not hasattr(request.user, 'role') or request.user.role not in ['ADMIN', 'SUPERADMIN', 'IT_ADMIN']:
                return JsonResponse({
                    'error': 'You do not have permission to delete assets. Only ADMIN or SUPERADMIN roles can delete assets.'
                }, status=403)
            
            # Get asset for confirmation
            asset = AssetQuery.get_by_id(asset_id)
            if asset is None:
                return JsonResponse({'error': f'Asset with id {asset_id} not found.'}, status=404)
            
            # Use Service for delete operation
            AssetService.delete_asset(asset_id)
            
            return JsonResponse({'success': True, 'message': 'Asset deleted successfully.'})
        
        # PATCH - Partial update asset
        elif request.method == 'PATCH':
            import json
            
            # Check if user is authenticated
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required. Please log in.'}, status=401)
            
            # Check permissions for update
            if not hasattr(request.user, 'can_manage_assets') or not request.user.can_manage_assets:
                if not hasattr(request.user, 'role') or request.user.role not in ['ADMIN', 'SUPERADMIN', 'IT_ADMIN']:
                    return JsonResponse({
                        'error': 'You do not have permission to update assets.'
                    }, status=403)
            
            data = json.loads(request.body)
            
            # Get asset for authorization check
            asset = AssetQuery.get_by_id(asset_id)
            if asset is None:
                return JsonResponse({'error': f'Asset with id {asset_id} not found.'}, status=404)
            
            # Convert to dict if it's a DTO
            if hasattr(asset, 'to_dict'):
                asset_data = asset.to_dict()
            else:
                asset_data = asset
            
            # Use Service for partial update
            updated_asset = AssetService.update_asset(
                request=request,
                asset_id=asset_id,
                name=data.get('name', asset_data.get('name', '')).strip(),
                description=data.get('description', asset_data.get('description', '')).strip(),
                category_id=data.get('category_id', data.get('category', asset_data.get('category_id'))),
                serial_number=data.get('serial_number', asset_data.get('serial_number', '')).strip(),
                asset_tag=data.get('asset_tag', asset_data.get('asset_tag', '')).strip(),
                status=data.get('status', asset_data.get('status', 'AVAILABLE')),
                location=data.get('location', asset_data.get('location', '')).strip(),
                purchase_date=data.get('purchase_date', asset_data.get('purchase_date', '')),
                purchase_price=data.get('purchase_price', asset_data.get('purchase_price', '')),
                warranty_expiry=data.get('warranty_expiry', asset_data.get('warranty_expiry', '')),
                assigned_to_id=data.get('assigned_to_id', data.get('assigned_to', asset_data.get('assigned_to_id')))
            )
            
            return JsonResponse({'success': True, 'message': f'Asset "{updated_asset.name}" updated successfully.'})
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)


