# -*- coding: utf-8 -*-
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter(name='getgroupName')
def getgroupName(str):
    return str.split(splitter)
    return str[0]