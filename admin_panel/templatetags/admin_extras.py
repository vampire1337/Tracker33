from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    """Добавляет CSS-класс к виджету формы"""
    if 'class' in value.field.widget.attrs:
        value.field.widget.attrs['class'] += f' {arg}'
    else:
        value.field.widget.attrs['class'] = arg
    return value 