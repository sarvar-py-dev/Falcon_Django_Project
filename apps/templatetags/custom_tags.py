from django import template

from apps.models.product import Favorite

register = template.Library()


@register.filter(name='custom_range')
def custom_range(value):
    return range(value)


@register.filter()
def str_to_phone(value, arg=None):
    if value.startswith('+998'):
        return value
    return f'+998{value}'


@register.filter()
def is_liked(user, product) -> bool:
    return Favorite.objects.filter(user=user, product=product).exists()


@register.filter()
def total(sub_total, shipping_cost):
    return sub_total + shipping_cost


@register.filter()
def get_obj_in_list(l, index):
    return l[index]
