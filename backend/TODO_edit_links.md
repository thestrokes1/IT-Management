# TODO: Update Edit Links from Modal to Direct Pages

## Task
Change edit buttons from modal-based to direct page links for projects and tickets.

## Changes Required:

### 1. projects.html
- [x] Change edit button to use `{% url 'frontend:edit_project' project.id %}`
- [x] Remove `editProject()` JavaScript function
- [x] Remove related modal code

### 2. tickets.html
- [x] Change edit button to use `{% url 'frontend:edit_ticket' ticket.id %}`
- [x] Remove `editTicket()` JavaScript function
- [x] Remove related modal code

### 3. Keep Unchanged
- edit-project.html (already functional)
- edit-ticket.html (already functional)
- create-project.html (no changes)
- create-ticket.html (no changes)

## Status: COMPLETED

