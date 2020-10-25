from django import template

register = template.Library()


@register.filter
def keyvalue(dictionary, key):
    return dictionary[key]
