# Frontend services module for non-project entities.
# Contains command services for Ticket and Asset state mutations.
# Project mutations MUST ONLY occur in apps/projects/application/* CQRS commands.
# Uses domain exceptions for error handling - no HttpResponse/JsonResponse in services.
# Uses domain authority for authorization checks.
# Uses domain events for activity tracking (no persistence logic in services).

from typing import Optional, Dict
from django.utils import timezone
from django.db import transaction

from apps.core.exceptions import (
    NotFoundError,
    ValidationError,
    PermissionDeniedError,
    DomainException,
)
from apps.core.domain.authorization import AuthorizationError
from apps.core.events import EventPublisher
from apps.tickets.domain.services.ticket_authority import (
    can_create_ticket,
    can_update_ticket,
    can_delete_ticket,
)
from apps.assets.domain.services.asset_authority import (
    can_create_asset,
    can_update_asset,
    can_delete_asset,
)


# =============================================================================
# ARCHITECTURAL NOTE: Project mutations are NOT handled here.
# All Project model mutations MUST occur ONLY in apps/projects/application/* CQRS commands:
#   - CreateProject.execute()
#   - UpdateProject.execute()
#   - DeleteProject.execute()
#   - ChangeProjectStatus.execute()
#   - ManageProjectMembers.execute()
# This ensures:
#   - Authorization is centralized in domain authority
#   - Business logic is encapsulated in commands
#   - Domain events are emitted consistently
#   - Write patterns are auditable
# =============================================================================


