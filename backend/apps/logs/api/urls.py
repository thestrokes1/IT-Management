"""
Activity Timeline API URLs.

URL configuration for Activity Timeline endpoints.
"""

from django.urls import path
from apps.logs.api import views


app_name = 'logs'


urlpatterns = [
    # Activity Timeline endpoints
    path(
        'activity-timeline/',
        views.ActivityTimelineAPIView.as_view(),
        name='activity-timeline'
    ),
    path(
        'activity-timeline/statistics/',
        views.ActivityStatisticsAPIView.as_view(),
        name='activity-timeline-statistics'
    ),
    path(
        'activity-timeline/<uuid:log_id>/',
        views.ActivityTimelineDetailAPIView.as_view(),
        name='activity-timeline-detail'
    ),
    path(
        'activity-timeline/entity/<str:entity_type>/<int:entity_id>/',
        views.EntityActivityAPIView.as_view(),
        name='entity-activity'
    ),
    
    # Function-based view aliases (for backward compatibility)
    path(
        'activity-timeline/simple/',
        views.activity_timeline_view,
        name='activity-timeline-simple'
    ),
    path(
        'activity-timeline/statistics/simple/',
        views.activity_statistics_view,
        name='activity-timeline-statistics-simple'
    ),
]

