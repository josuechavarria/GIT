# -*- coding: utf-8 -*-
from django import template
from django.template.defaultfilters import stringfilter
from evaluaciones.models import *

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

@register.filter(name='totalCriterios')
def getTotalCriterios(empresa_id, puesto_id):
    return evaluaciones.objects.filter(empresa__pk=empresa_id,puesto__pk=puesto_id,estado=True,periodo__estado=True).count()

@register.filter(name='evaluacionDisponible')
def getevaluacionDisponible(empresa_id, usuario_id):
	objColaborador = colaboradores.objects.get(usuario__pk=usuario_id)
	return 1 if evaluaciones.objects.filter(empresa__pk=empresa_id,puesto=objColaborador.puesto,estado=True,periodo__estado=True).count()>0 else 0

@register.filter(name='evaluacionColaboradores')
def getevaluacionColaboradores(empresa_id, usuario_id):
	return evaluacion_colaborador.objects.filter(empresa__pk=empresa_id, colaborador__supervisor__usuario__pk=usuario_id, estado=True,periodo__estado=True).distinct('colaborador').count()
#cambio

