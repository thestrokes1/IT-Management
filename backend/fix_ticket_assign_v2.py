"""
Complete fix for ticket assignment error.
This script updates events.py to accept previous_assignee parameters.
"""

import os

# Get the backend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
events_file = os.path.join(BASE_DIR, 'apps/tickets/domain/events.py')

print(f"Reading: {events_file}")

with open(events_file, 'r') as f:
    content = f.read()

# Update TicketAssigned dataclass
old_class = '''@dataclass
class TicketAssigned(TicketEvent):
    """Event fired when a ticket is assigned."""
    event_type: str = TicketEventType.TICKET_ASSIGNED
    assignee_id: Optional[int] = None
    assignee_username: str = ''
    assigner_id: Optional[int] = None
    assigner_username: str = ''
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata = {
            'assignee_id': self.assignee_id,
            'assignee_username': self.assignee_username,
            'assigner_id': self.assigner_id,
            'assigner_username': self.assigner_username,
        }'''

new_class = '''@dataclass
class TicketAssigned(TicketEvent):
    """Event fired when a ticket is assigned."""
    event_type: str = TicketEventType.TICKET_ASSIGNED
    assignee_id: Optional[int] = None
    assignee_username: str = ''
    assigner_id: Optional[int] = None
    assigner_username: str = ''
    previous_assignee_id: Optional[int] = None
    previous_assignee_username: str = ''
    
    def __post_init__(self):
        super().__post_init__()
        self.metadata = {
            'assignee_id': self.assignee_id,
            'assignee_username': self.assignee_username,
            'assigner_id': self.assigner_id,
            'assigner_username': self.assigner_username,
            'previous_assignee_id': self.previous_assignee_id,
            'previous_assignee_username': self.previous_assignee_username,
        }'''

if old_class in content:
    content = content.replace(old_class, new_class)
    print("Updated TicketAssigned dataclass in events.py")
else:
    print("TicketAssigned dataclass not found (may already be updated)")

# Update emit_ticket_assigned function
old_func = '''def emit_ticket_assigned(
    ticket_id: int,
    ticket_title: str,
    actor: Any,
    assignee_id: Optional[int],
    assignee_username: str,
    assigner_id: Optional[int] = None,
    assigner_username: str = ''
) -> None:
    """Emit a ticket assigned event."""
    event = TicketAssigned(
        ticket_id=ticket_id,
        ticket_title=ticket_title,
        actor=actor,
        assignee_id=assignee_id,
        assignee_username=assignee_username,
        assigner_id=assigner_id or (actor.id if actor else None),
        assigner_username=assigner_username or (actor.username if actor else ''),
    )
    EventDispatcher().dispatch(event)'''

new_func = '''def emit_ticket_assigned(
    ticket_id: int,
    ticket_title: str,
    actor: Any,
    assignee_id: Optional[int],
    assignee_username: str,
    assigner_id: Optional[int] = None,
    assigner_username: str = '',
    previous_assignee_id: Optional[int] = None,
    previous_assignee_username: str = ''
) -> None:
    """Emit a ticket assigned event."""
    event = TicketAssigned(
        ticket_id=ticket_id,
        ticket_title=ticket_title,
        actor=actor,
        assignee_id=assignee_id,
        assignee_username=assignee_username,
        assigner_id=assigner_id or (actor.id if actor else None),
        assigner_username=assigner_username or (actor.username if actor else ''),
        previous_assignee_id=previous_assignee_id,
        previous_assignee_username=previous_assignee_username,
    )
    EventDispatcher().dispatch(event)'''

if old_func in content:
    content = content.replace(old_func, new_func)
    print("Updated emit_ticket_assigned function in events.py")
else:
    print("emit_ticket_assigned function not found (may already be updated)")

with open(events_file, 'w') as f:
    f.write(content)

print("\n=== Fix applied successfully! ===")
print("Restart the Django server and test ticket assignment again.")
