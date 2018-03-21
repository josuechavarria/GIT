# -*- coding: utf-8 -*-
from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()

@register.filter(name='getgroupName')
def getgroupName(value, splitter='|'):
    return value.split(splitter)[0]