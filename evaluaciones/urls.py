from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.principal, name='principal'),
    url(r'^$', views.LoginView.as_view(), name='login'),
    url(r'^empresas/crear', views.CrearEmpresa.as_view(), name='empresa.crear'),
]