class TicketService(EventPublisher):
    """
    Service class for Ticket commands.
    Handles all state mutations for tickets.
    Raises ONLY domain exceptions - no HTTP responses.
    """
    
    @classmethod
    def _get_ticket_or_raise(cls, ticket_id: int):
        """Get ticket by ID or raise NotFoundError."""
        from apps.tickets.models import Ticket
        try:
            return Ticket.objects.get(id=ticket_id)
        except (Ticket.DoesNotExist, ValueError):
            raise NotFoundError(
                resource_type="Ticket",
                resource_id=ticket_id
            )
    
    @classmethod
    def create_ticket(
        cls,
        request,
        title: str,
        description: str,
        category_id: str,
        ticket_type_id: str,
        priority: str = 'MEDIUM',
        impact: str = 'MEDIUM',
        urgency: str = 'MEDIUM',
        assigned_to_id: str = '',
        due_date: str = ''
    ) -> 'Ticket':
        """Create a new ticket."""
        from apps.tickets.models import Ticket, TicketCategory, TicketType
        from datetime import datetime
        
        # Check authorization using domain authority
        # Raises PermissionDeniedError if not allowed
        if not can_create_ticket(request.user):
            raise PermissionDeniedError("You are not allowed to create tickets.")
        
        # Validate required fields
        if not title or not title.strip():
            raise ValidationError(message="Title is required", field='title')
        if not description or not description.strip():
            raise ValidationError(message="Description is required", field='description')
        
        # Get related objects
        try:
            category = TicketCategory.objects.get(id=category_id) if category_id else None
        except (TicketCategory.DoesNotExist, ValueError):
            raise NotFoundError(resource_type="TicketCategory", resource_id=category_id)
        
        try:
            ticket_type = TicketType.objects.get(id=ticket_type_id) if ticket_type_id else None
        except (TicketType.DoesNotExist, ValueError):
            raise NotFoundError(resource_type="TicketType", resource_id=ticket_type_id)
        
        assigned_to = None
        if assigned_to_id:
            from apps.users.models import User
            try:
                assigned_to = User.objects.get(id=assigned_to_id)
            except (User.DoesNotExist, ValueError):
                pass  # Optional field
        
        # Parse due date
        sla_due_at = None
        if due_date:
            try:
                sla_due_at = datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                pass  # Optional field
        
        # Create ticket
        ticket = Ticket.objects.create(
            title=title.strip(),
            description=description.strip(),
            category=category,
            ticket_type=ticket_type,
            priority=priority,
            impact=impact,
            urgency=urgency,
            assigned_to=assigned_to,
            sla_due_at=sla_due_at,
            requester=request.user,
            created_by=request.user
        )
        
        # Activity logging - runs after transaction commits, never breaks command
        transaction.on_commit(lambda: cls._log_ticket_created(ticket, request.user))
        
        return ticket
    
    @classmethod
    def _log_ticket_created(cls, ticket, user):
        """Log ticket creation activity."""
        try:
            from apps.logs.services.activity_service import ActivityService
            ActivityService().log_ticket_created(ticket, user, None)
        except Exception:
            pass  # Logging must never break the command
    
    @classmethod
    def update_ticket(
        cls,
        request,
        ticket_id: int,
        title: str,
        description: str,
        category_id: str,
        ticket_type_id: str,
        status: str = 'NEW',
        priority: str = 'MEDIUM',
        impact: str = 'MEDIUM',
        urgency: str = 'MEDIUM',
        assigned_to_id: str = '',
        assigned_team: str = '',
        location: str = '',
        contact_phone: str = '',
        contact_email: str = '',
        sla_due_at_str: str = '',
        resolution_summary: str = ''
    ) -> 'Ticket':
        """Update an existing ticket."""
        from apps.tickets.models import Ticket, TicketCategory, TicketType
        from datetime import datetime
        
        ticket = cls._get_ticket_or_raise(ticket_id)
        
        # Validate required fields
        if not title or not title.strip():
            raise ValidationError(message="Title is required", field='title')
        if not description or not description.strip():
            raise ValidationError(message="Description is required", field='description')
        
        # Get related objects
        try:
            category = TicketCategory.objects.get(id=category_id) if category_id else ticket.category
        except (TicketCategory.DoesNotExist, ValueError):
            raise NotFoundError(resource_type="TicketCategory", resource_id=category_id)
        
        try:
            ticket_type = TicketType.objects.get(id=ticket_type_id) if ticket_type_id else ticket.ticket_type
        except (TicketType.DoesNotExist, ValueError):
            raise NotFoundError(resource_type="TicketType", resource_id=ticket_type_id)
        
        assigned_to = ticket.assigned_to
        if assigned_to_id:
            from apps.users.models import User
            try:
                assigned_to = User.objects.get(id=assigned_to_id)
            except (User.DoesNotExist, ValueError):
                pass
        
        # Parse SLA due date
        sla_due_at = ticket.sla_due_at
        if sla_due_at_str:
            try:
                sla_due_at = datetime.strptime(sla_due_at_str, '%Y-%m-%d')
            except ValueError:
                pass
        
        # Update ticket
        ticket.title = title.strip()
        ticket.description = description.strip()
        ticket.category = category
        ticket.ticket_type = ticket_type
        ticket.status = status
        ticket.priority = priority
        ticket.impact = impact
        ticket.urgency = urgency
        ticket.assigned_to = assigned_to
        ticket.assigned_team = assigned_team.strip()
        ticket.location = location.strip()
        ticket.contact_phone = contact_phone.strip()
        ticket.contact_email = contact_email.strip()
        ticket.sla_due_at = sla_due_at
        ticket.resolution_summary = resolution_summary.strip()
        ticket.updated_by = request.user
        ticket.save()
        
        # Activity logging - runs after transaction commits, never breaks command
        transaction.on_commit(lambda: cls._log_ticket_updated(ticket, request.user))
        
        return ticket
    
    @classmethod
    def _log_ticket_updated(cls, ticket, user):
        """Log ticket update activity."""
        try:
            from apps.logs.services.activity_service import ActivityService
            ActivityService().log_ticket_action(
                action='UPDATE',
                ticket=ticket,
                actor=user,
                request=None,
                description=f"Updated ticket #{ticket.id}: {ticket.title}"
            )
        except Exception:
            pass  # Logging must never break the command
    
    @classmethod
    def delete_ticket(cls, ticket_id: int) -> bool:
        """
        Delete a ticket and all related records.
        
        Uses raw SQL to bypass Django signals that might cause FK issues.
        
        Args:
            ticket_id: Ticket ID to delete
            
        Returns:
            True if successful
            
        Raises:
            NotFoundError: If ticket not found
        """
        from django.db import connection
        from apps.tickets.models import Ticket
        
        ticket = cls._get_ticket_or_raise(ticket_id)
        ticket_db_id = ticket.id
        
        # Use raw SQL to avoid signal interference
        with connection.cursor() as cursor:
            # Delete related records first
            cursor.execute("DELETE FROM ticket_attachments WHERE ticket_id = %s", [ticket_db_id])
            cursor.execute("DELETE FROM ticket_comments WHERE ticket_id = %s", [ticket_db_id])
            cursor.execute("DELETE FROM ticket_history WHERE ticket_id = %s", [ticket_db_id])
            cursor.execute("DELETE FROM ticket_escalations WHERE ticket_id = %s", [ticket_db_id])
            cursor.execute("DELETE FROM ticket_satisfaction WHERE ticket_id = %s", [ticket_db_id])
            cursor.execute("DELETE FROM ticket_status_history WHERE ticket_id = %s", [ticket_db_id])
            
            # Clear related tickets (many-to-many)
            cursor.execute("DELETE FROM tickets_related_tickets WHERE from_ticket_id = %s", [ticket_db_id])
            cursor.execute("DELETE FROM tickets_related_tickets WHERE to_ticket_id = %s", [ticket_db_id])
            
            # Update child tickets
            cursor.execute("UPDATE tickets SET parent_ticket_id = NULL WHERE parent_ticket_id = %s", [ticket_db_id])
            
            # Finally delete the ticket itself
            cursor.execute("DELETE FROM tickets WHERE id = %s", [ticket_db_id])
        
        return True
    
    @classmethod
    def partial_update_ticket(cls, ticket_id: int, data: dict) -> 'Ticket':
        """Partially update a ticket."""
        from apps.tickets.models import Ticket
        
        ticket = cls._get_ticket_or_raise(ticket_id)
        
        # Update only provided fields
        for field, value in data.items():
            if hasattr(ticket, field) and field not in ['id', 'ticket_id', 'created_at', 'updated_at']:
                setattr(ticket, field, value)
        
        ticket.save()
        return ticket


