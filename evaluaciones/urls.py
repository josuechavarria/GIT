from django.conf.urls import url
from django.views.generic import TemplateView
from evaluaciones.models import empresas,puestos
from . import views

urlpatterns = [
    url(r'^$', views.principal, name='principal'),
    #url(r'^$', views.LoginView.as_view(), name='login'),    
    url(r'^empresas/crear', views.CrearEmpresa.as_view(model= empresas), name='crear_empresa'),
    url(r'^empresas/actualizar/(?P<pk>\d+)/$', views.ActualizarEmpresa.as_view(model= empresas), name='actualiza_empresa'),
    url(r'^empresas/listar', views.ListarEmpresas.as_view(model= empresas), name='listar_empresa'),
    url(r'^puesto/crear', views.CrearPuesto.as_view(model=puestos,success_url="accounts/login"), name='puesto_create'),
]
