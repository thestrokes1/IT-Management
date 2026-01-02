# TODO: Replace prompt() with Modal Dialogs

## Objective
Replace JavaScript `prompt()` dialogs with proper modal dialogs for editing projects and tickets.

## Files Modified
- [ ] `templates/frontend/projects.html` - Replace `editProject()` with modal
- [ ] `templates/frontend/tickets.html` - Replace `editTicket()` with modal

## Changes

### projects.html
- [ ] 1. Add Edit Project modal with name and description fields
- [ ] 2. Update `editProject()` function to open modal with current values
- [ ] 3. Add form submission handler for the modal
- [ ] 4. Test edit functionality

### tickets.html
- [ ] 1. Add Edit Ticket modal with title and description fields
- [ ] 2. Update `editTicket()` function to open modal with current values
- [ ] 3. Add form submission handler for the modal
- [ ] 4. Test edit functionality

## Technical Implementation

### Modal Structure (for both files)
```html
<div id="edit-modal" class="hidden fixed inset-0 z-50 overflow-y-auto">
    <div class="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 transition-opacity" aria-hidden="true">
            <div class="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>
        <div class="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
            <form id="edit-form">
                <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Edit Item</h3>
                <!-- Form fields here -->
                <div class="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                    <button type="submit" class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 sm:col-start-2">Save</button>
                    <button type="button" onclick="hideEditModal()" class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 sm:mt-0 sm:col-start-1">Cancel</button>
                </div>
            </form>
        </div>
    </div>
</div>
```

## Status
- [x] Plan created and approved
- [x] TODO file created
- [x] Implementing projects.html modal
- [x] Implementing tickets.html modal
- [ ] Testing
- [ ] Completed

