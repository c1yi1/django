from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """获取字典中的值"""
    if dictionary and isinstance(dictionary, dict) and key in dictionary:
        return dictionary[key]
    return None


