from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

# Also register as 'get' for compatibility with existing templates
register.filter('get', get_item)
