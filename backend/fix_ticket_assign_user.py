"""
Fix script for ticket_assign_to_user NameError.
Run this to fix the 'User is not defined' error.
"""

import re

# Read the file
file_path = 'apps/frontend/views/tickets.py'
with open(file_path, 'r') as f:
    content = f.read()

# Find and fix the ticket_assign_to_user function
# We need to add the import for User inside the function

old_function = '''@login_required
@require_http_methods(["POST"])
def ticket_assign_to_user(request, ticket_id, user_id):
    """
    Assign a ticket to a specific user.
    For IT_ADMIN, MANAGER, SUPERADMIN to assign to any user.
    """
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Get target user
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('frontend:ticket-detail', ticket_id=ticket_id)
    
    # Check permission using domain authority
    from apps.tickets.domain.services.ticket_authority import can_assign as can_assign_ticket
    if not can_assign_ticket(request.user, ticket, target_user):
        messages.error(request, 'You do not have permission to assign this ticket.')
        return redirect('frontend:ticket-detail', ticket_id=ticket_id)
    
    # Store old assignee for logging
    old_assignee = ticket.assigned_to
    old_assignee_name = old_assignee.username if old_assignee else None
    
    # Perform the assignment directly
    ticket.assigned_to = target_user
    ticket.assignment_status = 'ASSIGNED'
    ticket.updated_by = request.user
    ticket.save()
    
    # Emit domain event for activity logging
    from apps.tickets.domain.events import emit_ticket_assigned
    emit_ticket_assigned(
        ticket_id=ticket.id,
        ticket_title=ticket.title,
        actor=request.user,
        assignee_id=target_user.id,
        assignee_username=target_user.username,
        previous_assignee_id=old_assignee.id if old_assignee else None,
        previous_assignee_username=old_assignee_name,
    )
    
    messages.success(request, f'Ticket assigned to {target_user.username} successfully!')
    return redirect('frontend:ticket-detail', ticket_id=ticket_id)'''

new_function = '''@login_required
@require_http_methods(["POST"])
def ticket_assign_to_user(request, ticket_id, user_id):
    """
    Assign a ticket to a specific user.
    For IT_ADMIN, MANAGER, SUPERADMIN to assign to any user.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Get target user
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('frontend:ticket-detail', ticket_id=ticket_id)
    
    # Check permission using domain authority
    from apps.tickets.domain.services.ticket_authority import can_assign as can_assign_ticket
    if not can_assign_ticket(request.user, ticket, target_user):
        messages.error(request, 'You do not have permission to assign this ticket.')
        return redirect('frontend:ticket-detail', ticket_id=ticket_id)
    
    # Store old assignee for logging
    old_assignee = ticket.assigned_to
    old_assignee_name = old_assignee.username if old_assignee else None
    
    # Perform the assignment directly
    ticket.assigned_to = target_user
    ticket.assignment_status = 'ASSIGNED'
    ticket.updated_by = request.user
    ticket.save()
    
    # Emit domain event for activity logging
    from apps.tickets.domain.events import emit_ticket_assigned
    emit_ticket_assigned(
        ticket_id=ticket.id,
        ticket_title=ticket.title,
        actor=request.user,
        assignee_id=target_user.id,
        assignee_username=target_user.username,
        previous_assignee_id=old_assignee.id if old_assignee else None,
        previous_assignee_username=old_assignee_name,
    )
    
    messages.success(request, f'Ticket assigned to {target_user.username} successfully!')
    return redirect('frontend:ticket-detail', ticket_id=ticket_id)'''

# Apply the fix
if old_function in content:
    content = content.replace(old_function, new_function)
    with open(file_path, 'w') as f:
        f.write(content)
    print("Fixed! The User import has been added to ticket_assign_to_user function.")
else:
    print("Could not find the exact function to replace. The file may have already been modified.")
    print("Trying alternative fix...")
    
    # Alternative: just add the import at the start of the function
    alt_pattern = r'(@login_required\s+@require_http_methods\(\["POST"\]\)\s+def ticket_assign_to_user\(request, ticket_id, user_id\):)'
    alt_replacement = r'''\1
    from django.contrib.auth import get_user_model
    User = get_user_model()'''
    
    new_content = re.sub(alt_pattern, alt_replacement, content, flags=re.MULTILINE)
    if new_content != content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        print("Fixed using alternative method!")
    else:
        print("Could not apply alternative fix either.")
