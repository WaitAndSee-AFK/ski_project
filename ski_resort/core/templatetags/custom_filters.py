from django import template

register = template.Library()

@register.filter
def get_by_id(queryset, id):
    try:
        return queryset.get(id=id)
    except:
        return None