"""
URL configuration for IT Management Platform.
Main URL configuration that includes API documentation and app URLs.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API endpoints
    path('api/auth/', include('apps.users.urls')),
    path('api/assets/', include('apps.assets.urls')),
    path('api/tickets/', include('apps.tickets.urls')),
    path('api/projects/', include('apps.projects.urls')),
    path('api/logs/', include('apps.logs.urls')),
    path('api/security/', include('apps.security.urls')),
    
    # Web interface (Django templates)
    path('', include('apps.frontend.urls')),  # Main frontend interface
    path('', include('apps.users.web_urls')),  # Web URLs for users
    path('', include('apps.assets.web_urls')),  # Web URLs for assets
    path('', include('apps.tickets.web_urls')),  # Web URLs for tickets
    path('', include('apps.projects.web_urls')),  # Web URLs for projects
    path('', include('apps.logs.web_urls')),  # Web URLs for logs
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin site configuration
admin.site.site_header = "IT Management Platform Administration"
admin.site.site_title = "IT Management Admin"
admin.site.index_title = "Welcome to IT Management Platform Admin"
