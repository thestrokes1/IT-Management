"""
Web URL configuration for logs app.
Used for Django templates (non-API views).
"""

from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    path(
        'logs/',
        TemplateView.as_view(template_name='frontend/logs.html'),
        name='web-log-list',
    ),
    path(
        'logs/activity/',
        TemplateView.as_view(template_name='frontend/logs.html'),
        name='web-activity-log-list',
    ),
    path(
        'logs/audit/',
        TemplateView.as_view(template_name='frontend/logs.html'),
        name='web-audit-log-list',
    ),
    path(
        'logs/security/',
        TemplateView.as_view(template_name='frontend/logs.html'),
        name='web-security-event-list',
    ),
    path(
        'logs/system/',
        TemplateView.as_view(template_name='frontend/logs.html'),
        name='web-system-log-list',
    ),
    path(
        'logs/dashboard/',
        TemplateView.as_view(template_name='frontend/logs.html'),
        name='web-log-dashboard',
    ),
    path(
        'logs/alerts/',
        TemplateView.as_view(template_name='frontend/logs.html'),
        name='web-log-alert-list',
    ),
    path(
        'logs/reports/',
        TemplateView.as_view(template_name='frontend/logs.html'),
        name='web-log-report-list',
    ),
    path(
        'logs/export/',
        TemplateView.as_view(template_name='frontend/logs.html'),
        name='web-log-export',
    ),
]
