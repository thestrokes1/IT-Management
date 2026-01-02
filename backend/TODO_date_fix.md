# Date Comparison Fix - TODO List

## Objective
Fix the runtime error: "> not supported between instances of 'datetime.date' and 'str'" when saving/editing projects.

## Issues Identified
1. Date fields from frontend forms are passed as strings
2. String dates are compared with datetime.date objects in validators
3. Comparison in `Project.is_overdue` property and serializer validation

## Fix Plan
- [ ] Fix CreateProjectView.post() - Convert date strings to datetime.date objects
- [ ] Fix EditProjectView.post() - Convert date strings to datetime.date objects  
- [ ] Fix ProjectCreateSerializer.validate() - Ensure proper date validation
- [ ] Fix ProjectUpdateSerializer.validate() - Ensure proper date validation
- [ ] Verify the fix works

## Files to Modify
1. `it_management_platform/backend/apps/frontend/views.py`
2. `it_management_platform/backend/apps/projects/serializers.py`

## Implementation Details
- Use `datetime.strptime(date_string, '%Y-%m-%d').date()` to convert strings
- Handle empty strings by setting None
- Preserve existing validation logic
