"""Web URLs for tickets app - HTML template views (not API)"""
from django.urls import path
from . import web_views

app_name = 'tickets'

urlpatterns = [
    # Ticket detail page (READ-ONLY internal view)
    path(
        'tickets/<uuid:ticket_id>/',
        web_views.TicketDetailView.as_view(),
        name='ticket_detail'
    ),
]

