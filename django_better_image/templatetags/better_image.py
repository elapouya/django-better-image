from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def better_image_dialogs(context):
    """Initialize app : add hidden dialogs to the page
    """

    out = render_to_string('django_better_image/crop_dialog.html',
                           context.flatten(), context.request)

    return mark_safe(out)