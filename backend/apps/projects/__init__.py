"""
Projects app for IT Management Platform.
Project and task management system with role-based access control.
"""

from django.apps import AppConfig

class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.projects'
    verbose_name = 'Project Management'
    
    def ready(self):
        import apps.projects.signals
