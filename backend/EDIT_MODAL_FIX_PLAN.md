# Edit Modal Fix Plan

## Problem Analysis

The edit modals in `projects.html` and `tickets.html` are not appearing because:
1. The edit modals are defined at the bottom of each page with their own `fixed inset-0` positioning
2. They try to show using `modal-overlay` from base.html, but they're NOT children of that overlay
3. The `modal-overlay` div in base.html is empty when showing edit modals, causing them to be hidden behind it

## Working Pattern Reference

In `users.html` and `assets.html`:
- Edit links navigate to separate pages: `{% url 'frontend:edit_user' user.id %}`
- No inline modals, uses separate edit page for form

## Solution Plan

### Step 1: Update base.html
Add the edit modals for projects and tickets INSIDE the modal-overlay div:
- Add `edit-project-modal` inside modal-overlay
- Add `edit-ticket-modal` inside modal-overlay
- Use the existing `showModal(modalId)` and `hideModal(modalId)` functions

### Step 2: Update projects.html
1. Remove the inline edit-project-modal HTML (moved to base.html)
2. Remove the `editProject()` and `hideEditProjectModal()` functions
3. Remove the form submission handler for edit-project-form
4. Update the Edit link to call a simple `editProject()` function that uses showModal()

### Step 3: Update tickets.html
1. Remove the inline edit-ticket-modal HTML (moved to base.html)
2. Remove the `editTicket()` and `hideEditTicketModal()` functions  
3. Remove the form submission handler for edit-ticket-form
4. Update the Edit link to call a simple `editTicket()` function that uses showModal()

## Implementation Details

### JavaScript Functions (in each page)

```javascript
function editProject(projectId, projectName, projectDesc) {
    document.getElementById('edit-project-id').value = projectId;
    document.getElementById('edit-project-name').value = projectName;
    document.getElementById('edit-project-description').value = projectDesc || '';
    showModal('edit-project-modal');
}
```

### Modal HTML Structure (in base.html)

The modals should be placed inside the existing modal-overlay div in base.html:

```html
<div id="modal-overlay" class="fixed inset-0 bg-gray-600 bg-opacity-50 z-50 hidden">
    <!-- Create Ticket Modal (already exists) -->
    <div id="create-ticket-modal" class="hidden ...">...</div>
    
    <!-- NEW: Edit Project Modal -->
    <div id="edit-project-modal" class="hidden fixed inset-0 z-50 overflow-y-auto">
        <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div class="fixed inset-0 transition-opacity" aria-hidden="true">
                <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <div class="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
                <form id="edit-project-form">...</form>
            </div>
        </div>
    </div>
    
    <!-- NEW: Edit Ticket Modal -->
    <div id="edit-ticket-modal" class="hidden fixed inset-0 z-50 overflow-y-auto">
        ...
    </div>
</div>
```

## Files to Modify

1. `templates/frontend/base.html` - Add edit modals inside modal-overlay
2. `templates/frontend/projects.html` - Remove inline modal, simplify JS
3. `templates/frontend/tickets.html` - Remove inline modal, simplify JS

## Follow-up Steps

1. Test edit modal functionality in projects page
2. Test edit modal functionality in tickets page
3. Verify existing create-ticket modal still works
4. Update TODO_replace_prompt_modals.md to mark as completed