class AssetService(EventPublisher):
    """
    Service class for Asset commands.
    Handles all state mutations for assets.
    Raises ONLY domain exceptions - no HTTP responses.
    """
    
    @classmethod
    def _get_asset_or_raise(cls, asset_id: int):
        """Get asset by ID or raise NotFoundError."""
        from apps.assets.models import Asset
        try:
            return Asset.objects.get(id=asset_id)
        except (Asset.DoesNotExist, ValueError):
            raise NotFoundError(
                resource_type="Asset",
                resource_id=asset_id
            )
    
    @classmethod
    def create_asset(
        cls,
        request,
        name: str,
        description: str,
        category_id: str,
        serial_number: str = '',
        asset_tag: str = '',  # Not in model, but used in views
        status: str = 'ACTIVE',
        location: str = '',
        purchase_date: str = '',
        purchase_price: str = '',
        warranty_expiry: str = '',
        assigned_to_id: str = ''
    ) -> 'Asset':
        """Create a new asset."""
        from apps.assets.models import Asset, AssetCategory
        from datetime import datetime
        
        # Check authorization using domain authority
        # Raises PermissionDeniedError if not allowed
        if not can_create_asset(request.user):
            raise PermissionDeniedError("You are not allowed to create assets.")
        
        # Validate required fields
        if not name or not name.strip():
            raise ValidationError(message="Name is required", field='name')
        
        # PRE-SAVE VALIDATION: Check for duplicate serial_number
        # This prevents IntegrityError crashes and provides a friendly error message
        # Only validate if serial_number is provided (it's an optional field)
        if serial_number and serial_number.strip():
            from apps.assets.models import Asset
            existing_asset = Asset.objects.filter(
                serial_number__iexact=serial_number.strip()
            ).first()
            if existing_asset:
                raise ValidationError(
                    message=f"An asset with serial number '{serial_number}' already exists. "
                           f"Please choose a different serial number.",
                    field='serial_number'
                )
        
        # Get category
        try:
            category = AssetCategory.objects.get(id=category_id) if category_id else None
        except (AssetCategory.DoesNotExist, ValueError):
            raise NotFoundError(resource_type="AssetCategory", resource_id=category_id)
        
        # Determine asset type (default to HARDWARE)
        asset_type = 'HARDWARE'  # Default, can be made configurable
        
        # Parse dates
        purchase_date_obj = None
        if purchase_date:
            try:
                purchase_date_obj = datetime.strptime(purchase_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        warranty_expiry_obj = None
        if warranty_expiry:
            try:
                warranty_expiry_obj = datetime.strptime(warranty_expiry, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Parse purchase price
        purchase_cost = None
        if purchase_price:
            try:
                purchase_cost = float(purchase_price)
            except (ValueError, TypeError):
                pass
        
        # Get assigned user
        assigned_to = None
        if assigned_to_id:
            from apps.users.models import User
            try:
                assigned_to = User.objects.get(id=assigned_to_id)
            except (User.DoesNotExist, ValueError):
                pass
        
        # Create asset
        asset = Asset.objects.create(
            name=name.strip(),
            description=description.strip(),
            asset_type=asset_type,
            category=category,
            serial_number=serial_number.strip() if serial_number else '',
            status=status,
            location=location.strip(),
            purchase_date=purchase_date_obj,
            purchase_cost=purchase_cost,
            warranty_expiry=warranty_expiry_obj,
            assigned_to=assigned_to,
            created_by=request.user
        )
        
        # Activity logging - runs after transaction commits, never breaks command
        transaction.on_commit(lambda: cls._log_asset_created(asset, request.user))
        
        return asset
    
    @classmethod
    def _log_asset_created(cls, asset, user):
        """Log asset creation activity."""
        try:
            from apps.logs.services.activity_service import ActivityService
            ActivityService().log_asset_created(asset, user, None)
        except Exception:
            pass  # Logging must never break the command
    
    @classmethod
    def update_asset(
        cls,
        request,
        asset_id: int,
        name: str,
        description: str,
        category_id: str,
        serial_number: str = '',
        asset_tag: str = '',  # Not in model, but used in views
        status: str = 'ACTIVE',
        location: str = '',
        purchase_date: str = '',
        purchase_price: str = '',
        warranty_expiry: str = '',
        assigned_to_id: str = ''
    ) -> 'Asset':
        """Update an existing asset."""
        from apps.assets.models import Asset, AssetCategory
        from datetime import datetime
        
        asset = cls._get_asset_or_raise(asset_id)
        
        # Check authorization using domain authority
        # Raises PermissionDeniedError if not allowed
        if not can_update_asset(request.user, asset):
            raise PermissionDeniedError("You are not allowed to update this asset.")
        
        # Validate required fields
        if not name or not name.strip():
            raise ValidationError(message="Name is required", field='name')
        
        # Get category
        try:
            category = AssetCategory.objects.get(id=category_id) if category_id else asset.category
        except (AssetCategory.DoesNotExist, ValueError):
            raise NotFoundError(resource_type="AssetCategory", resource_id=category_id)
        
        # Parse dates
        purchase_date_obj = asset.purchase_date
        if purchase_date:
            try:
                purchase_date_obj = datetime.strptime(purchase_date, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        warranty_expiry_obj = asset.warranty_expiry
        if warranty_expiry:
            try:
                warranty_expiry_obj = datetime.strptime(warranty_expiry, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Parse purchase price
        purchase_cost = asset.purchase_cost
        if purchase_price:
            try:
                purchase_cost = float(purchase_price)
            except (ValueError, TypeError):
                pass
        
        # Get assigned user
        assigned_to = asset.assigned_to
        if assigned_to_id:
            from apps.users.models import User
            try:
                assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None
            except (User.DoesNotExist, ValueError):
                pass
        
        # Update asset
        asset.name = name.strip()
        asset.description = description.strip()
        asset.category = category
        asset.serial_number = serial_number.strip() if serial_number else asset.serial_number
        asset.status = status
        asset.location = location.strip()
        asset.purchase_date = purchase_date_obj
        asset.purchase_cost = purchase_cost
        asset.warranty_expiry = warranty_expiry_obj
        asset.assigned_to = assigned_to
        asset.updated_by = request.user
        asset.save()
        
        # Activity logging - runs after transaction commits, never breaks command
        transaction.on_commit(lambda: cls._log_asset_updated(asset, request.user))
        
        return asset
    
    @classmethod
    def _log_asset_updated(cls, asset, user):
        """Log asset update activity."""
        try:
            from apps.logs.services.activity_service import ActivityService
            ActivityService().log_asset_action(
                action='UPDATE',
                asset=asset,
                actor=user,
                request=None,
                description=f"Updated asset: {asset.name}"
            )
        except Exception:
            pass  # Logging must never break the command
    
    @classmethod
    def delete_asset(cls, request, asset_id: int) -> bool:
        """
        Delete an asset and all related records.
        
        Uses raw SQL to bypass Django signals that might cause FK issues.
        Handles foreign key constraints by deleting related records first,
        including subclasses (HardwareAsset, SoftwareAsset).
        
        Args:
            request: HTTP request object
            asset_id: Asset ID to delete
            
        Returns:
            True if successful
            
        Raises:
            NotFoundError: If asset not found
            PermissionDeniedError: If user lacks permission
        """
        from django.db import connection
        from django.db.models import Q
        from apps.assets.models import (
            Asset, AssetAssignment, AssetMaintenance, AssetAuditLog,
            HardwareAsset, SoftwareAsset
        )
        
        asset = cls._get_asset_or_raise(asset_id)
        
        # Check authorization using domain authority
        # Raises PermissionDeniedError if not allowed
        if not can_delete_asset(request.user, asset):
            raise PermissionDeniedError("You are not allowed to delete this asset.")
        
        asset_db_id = asset.id
        
        # Use raw SQL to avoid signal interference
        with connection.cursor() as cursor:
            # Delete related records first
            cursor.execute("DELETE FROM asset_assignments WHERE asset_id = %s", [asset_db_id])
            cursor.execute("DELETE FROM asset_maintenance WHERE asset_id = %s", [asset_db_id])
            cursor.execute("DELETE FROM asset_audit_logs WHERE asset_id = %s", [asset_db_id])
            
            # Delete subclasses first (HardwareAsset, SoftwareAsset)
            # These use asset_ptr_id as the FK
            cursor.execute("DELETE FROM hardware_assets WHERE asset_ptr_id = %s", [asset_db_id])
            cursor.execute("DELETE FROM software_assets WHERE asset_ptr_id = %s", [asset_db_id])
            
            # Finally delete the asset itself
            cursor.execute("DELETE FROM assets WHERE id = %s", [asset_db_id])
        
        return True
