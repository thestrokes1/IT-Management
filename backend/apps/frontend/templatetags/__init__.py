# Template tags package for frontend app
default_app_config = 'apps.frontend.apps.FrontendConfig'

# Template tag libraries are automatically discovered by Django
# when the templatetags directory contains Python modules with @register decorators.
# Each module (menu_tags.py, custom_filters.py, etc.) registers its own tags/filters.

# Note: Do NOT import modules here as it can cause circular import issues.
# Django's template loader automatically discovers and loads template tag modules
# when they are referenced via {% load %} tags in templates.


