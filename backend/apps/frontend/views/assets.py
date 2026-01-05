"""
Asset views for IT Management Platform.
Contains all asset-related views (list, create, edit, delete, API).
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
import json

try:
    from apps.users.models import User
    from apps.assets.models import Asset, AssetCategory
except ImportError:
    User = None
    Asset = None


class AssetsView(LoginRequiredMixin, TemplateView):
    """
    Assets management web interface.
    """
    template_name = 'frontend/assets.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            assets = Asset.objects.select_related('category', 'assigned_to').order_by('-created_at')[:50]
            categories = Asset.objects.select_related('category').values('category__name').distinct()
        except:
            assets = []
            categories = []
        context.update({
            'assets': assets,
            'categories': categories
        })
        return context


class CreateAssetView(LoginRequiredMixin, TemplateView):
    """
    Create new asset web interface.
    """
    template_name = 'frontend/create-asset.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            categories = AssetCategory.objects.filter(is_active=True)
            available_users = User.objects.filter(is_active=True)
        except:
            categories = []
            available_users = []
        context.update({
            'categories': categories,
            'available_users': available_users,
            'form': {}
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle asset creation."""
        try:
            name = request.POST.get('name', '')
            asset_tag = request.POST.get('asset_tag', '')
            asset_type = request.POST.get('asset_type', '')
            category_id = request.POST.get('category', '')
            description = request.POST.get('description', '')
            serial_number = request.POST.get('serial_number', '')
            model = request.POST.get('model', '')
            manufacturer = request.POST.get('manufacturer', '')
            version = request.POST.get('version', '')
            status = request.POST.get('status', 'ACTIVE')
            assigned_to_id = request.POST.get('assigned_to', '')
            location = request.POST.get('location', '')
            purchase_date = request.POST.get('purchase_date', '')
            purchase_cost = request.POST.get('purchase_cost', '')
            warranty_expiry = request.POST.get('warranty_expiry', '')
            end_of_life = request.POST.get('end_of_life', '')
            
            # Validation
            errors = {}
            if not name:
                errors['name'] = 'Asset name is required'
            if not asset_type:
                errors['asset_type'] = 'Asset type is required'
            if not category_id:
                errors['category'] = 'Category is required'
            if not status:
                errors['status'] = 'Status is required'
            
            if errors:
                context = self.get_context_data()
                context['errors'] = errors
                context['form'] = request.POST
                return render(request, self.template_name, context)
            
            # Create asset
            category = AssetCategory.objects.get(id=category_id)
            assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None
            
            asset = Asset.objects.create(
                name=name,
                asset_type=asset_type,
                category=category,
                description=description,
                serial_number=serial_number if serial_number else None,
                model=model,
                manufacturer=manufacturer,
                version=version,
                status=status,
                assigned_to=assigned_to,
                location=location,
                purchase_date=purchase_date if purchase_date else None,
                purchase_cost=purchase_cost if purchase_cost else None,
                warranty_expiry=warranty_expiry if warranty_expiry else None,
                end_of_life=end_of_life if end_of_life else None,
                created_by=request.user
            )
            
            messages.success(request, f'Asset "{asset.name}" created successfully!')
            return redirect('frontend:assets')
        
        except Exception as e:
            messages.error(request, f'Error creating asset: {str(e)}')
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)


