from django import template
from django.template import TemplateSyntaxError
import six

register = template.Library()


def _generate_context(objects_list, *args):
    def rgetattr(obj, full_attr):
        seperated_attrs = full_attr.split(".")
        result_object = obj
        for attr in seperated_attrs:
            result_object = getattr(result_object, attr)
        return result_object

    for arg in args:
        if not isinstance(arg, six.string_types):
            raise TemplateSyntaxError("except the first argument, all arguments must be a string")
    if len(objects_list) == 0:
        return {}
    titles = []
    obj = objects_list[0]
    for arg in args:
        titles.append(obj._meta.get_field(arg).verbose_name.title())

    objects_data = {}
    for obj in objects_list:
        current_obj_data = []
        for arg in args:
            current_obj_data.append(rgetattr(obj, arg))
        objects_data[obj] = current_obj_data

    return {
        'titles': titles,
        'data': objects_data,
    }

@register.inclusion_tag("fragments/deletable_object_list.html")
def generate_deletable_object_list(objects_list, *args):
    return _generate_context(objects_list, *args)