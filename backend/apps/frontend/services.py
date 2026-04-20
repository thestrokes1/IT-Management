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
        asset_type: str = 'HARDWARE',
        model: str = '',
        manufacturer: str = '',
        version: str = '',
        status: str = 'ACTIVE',
        location: str = '',
        purchase_date: str = '',
        purchase_price: str = '',
        warranty_expiry: str = '',
        end_of_life: str = '',
        contact_type: str = '',
        contact_email: str = '',
        contact_phone: str = '',
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
        
        end_of_life_obj = None
        if end_of_life:
            try:
                end_of_life_obj = datetime.strptime(end_of_life, '%Y-%m-%d').date()
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
            model=model.strip() if model else '',
            manufacturer=manufacturer.strip() if manufacturer else '',
            version=version.strip() if version else '',
            status=status,
            location=location.strip(),
            purchase_date=purchase_date_obj,
            purchase_cost=purchase_cost,
            warranty_expiry=warranty_expiry_obj,
            end_of_life=end_of_life_obj,
            contact_type=contact_type.strip() if contact_type else '',
            contact_email=contact_email.strip() if contact_email else '',
            contact_phone=contact_phone.strip() if contact_phone else '',
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
        asset_type: str = '',
        model: str = '',
        manufacturer: str = '',
        version: str = '',
        status: str = 'ACTIVE',
        location: str = '',
        purchase_date: str = '',
        purchase_price: str = '',
        warranty_expiry: str = '',
        end_of_life: str = '',
        contact_type: str = '',
        contact_email: str = '',
        contact_phone: str = '',
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
        
        end_of_life_obj = asset.end_of_life
        if end_of_life:
            try:
                end_of_life_obj = datetime.strptime(end_of_life, '%Y-%m-%d').date()
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
        # Only update asset_type if provided
        if asset_type:
            asset.asset_type = asset_type
        if model is not None:
            asset.model = model.strip() if model else ''
        if manufacturer is not None:
            asset.manufacturer = manufacturer.strip() if manufacturer else ''
        if version is not None:
            asset.version = version.strip() if version else ''
        asset.status = status
        asset.location = location.strip()
        asset.purchase_date = purchase_date_obj
        asset.purchase_cost = purchase_cost
        asset.warranty_expiry = warranty_expiry_obj
        asset.end_of_life = end_of_life_obj
        if contact_type is not None:
            asset.contact_type = contact_type.strip() if contact_type else ''
        if contact_email is not None:
            asset.contact_email = contact_email.strip() if contact_email else ''
        if contact_phone is not None:
            asset.contact_phone = contact_phone.strip() if contact_phone else ''
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