class EditAssetView(LoginRequiredMixin, TemplateView):
    """
    Edit asset web interface.
    """
    template_name = 'frontend/edit-asset.html'
    login_url = 'frontend:login'
    
    def dispatch(self, request, asset_id, *args, **kwargs):
        """Check if user can manage assets."""
        if not hasattr(request.user, 'can_manage_assets') or not request.user.can_manage_assets:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'You do not have permission to edit assets.'}, status=403)
            messages.error(request, 'You do not have permission to edit assets.')
            return redirect('frontend:assets')
        self.asset_id = asset_id
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            asset = Asset.objects.select_related('category', 'assigned_to').get(id=self.asset_id)
            categories = AssetCategory.objects.filter(is_active=True)
            available_users = User.objects.filter(is_active=True)
            context.update({
                'asset': asset,
                'categories': categories,
                'available_users': available_users,
                'form': {}
            })
        except Asset.DoesNotExist:
            messages.error(self.request, 'Asset not found.')
            return redirect('frontend:assets')
        except Exception as e:
            messages.error(self.request, f'Error loading asset: {str(e)}')
            return redirect('frontend:assets')
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle asset edit."""
        try:
            asset = Asset.objects.select_related('category', 'assigned_to').get(id=self.asset_id)
            
            name = request.POST.get('name', '')
            asset_tag = request.POST.get('asset_tag', '')
            asset_type = request.POST.get('asset_type', '')
            category_id = request.POST.get('category', '')
            description = request.POST.get('description', '')
            serial_number = request.POST.get('serial_number', '')
            model = request.POST.get('model', '')
            manufacturer = request.POST.get('manufacturer', '')
            version = request.POST.get('version', '')
            status = request.POST.get('status', 'ACTIVE')
            assigned_to_id = request.POST.get('assigned_to', '')
            location = request.POST.get('location', '')
            purchase_date = request.POST.get('purchase_date', '')
            purchase_cost = request.POST.get('purchase_cost', '')
            warranty_expiry = request.POST.get('warranty_expiry', '')
            
            # Validation
            errors = {}
            if not name:
                errors['name'] = 'Asset name is required'
            if not asset_tag:
                errors['asset_tag'] = 'Asset tag is required'
            if not asset_type:
                errors['asset_type'] = 'Asset type is required'
            if not category_id:
                errors['category'] = 'Category is required'
            if not status:
                errors['status'] = 'Status is required'
            
            if errors:
                context = self.get_context_data()
                context['errors'] = errors
                context['form'] = request.POST
                return render(request, self.template_name, context)
            
            # Update asset
            category = AssetCategory.objects.get(id=category_id)
            assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None
            
            asset.name = name
            asset.asset_tag = asset_tag
            asset.asset_type = asset_type
            asset.category = category
            asset.description = description
            asset.serial_number = serial_number if serial_number else None
            asset.model = model
            asset.manufacturer = manufacturer
            asset.version = version
            asset.status = status
            asset.assigned_to = assigned_to
            asset.location = location
            asset.purchase_date = purchase_date if purchase_date else None
            asset.purchase_cost = purchase_cost if purchase_cost else None
            asset.warranty_expiry = warranty_expiry if warranty_expiry else None
            asset.save()
            
            messages.success(request, f'Asset "{asset.name}" updated successfully!')
            return redirect('frontend:assets')
        
        except Asset.DoesNotExist:
            messages.error(request, 'Asset not found.')
            return redirect('frontend:assets')
        except Exception as e:
            messages.error(request, f'Error updating asset: {str(e)}')
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)


@login_required(login_url='frontend:login')
@require_http_methods(["DELETE", "PATCH"])
def asset_crud(request, asset_id):
    """Handle asset CRUD operations (DELETE and PATCH)."""
    # Check permissions
    if not hasattr(request.user, 'role') or request.user.role not in ['ADMIN', 'SUPERADMIN']:
        return JsonResponse({'error': 'You do not have permission to manage assets.'}, status=403)
    
    try:
        asset = Asset.objects.get(id=asset_id)
        
        if request.method == 'DELETE':
            from django.db import transaction
            from django.db.models.signals import pre_delete
            from django.dispatch import receiver
            from apps.assets.models import AssetAssignment, AssetMaintenance, AssetAuditLog
            
            asset_name = asset.name
            
            # Use transaction to ensure all deletions happen atomically
            with transaction.atomic():
                # Temporarily disconnect the pre_delete signal to prevent it from
                # creating an AssetAuditLog while the asset is being deleted
                # This avoids the FOREIGN KEY constraint issue
                try:
                    from apps.assets.signals import create_asset_deletion_log
                    pre_delete.disconnect(create_asset_deletion_log, sender=Asset)
                    signal_disconnected = True
                except Exception:
                    signal_disconnected = False
                
                try:
                    # Delete related records in the correct order to avoid constraint errors
                    # First delete maintenance records
                    try:
                        AssetMaintenance.objects.filter(asset=asset).delete()
                    except Exception as e:
                        pass  # Continue if no maintenance records exist
                    
                    # Delete audit logs
                    try:
                        AssetAuditLog.objects.filter(asset=asset).delete()
                    except Exception as e:
                        pass  # Continue if no audit logs exist
                    
                    # Delete assignments
                    try:
                        AssetAssignment.objects.filter(asset=asset).delete()
                    except Exception as e:
                        pass  # Continue if no assignments exist
                    
                    # Now delete the asset itself - CASCADE will handle any remaining references
                    asset.delete()
                    
                finally:
                    # Reconnect the signal if it was disconnected
                    if signal_disconnected:
                        try:
                            pre_delete.connect(create_asset_deletion_log, sender=Asset)
                        except Exception:
                            pass
            
            return JsonResponse({'success': True, 'message': f'Asset "{asset_name}" deleted successfully.'})
        
        elif request.method == 'PATCH':
            # Update asset
            data = json.loads(request.body)
            
            if 'name' in data and data['name'].strip():
                asset.name = data['name']
            if 'tag' in data:
                asset.tag = data['tag']
            
            asset.save()
            
            return JsonResponse({'success': True, 'message': f'Asset "{asset.name}" updated successfully.'})
    
    except Asset.DoesNotExist:
        return JsonResponse({'error': 'Asset not found.'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

