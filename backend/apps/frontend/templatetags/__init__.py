# Template tags package for frontend app
default_app_config = 'apps.frontend.apps.FrontendConfig'

# Explicitly load template tags to register them with Django
from . import menu_tags
from . import menu_permissions
from . import dict_extras


