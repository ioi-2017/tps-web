from django import template

register = template.Library()

@register.filter(name='privileged_get')
def privileged_get(d, k):
    return d[k]