# Tickets Fix TODO List

## Issues Fixed:

### 1. Fixed tickets.html - Null-safe created_by.username
- Changed `{{ ticket.created_by.username }}` to use conditional check: `{% if ticket.created_by %}{{ ticket.created_by.username }}{% else %}System{% endif %}`

### 2. Fixed create-ticket.html - Added ticket_type field
- Added ticket_type dropdown with ticket types from the context

### 3. Fixed CreateTicketView in views.py
- Added `requester = request.user` to set the requester field
- Fixed `due_date` to `sla_due_at` mapping with proper datetime parsing
- Added `ticket_type` handling (optional field)
- Added `ticket_types` to context in `get_context_data`

### 4. Updated TicketsView
- Added `ticket_type` to `select_related` query

## All Issues Resolved ✅

## Changes Summary:

1. **tickets.html**: Fixed template error when created_by is NULL
2. **create-ticket.html**: Added ticket_type dropdown field  
3. **views.py (CreateTicketView)**: 
   - Added ticket_type context variable
   - Fixed ticket creation to properly set requester, ticket_type, and sla_due_at
4. **views.py (TicketsView)**: Added ticket_type to select_related

