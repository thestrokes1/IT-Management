"""
Asset views for IT Management Platform.
Contains all asset-related views (list, create, edit, delete).
Uses CQRS pattern: Queries for reads, Services for writes.
Uses permission_mapper for consistent UI permission flags.
"""

from django.shortcuts import render, redirect, get_object_or_404
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
from apps.core.exceptions import ValidationError
from apps.frontend.permissions_mapper import (
    build_asset_ui_permissions,
    build_assets_permissions_map,
    get_list_permissions,
)


class AssetsView(LoginRequiredMixin, TemplateView):
    """
    Assets management web interface.
    Uses AssetQuery for read operations with role-based access control.
    Only MANAGER+ roles can view all assets. VIEWER/TECHNICIAN are blocked.
    Uses permission_mapper for consistent UI permission flags.
    
    UI Permission Flags Contract:
    {
        "can_view": bool,
        "can_update": bool,
        "can_delete": bool,
        "can_assign": bool,
        "can_unassign": bool,
        "can_self_assign": bool,
        "assigned_to_me": bool,
    }
    """
    template_name = 'frontend/assets.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use Query for reads - only reached if permission granted
        user = self.request.user

        if user.role == 'TECHNICIAN':
            assets = AssetQuery.get_unassigned_or_assigned_to(user)
        else:
            assets = AssetQuery.get_all()

        status_choices = AssetQuery.get_status_choices()
        category_choices = AssetQuery.get_categories()
        
        # Build permissions map using permission_mapper
        permissions_map = build_assets_permissions_map(user, assets)
        
        # Get list-level permissions
        list_permissions = get_list_permissions(user)
        list_permissions['can_create'] = can_create_asset(user)
        
        context.update({
            'assets': assets,
            'status_choices': status_choices,
            'category_choices': category_choices,
            'permissions_map': permissions_map,
            'permissions': list_permissions,
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
        
        # Get list permissions for template consistency
        list_permissions = get_list_permissions(self.request.user)
        list_permissions['can_create'] = can_create_asset(self.request.user)
        
        context.update({
            'categories': categories,
            'available_users': available_users,
            'form': {},
            'permissions': list_permissions,
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
        
        except ValidationError as e:
            # Handle validation errors (like duplicate serial_number)
            messages.error(request, str(e.message))
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error creating asset: {str(e)}')
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)


class AssetDetailView(LoginRequiredMixin, TemplateView):
    """
    Asset detail view.
    Uses AssetQuery for reads.
    Uses permission_mapper for UI permission flags.
    """
    template_name = 'frontend/asset_detail.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset_id = self.kwargs.get('asset_id')
        
        # Use Query for reads
        asset = AssetQuery.get_with_details(asset_id)
        
        if asset is None:
            messages.error(self.request, 'Asset not found.')
            return redirect('frontend:assets')
        
        # Build UI permission flags using permission_mapper
        permissions = build_asset_ui_permissions(self.request.user, asset)
        
        # Get list of assignable users based on role
        from apps.users.models import User
        user = self.request.user
        
        if user.role in ['SUPERADMIN', 'MANAGER', 'IT_ADMIN']:
            # Show all technicians for assignment
            assignable_users = User.objects.filter(role='TECHNICIAN', is_active=True).order_by('username')
        elif user.role == 'TECHNICIAN':
            # Technician can only see themselves for self-assignment
            assignable_users = User.objects.filter(id=user.id)
        else:
            assignable_users = User.objects.none()
        
        context.update({
            'asset': asset,
            'permissions': permissions,
            'assignable_users': assignable_users,
        })
        return context


class EditAssetView(CanManageAssetsMixin, TemplateView):
    """
    Edit asset web interface.
    Uses AssetQuery for reads, AssetService for writes.
    Uses permission_mapper for UI permission flags.
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
        
        # Build UI permission flags using permission_mapper
        permissions = build_asset_ui_permissions(self.request.user, asset)
        
        context.update({
            'asset': asset,
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
        
        # Check domain permission
        assert_can_delete_asset(request.user, asset)
        
        # Use Service for write operation
        AssetService.delete_asset(request, asset_id)
        
        return JsonResponse({'success': True, 'message': f'Asset deleted successfully.'})
    
    except AuthorizationError as e:
        return JsonResponse({'error': str(e)}, status=403)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error deleting asset: {str(e)}'}, status=500)


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
            
            return JsonResponse({'success': True, 'asset': asset})
        
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
            
            # Use Service for delete operation - pass request as first argument
            AssetService.delete_asset(request, asset_id)
            
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
            
            # Use Service for partial update
            updated_asset = AssetService.update_asset(
                request=request,
                asset_id=asset_id,
                name=data.get('name', '').strip(),
                description=data.get('description', '').strip(),
                category_id=data.get('category_id', data.get('category')),
                serial_number=data.get('serial_number', '').strip(),
                asset_tag=data.get('asset_tag', '').strip(),
                status=data.get('status', 'AVAILABLE'),
                location=data.get('location', '').strip(),
                purchase_date=data.get('purchase_date', ''),
                purchase_price=data.get('purchase_price', ''),
                warranty_expiry=data.get('warranty_expiry', ''),
                assigned_to_id=data.get('assigned_to_id', data.get('assigned_to'))
            )
            
            return JsonResponse({'success': True, 'message': f'Asset "{updated_asset.name}" updated successfully.'})
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)



def asset_assign_self(request, asset_id):
    """
    Handle self-assignment of an asset.
    
    Views MUST NOT import or instantiate use cases.
    Views MUST ONLY:
    1. Validate permissions
    2. Build an immutable Command DTO
    3. Pass it to a handler/resolver
    4. Call use_case.execute(command)
    """
    from uuid import UUID
    
    # Convert asset_id to UUID
    try:
        if isinstance(asset_id, int):
            from apps.assets.models import Asset
            asset = get_object_or_404(Asset, id=asset_id)
            asset_uuid = asset.asset_id
        else:
            asset_uuid = UUID(str(asset_id))
    except (ValueError, TypeError, AttributeError):
        messages.error(request, 'Invalid asset ID.')
        return redirect('frontend:assets')
    
    # Get asset for permission check
    from apps.assets.models import Asset
    try:
        asset = Asset.objects.get(id=asset_id)
    except Asset.DoesNotExist:
        messages.error(request, 'Asset not found.')
        return redirect('frontend:assets')
    
    # Check permission using domain authority
    from apps.assets.domain.services.asset_authority import can_assign_to_self as can_assign_to_self_asset
    if not can_assign_to_self_asset(request.user, asset):
        messages.error(request, 'You cannot assign this asset to yourself.')
        return redirect('frontend:assets')
    
    # Build immutable Command DTO (no business logic in view)
    from apps.assets.application.commands import AssetAssignmentCommand
    command = AssetAssignmentCommand(
        actor=request.user,
        asset_id=asset_uuid,
        assignee_id=None  # None = self-assignment
    )
    
    # Pass command to handler (handler routes to correct use case)
    from apps.assets.application.handlers import assign_asset
    result = assign_asset(command)
    
    if result.success:
        messages.success(request, result.data.get('message', 'Asset assigned to you successfully!'))
    else:
        messages.error(request, result.error)
    
    return redirect('frontend:assets')


@login_required
@require_http_methods(["POST"])
def asset_assign_to_user(request, asset_id, user_id):
    """
    Handle assignment of an asset to a specific user.
    
    Views MUST NOT import or instantiate use cases.
    Views MUST ONLY:
    1. Validate permissions
    2. Build an immutable Command DTO
    3. Pass it to a handler/resolver
    4. Call use_case.execute(command)
    """
    from django.shortcuts import get_object_or_404
    from apps.assets.models import Asset
    from apps.users.models import User
    
    # Get asset
    asset = get_object_or_404(Asset, id=asset_id)
    
    # Get target user
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('frontend:asset-detail', asset_id=asset_id)
    
    # Check permission using domain authority
    from apps.assets.domain.services.asset_authority import can_assign as can_assign_asset
    if not can_assign_asset(request.user, asset, target_user):
        messages.error(request, 'You do not have permission to assign this asset.')
        return redirect('frontend:asset-detail', asset_id=asset_id)
    
    # Build immutable Command DTO (no business logic in view)
    from apps.assets.application.commands import AssetAssignmentCommand
    command = AssetAssignmentCommand(
        actor=request.user,
        asset_id=asset.asset_id,
        assignee_id=target_user.id
    )
    
    # Pass command to handler (handler routes to correct use case)
    from apps.assets.application.handlers import assign_asset
    result = assign_asset(command)
    
    if result.success:
        messages.success(request, result.data.get('message', f'Asset assigned to {target_user.username} successfully!'))
    else:
        messages.error(request, result.error)
    
    return redirect('frontend:asset-detail', asset_id=asset_id)


# Wrapper functions for URL patterns
def assets(request):
    """List all assets."""
    view = AssetsView.as_view()
    return view(request)


def asset_detail(request, asset_id):
    """Show asset detail."""
    view = AssetDetailView.as_view()
    return view(request, asset_id=asset_id)


def create_asset(request):
    """Create a new asset."""
    view = CreateAssetView.as_view()
    return view(request)


def edit_asset(request, asset_id):
    """Edit an asset."""
    view = EditAssetView.as_view()
    return view(request, asset_id=asset_id)


def asset_unassign_self(request, asset_id):
    """Unassign asset from self."""
    from django.contrib.auth.decorators import login_required
    from django.views.decorators.http import require_POST
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from apps.assets.models import Asset
    
    asset = get_object_or_404(Asset, id=asset_id)
    
    # Check if user has permission (only assigned user or admin)
    if not (request.user == asset.assigned_to or request.user.role in ['ADMIN', 'SUPERADMIN', 'IT_ADMIN']):
        messages.error(request, 'You do not have permission to unassign this asset.')
        return redirect('frontend:asset-detail', asset_id=asset_id)
    
    # Unassign the asset
    asset.assigned_to = None
    asset.save()
    messages.success(request, 'Asset unassigned successfully.')
    return redirect('frontend:asset-detail', asset_id=asset_id)

