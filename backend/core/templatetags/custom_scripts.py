from django import template
from django.utils.safestring import mark_safe
from core.models import CustomScript

register = template.Library()


@register.simple_tag(takes_context=True)
def render_custom_scripts(context, position):
    """
    Render custom scripts for a specific position.
    
    Usage in templates:
        {% load custom_scripts %}
        {% render_custom_scripts 'head_start' %}
        {% render_custom_scripts 'head_end' %}
        {% render_custom_scripts 'body_start' %}
        {% render_custom_scripts 'body_end' %}
        {% render_custom_scripts 'footer' %}
    """
    request = context.get('request')
    if not request:
        return ''
    
    current_path = request.path
    
    # Get all active scripts for this position
    scripts = CustomScript.objects.filter(
        position=position,
        is_active=True
    ).order_by('order', 'name')
    
    # Filter scripts based on page targeting
    output = []
    for script in scripts:
        if script.should_display_on_page(current_path):
            output.append(script.script_code)
    
    # Join all scripts with newlines and mark as safe HTML
    return mark_safe('\n'.join(output))


@register.simple_tag(takes_context=True)
def has_custom_scripts(context, position):
    """
    Check if there are any active scripts for a specific position.
    Useful for conditional rendering.
    
    Usage:
        {% if has_custom_scripts 'head_end' %}
            <!-- Scripts will be rendered -->
        {% endif %}
    """
    request = context.get('request')
    if not request:
        return False
    
    current_path = request.path
    
    scripts = CustomScript.objects.filter(
        position=position,
        is_active=True
    )
    
    for script in scripts:
        if script.should_display_on_page(current_path):
            return True
    
    return False
