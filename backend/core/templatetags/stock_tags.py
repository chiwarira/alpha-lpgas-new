from django import template

register = template.Library()


@register.filter
def dict_get(d, key):
    """Look up `key` in a dict (works with model instances as keys)."""
    if d is None:
        return 0
    return d.get(key, 0)


@register.filter
def signed(value):
    """Format an integer with an explicit sign, e.g. +3 / -2 / 0."""
    try:
        value = int(value)
    except (TypeError, ValueError):
        return value
    return f"+{value}" if value > 0 else str(value)
