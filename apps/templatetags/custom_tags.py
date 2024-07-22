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
    if user.is_anonymous:
        return False
    return Favorite.objects.filter(user=user, product=product).exists()


@register.filter()
def get_obj_in_list(l, index):
    return l[index]


@register.filter()
def get_last_chars(value, arg):
    return value[len(value) - arg:]


@register.filter()
def create_tax_sum(total_sum, tax):
    return total_sum // tax
