# TODO: Create Dedicated Edit Pages for Projects and Tickets

## Phase 1: Create Edit Project Page
- [ ] 1.1 Create `edit-project.html` template with all project fields
- [ ] 1.2 Add `EditProjectView` class in `views.py`
- [ ] 1.3 Add URL pattern `projects/<int:project_id>/edit/` in `urls.py`
- [ ] 1.4 Update `projects.html` to link to edit page instead of modal

## Phase 2: Create Edit Ticket Page
- [ ] 2.1 Create `edit-ticket.html` template with all ticket fields
- [ ] 2.2 Add `EditTicketView` class in `views.py`
- [ ] 2.3 Add URL pattern `tickets/<int:ticket_id>/edit/` in `urls.py`
- [ ] 2.4 Update `tickets.html` to link to edit page instead of modal

## Phase 3: Cleanup
- [ ] 3.1 Remove inline edit modals from `projects.html`
- [ ] 3.2 Remove inline edit modals from `tickets.html`
- [ ] 3.3 Clean up unused JavaScript functions

