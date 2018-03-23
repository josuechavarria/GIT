from django.conf.urls import url
from django.views.generic import TemplateView
from evaluaciones.models import *
from django.core.urlresolvers import reverse_lazy
from . import views

urlpatterns = [
    url(r'^$', views.principal, name='principal'),
    url(r'^login/$', views.LoginView.as_view(), name='login'), 
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),    
    url(r'^empresas/(?P<pk>\d+)/$', views.IndexEmpresaView.as_view(), name='principal_empresa'),
    url(r'^empresas/crear/$', views.CrearEmpresa.as_view(model= empresas), name='crear_empresa'),
    url(r'^empresas/actualizar/(?P<pk>\d+)/$', views.ActualizarEmpresa.as_view(model= empresas), name='actualiza_empresa'),
    url(r'^empresas/listar', views.ListarEmpresas.as_view(model= empresas), name='listar_empresa'),
    url(r'^puesto/crear/(?P<pk>\d+)/$', views.CrearPuesto.as_view(model=puestos), name='crear_puesto'),
    url(r'^puesto/actualizar/(?P<pk>\d+)/(?P<id>\d+)/$', views.ActualizarPuesto.as_view(model= puestos), name='actualiza_puesto'),
    url(r'^puesto/listar/(?P<pk>\d+)/$',views.ListarPuestos.as_view(model=puestos), name='listar_puesto'),
    url(r'^puesto/borrar/(?P<pk>\d+)/(?P<id>\d+)/$',views.BorrarPuesto.as_view(model=puestos), name='borrar_puesto'),
    url(r'^departamento/crear/(?P<pk>\d+)/$', views.CrearDepartamento.as_view(model=departamentos), name='crear_departamento'),
    url(r'^departamento/actualizar/(?P<pk>\d+)/(?P<id>\d+)/$', views.ActualizarDepartamento.as_view(model= departamentos), name='actualiza_departamento'),
    url(r'^departamento/listar/(?P<pk>\d+)/$', views.ListarDepartamentos.as_view(model= departamentos), name='listar_departamento'),
    url(r'^sucursal/crear/(?P<pk>\d+)/$', views.CrearSucursal.as_view(model=sucursales), name='crear_sucursal'),
    url(r'^sucursal/actualizar/(?P<pk>\d+)/(?P<id>\d+)/$', views.ActualizarSucursal.as_view(model= sucursales), name='actualiza_sucursal'),
    url(r'^sucursal/listar/(?P<pk>\d+)/$', views.ListarSucursales.as_view(model= sucursales), name='listar_sucursal'),
    url(r'^roles/listar/(?P<pk>\d+)/$', views.RolesView.as_view(), name='listar_roles'),
    url(r'^roles/nuevo/(?P<pk>\d+)/$', views.RolesNuevoView.as_view(), name='crear_roles'),
    url(r'^criterio/crear/(?P<pk>\d+)/$', views.CrearCriterio.as_view(model=criterios), name='crear_criterio'),
    url(r'^criterio/listar/(?P<pk>\d+)/$',
        views.ListarCriterios.as_view(), name='listar_criterios'),
    url(r'^periodo/crear/(?P<pk>\d+)/$', views.CrearPeriodos.as_view(model=periodos), name='crear_periodo'),
    url(r'^periodo/listar/(?P<pk>\d+)/$', views.ListarPeriodos.as_view(model=periodos), name='listar_periodos'),
    url(r'^objetivo/crear/(?P<pk>\d+)/$', views.CrearObjetivos.as_view(model=objetivos), name='crear_objetivos'),
    url(r'^objetivos/listar/(?P<pk>\d+)/$', views.ListarObjetivos.as_view(), name='listar_objetivos'),
    url(r'^objetivos/actualizar/(?P<pk>\d+)/(?P<id>\d+)/$',
        views.ActualizarObjetivos.as_view(model=objetivos), name='actualizar_objetivos'),
    url(r'^tipoPeriodicidad/crear/', views.CreartipoPeriodicidad.as_view(model=tipoperiodicidad), name='crear_tipoperiodicidad'),
]
