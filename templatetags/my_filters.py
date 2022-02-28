from django import template

register = template.Library()
@register.filter(name='times') 
def times(number):
    return [i+1 for i in range(number)]