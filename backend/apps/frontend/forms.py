from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, Div, HTML

from apps.tickets.models import Ticket, TicketCategory, TicketType
from apps.users.models import User

class TicketForm(forms.Form):
    title = forms.CharField(max_length=255, required=True, label="Ticket Title")
    category = forms.ModelChoiceField(
        queryset=TicketCategory.objects.filter(is_active=True), 
        required=True,
        empty_label="Select a category"
    )
    ticket_type = forms.ModelChoiceField(
        queryset=TicketType.objects.filter(is_active=True), 
        required=False,
        empty_label="Select a ticket type (optional)"
    )
    priority = forms.ChoiceField(choices=Ticket.PRIORITY_CHOICES, required=True)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 6}), required=True, label="Detailed Description")
    
    impact = forms.ChoiceField(choices=[('', 'Select impact level')] + list(Ticket.IMPACT_CHOICES), required=False)
    urgency = forms.ChoiceField(choices=[('', 'Select urgency level')] + list(Ticket.URGENCY_CHOICES), required=False)
    
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(), 
        required=False,
        empty_label="Unassigned"
    )
    due_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=False)
    
    contact_type = forms.ChoiceField(choices=[('', 'Select contact type')] + list(Ticket.CONTACT_TYPE_CHOICES), required=False)
    contact_email = forms.EmailField(required=False)
    contact_phone = forms.CharField(max_length=50, required=False)
    location = forms.CharField(max_length=255, required=False)

    def __init__(self, *args, **kwargs):
        available_users = kwargs.pop('available_users', None)
        is_edit = kwargs.pop('is_edit', False)
        super().__init__(*args, **kwargs)
        
        if available_users is not None:
            self.fields['assigned_to'].queryset = available_users
            
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        # Override crispy internal spacing for Tailwind CSS Grid
        self.helper.layout = Layout(
            Fieldset(
                'Basic Information',
                'title',
                Row(
                    Column('category', css_class='col-span-1'),
                    Column('ticket_type', css_class='col-span-1'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
                ),
                'priority'
            ),
            Fieldset(
                'Description',
                'description'
            ),
            Fieldset(
                'Additional Information',
                Row(
                    Column('impact', css_class='col-span-1'),
                    Column('urgency', css_class='col-span-1'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
                ),
                Row(
                    Column('assigned_to', css_class='col-span-1'),
                    Column('due_date', css_class='col-span-1'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
                )
            ),
            Fieldset(
                'Contact Information',
                Row(
                    Column('contact_type', css_class='col-span-1'),
                    Column('contact_email', css_class='col-span-1'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
                ),
                Row(
                    Column('contact_phone', css_class='col-span-1'),
                    Column('location', css_class='col-span-1'),
                    css_class='grid grid-cols-1 md:grid-cols-2 gap-4'
                )
            ),
            Div(
                HTML('<a href="{% url \'frontend:tickets\' %}" class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition duration-150"><i class="fas fa-arrow-left mr-2"></i>Cancel</a>'),
                Submit('submit', 'Update Ticket' if is_edit else 'Create Ticket', css_class='inline-flex items-center px-6 py-2 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150'),
                css_class='flex items-center justify-between pt-8 mt-6 border-t border-gray-200'
            )
        )
