from django import template

register = template.Library()

@register.filter
def dict_key(dictionary, key):
    if dictionary is None:
        return {}
    return dictionary.get(key, {})

@register.filter
def dict_key_or_default(dictionary, args):
    if dictionary is None:
        return {}
    try:
        key, default = args.split(",")
        key = key.strip()
        default = default.strip()
    except ValueError:
        raise ValueError("dict_key_or_default requires two arguments separated by a comma.")
    
    return dictionary.get(key, default)

@register.filter
def get_by_id(queryset, pk):
    try:
        return queryset.get(pk=pk)
    except queryset.model.DoesNotExist:
        return None