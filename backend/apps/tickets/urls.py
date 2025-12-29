"""
URL configuration for tickets app.
API and web endpoints for ticket management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.tickets.views import (
    TicketCategoryViewSet, TicketTypeViewSet, TicketViewSet,
    TicketCommentViewSet, TicketAttachmentViewSet, TicketTemplateViewSet,
    SLAViewSet, TicketEscalationViewSet, TicketSearchView
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'categories', TicketCategoryViewSet, basename='ticketcategory')
router.register(r'types', TicketTypeViewSet, basename='tickettype')
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'comments', TicketCommentViewSet, basename='ticketcomment')
router.register(r'attachments', TicketAttachmentViewSet, basename='ticketattachment')
router.register(r'templates', TicketTemplateViewSet, basename='tickettemplate')
router.register(r'slas', SLAViewSet, basename='sla')
router.register(r'escalations', TicketEscalationViewSet, basename='ticketescalation')

urlpatterns = [
    # API endpoints
    path('search/', TicketSearchView.as_view(), name='ticket-search'),
    
    # API router URLs
    path('', include(router.urls)),
]

# Web URLs for Django templates
web_urlpatterns = [
    # Web interface URLs
    path('tickets/', lambda request: None, name='web-ticket-list'),  # Placeholder
    path('tickets/create/', lambda request: None, name='web-ticket-create'),  # Placeholder
    path('tickets/<int:pk>/', lambda request: None, name='web-ticket-detail'),  # Placeholder
    path('tickets/<int:pk>/edit/', lambda request: None, name='web-ticket-edit'),  # Placeholder
    path('tickets/<int:pk>/assign/', lambda request: None, name='web-ticket-assign'),  # Placeholder
    path('tickets/<int:pk>/comments/', lambda request: None, name='web-ticket-comments'),  # Placeholder
    path('tickets/<int:pk>/attachments/', lambda request: None, name='web-ticket-attachments'),  # Placeholder
    path('tickets/<int:pk>/history/', lambda request: None, name='web-ticket-history'),  # Placeholder
    path('tickets/<int:pk>/escalations/', lambda request: None, name='web-ticket-escalations'),  # Placeholder
    path('tickets/<int:pk>/satisfaction/', lambda request: None, name='web-ticket-satisfaction'),  # Placeholder
    path('tickets/my-tickets/', lambda request: None, name='web-my-tickets'),  # Placeholder
    path('tickets/assigned/', lambda request: None, name='web-assigned-tickets'),  # Placeholder
    path('tickets/overdue/', lambda request: None, name='web-overdue-tickets'),  # Placeholder
    path('tickets/escalated/', lambda request: None, name='web-escalated-tickets'),  # Placeholder
    path('categories/', lambda request: None, name='web-ticket-category-list'),  # Placeholder
    path('categories/create/', lambda request: None, name='web-ticket-category-create'),  # Placeholder
    path('templates/', lambda request: None, name='web-ticket-template-list'),  # Placeholder
    path('templates/create/', lambda request: None, name='web-ticket-template-create'),  # Placeholder
    path('slas/', lambda request: None, name='web-sla-list'),  # Placeholder
    path('slas/create/', lambda request: None, name='web-sla-create'),  # Placeholder
]

# This will be imported as web_urls in config/urls.py
web_urls = web_urlpatterns
