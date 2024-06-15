# custom_filters.py

from django import template

register = template.Library()

@register.filter
def calculate_subtotal(price, quantity):
    return price * quantity
