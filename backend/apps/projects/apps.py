"""
Projects app configuration.
"""

from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.projects'
    verbose_name = 'Projects & Tasks'
    description = 'Project and task management system'
    
    def ready(self):
        import apps.projects.signals