class ReportsQueryService:
    """Service layer for fetching aggregated report data."""
    
    def get_full_report_data(self, user, is_admin: bool = False) -> Dict:
        total_assets = self._get_total_assets()
        active_projects = self._get_active_projects()
        open_tickets = self._get_open_tickets()
        active_users = self._get_active_users()
        recent_security_events = self._get_recent_security_events()
        asset_status_distribution = self._get_asset_status_distribution()
        tickets_by_status = self._get_tickets_by_status()
        tickets_by_priority = self._get_tickets_by_priority()
        total_tickets = self._get_total_tickets()
        recent_tickets = self._get_recent_tickets(user, is_admin)
        recent_activities = self._get_recent_activities(user)
        
        return {
            'total_assets': total_assets,
            'active_projects': active_projects,
            'open_tickets': open_tickets,
            'active_users': active_users,
            'recent_security_events': recent_security_events,
            'asset_status_distribution': asset_status_distribution,
            'tickets_by_status': tickets_by_status,
            'tickets_by_priority': tickets_by_priority,
            'total_tickets': total_tickets,
            'recent_tickets': recent_tickets,
            'recent_activities': recent_activities,
            'is_admin': is_admin,
        }
    
    def _get_total_assets(self) -> int:
        try:
            from apps.assets.models import Asset
            return Asset.objects.count()
        except Exception:
            return 0
    
    def _get_active_projects(self) -> int:
        try:
            from apps.projects.models import Project
            return Project.objects.filter(status__in=['ACTIVE', 'IN_PROGRESS', 'ON_HOLD']).count()
        except Exception:
            return 0
    
    def _get_open_tickets(self) -> int:
        try:
            from apps.tickets.models import Ticket
            return Ticket.objects.filter(status__in=['NEW', 'OPEN', 'IN_PROGRESS']).count()
        except Exception:
            return 0
    
    def _get_active_users(self) -> int:
        try:
            from apps.users.models import User
            return User.objects.filter(is_active=True, is_superuser=False).count()
        except Exception:
            return 0
    
    def _get_recent_security_events(self) -> int:
        try:
            from apps.logs.models import SecurityEvent
            from datetime import timedelta
            recent_date = timezone.now() - timedelta(days=7)
            return SecurityEvent.objects.filter(detected_at__gte=recent_date).count()
        except Exception:
            return 0
    
    def _get_asset_status_distribution(self) -> Dict:
        try:
            from apps.assets.models import Asset
            distribution = {}
            for status, label in Asset.STATUS_CHOICES:
                count = Asset.objects.filter(status=status).count()
                distribution[status] = {'label': label, 'count': count}
            return distribution
        except Exception:
            return {}
    
    def _get_tickets_by_status(self) -> Dict:
        try:
            from apps.tickets.models import Ticket
            distribution = {}
            for status, label in Ticket.STATUS_CHOICES:
                count = Ticket.objects.filter(status=status).count()
                distribution[status] = {'label': label, 'count': count}
            return distribution
        except Exception:
            return {}
    
    def _get_tickets_by_priority(self) -> Dict:
        try:
            from apps.tickets.models import Ticket
            distribution = {}
            for priority, label in Ticket.PRIORITY_CHOICES:
                count = Ticket.objects.filter(priority=priority).count()
                distribution[priority] = {'label': label, 'count': count}
            return distribution
        except Exception:
            return {}
    
    def _get_total_tickets(self) -> int:
        try:
            from apps.tickets.models import Ticket
            return Ticket.objects.count()
        except Exception:
            return 0
    
    def _get_recent_tickets(self, user, is_admin: bool, limit: int = 50) -> list:
        try:
            from apps.tickets.models import Ticket
            from django.db.models import Q
            
            if is_admin:
                tickets = Ticket.objects.select_related('created_by', 'assigned_to', 'category').order_by('-created_at')[:limit]
            else:
                tickets = Ticket.objects.filter(Q(created_by=user) | Q(assigned_to=user)).select_related('created_by', 'assigned_to', 'category').order_by('-created_at')[:limit]
            
            return [self._ticket_to_dict(ticket) for ticket in tickets]
        except Exception:
            return []
    
    def _get_recent_activities(self, user, limit: int = 50) -> list:
        try:
            from apps.logs.services.activity_service import ActivityService
            service = ActivityService()
            activities = service.get_activity_logs(user=user, limit=limit)
            from apps.logs.services.log_adapter import LogAdapter
            adapter = LogAdapter()
            return adapter.to_template_dicts(activities)
        except Exception:
            return []
    
    def _ticket_to_dict(self, ticket) -> Dict:
        return {
            'id': ticket.id,
            'title': ticket.title,
            'status': ticket.status,
            'priority': ticket.priority,
            'category': ticket.category.name if ticket.category else None,
            'created_at': ticket.created_at,
            'created_by': {
                'id': ticket.created_by.id if ticket.created_by else None,
                'username': ticket.created_by.username if ticket.created_by else 'System',
            },
            'assigned_to': {
                'id': ticket.assigned_to.id if ticket.assigned_to else None,
                'username': ticket.assigned_to.username if ticket.assigned_to else None,
            },
            'status_display': ticket.get_status_display(),
            'priority_display': ticket.get_priority_display(),
        }
