# -*- coding: utf-8 -*-
from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()

@register.filter(name='getgroupName')
def getgroupName(value, splitter='|'):
    return value.split(splitter)[0]

@register.filter(name='addcss')
def addcss(field, args):
    if args is None:
        return False
    arg_list = [arg.strip() for arg in args.split(',')]
    return field.as_widget(attrs={"%s" % arg.split(':')[0] : arg.split(':')[1] for arg in arg_list })