from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.principal, name='principal'),
    url(r'^empresas/crear', views.CrearEmpresa.as_view(), name='empresa.crear'),
]
