from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.generic import View, TemplateView,CreateView, ListView, UpdateView,DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from braces.views import FormInvalidMessageMixin

from evaluaciones.models import *
from evaluaciones.forms import *

def home(request):
    numbers = [1,2,3,4,5]
    name = 'Hector Machuca'
    args = {'name' :name, 'numbers': numbers}
    return render(request, 'evaluaciones/landing.html',args)

def principal(request):
    return render(request,'evaluaciones/principal.html')

class RolesView(View):	
	def get(self, request, pk=None):
		template_name = "evaluaciones/roles_list.html"
		ctx = {'grupos': Group.objects.filter(name__endswith=u'_%s' % (pk)),
		'empresa' : empresas.objects.get(pk=pk)
		}
		return render_to_response(template_name, ctx)
   
	def post(self, request):
		print("hola post")


class IndexEmpresaView(View):
	def get(self, request, pk=None):
		template_name = "evaluaciones/index_empresa.html"
		ctx={'empresa': empresas.objects.get(pk=pk)}
		return render(request,template_name,ctx)

## Vistas para la creación
class CrearEmpresa(SuccessMessageMixin,CreateView):
	model = empresas
	form_class = empresasForm
	template_name = "evaluaciones/crearEmpresa.html"
	#success_url = reverse_lazy('evaluaciones:crear_empresa')
	success_message = "Empresa creada satisfactoriamente."
	error_message = "La empresa no se pudo crear, inténtelo nuevamente."

	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_empresa')
		else:
			url = reverse_lazy('evaluaciones:listar_empresa')
		return url

# Vistas para la actualización
class ActualizarEmpresa(SuccessMessageMixin,UpdateView):
	model = empresas
	form_class = empresasFormEdit
	template_name = "evaluaciones/ActualizaEmpresa.html"
	success_message = "Empresa actualizada satisfactoriamente."
	error_message = "La empresa no se pudo actualizar, inténtelo nuevamente."
	
	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_empresa')
		else:
			url = reverse_lazy('evaluaciones:listar_empresa')
		return url
	#fields = ['nombre', 'rtn', 'direccion', 'otros_datos']
#Listas, tablas
class ListarEmpresas(ListView):	
	model = empresas
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['now'] = timezone.now()
		print(context)
		return context

class CrearPuesto(SuccessMessageMixin,FormInvalidMessageMixin,CreateView):
	model = puestos
	form_class = puestosForm
	template_name = "evaluaciones/crearpuesto.html"
	success_message = "Puesto creado satisfactoriamente."
	form_invalid_message = 'Error al crear el puesto por favor revise los datos'
	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_puesto', args=[self.kwargs['pk']])
		else:
			url = reverse_lazy('evaluaciones:listar_puesto', args=[self.kwargs['pk']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context

# Vistas para la actualización
class ActualizarPuesto(SuccessMessageMixin,FormInvalidMessageMixin,UpdateView):
	model = puestos
	form_class = puestosForm
	template_name = "evaluaciones/ActualizaPuesto.html"
	success_message = "Puesto actualizado satisfactoriamente."
	form_invalid_message = 'Error al Actualizar el puesto  por favor revise los datos'
	
	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_puesto', args=[self.kwargs['id']])
		else:
			url = reverse_lazy('evaluaciones:listar_puesto', args=[self.kwargs['id']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context

class ListarPuestos(ListView):	
	model = puestos	
	print(model)
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context

class BorrarPuesto(DeleteView):
	model = puestos
	success_url = reverse_lazy('listar_puesto')
	def get_context_data(self, **kwargs):
			context = super().get_context_data(**kwargs)
			context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
			return context


class CrearDepartamento(SuccessMessageMixin,CreateView):
	model = departamentos
	form_class = DepartamentosForm
	template_name = "evaluaciones/crearDepartamento.html"
	success_message = "Departamento creado satisfactoriamente."
	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_departamento', args=[self.kwargs['pk']])
		else:
			url = reverse_lazy('evaluaciones:listar_departamento', args=[self.kwargs['pk']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context

# Vistas para la actualización
class ActualizarDepartamento(SuccessMessageMixin,UpdateView):
	model = departamentos
	form_class = DepartamentosForm
	template_name = "evaluaciones/ActualizaDepartamento.html"
	success_message = "Departamento actualizado satisfactoriamente."
	error_message = "El Departamento no se pudo actualizar, inténtelo nuevamente."
	
	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_departamento', args=[self.kwargs['id']])
		else:
			url = reverse_lazy('evaluaciones:listar_departamento', args=[self.kwargs['id']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context

class ListarDepartamentos(ListView):	
	model = departamentos
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context

class CrearSucursal(SuccessMessageMixin,CreateView):
	model = sucursales
	form_class = SucursalesForm
	template_name = "evaluaciones/crearSucursal.html"
	success_message = "Sucursal creado satisfactoriamente."
	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_sucursal', args=[self.kwargs['pk']])
		else:
			url = reverse_lazy('evaluaciones:listar_sucursal', args=[self.kwargs['pk']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context

# Vistas para la actualización
class ActualizarSucursal(SuccessMessageMixin,UpdateView):
	model = sucursales
	form_class = SucursalesForm
	template_name = "evaluaciones/ActualizaSucursal.html"
	success_message = "Sucursal actualizado satisfactoriamente."
	error_message = "La Sucursal no se pudo actualizar, inténtelo nuevamente."
	
	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_sucursal', args=[self.kwargs['id']])
		else:
			url = reverse_lazy('evaluaciones:listar_sucursal', args=[self.kwargs['id']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context

class ListarSucursales(ListView):	
	model = sucursales
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context

class IndexView(View):
	def get(self, request):
		template_name = "evaluaciones/landing.html"
		ctx={'s':'s'}
		return render_to_response(template_name,ctx)

class LoginView(View):	
	def get(self, request):
		if request.user.is_authenticated():
			return HttpResponseRedirect(reverse('evaluaciones:principal'))
		form = LoginForm()
		ctx = {'form':form}
		return render_to_response('login.html', ctx, context_instance=RequestContext(request))
   
	def post(self, request):
		print("hola post")
		print(request.POST)
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username=username, password=password)
		print (username)
		print (password)
		if user is not None:
			if user.is_active:
				login(request, user)
				return HttpResponseRedirect(reverse('evaluaciones:principal'))
			else:
				messages.error(request, 'Usuario Inactivo')
				return HttpResponseRedirect(reverse('evaluaciones:login'))
		else:
			# Mensaje Incorrecto
			print("hola invalidaos")
			messages.error(request, 'Correo o contraseña inválidos')
			return HttpResponseRedirect(reverse('login'))

class LogoutView(View):
	def get(self, request):
		logout(request)
		return HttpResponseRedirect('/accounts/login/')

# Criterios
class CrearCriterio(SuccessMessageMixin,CreateView):
	model = criterios
	form_class = CriteriosForm
	template_name = "evaluaciones/CrearCriterio.html"
	success_message = "Criterio creado satisfactoriamente."
	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_criterio', args=[self.kwargs['pk']])
		else:
			url = reverse_lazy('evaluaciones:listar_criterio', args=[self.kwargs['pk']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context

class ListarCriterios(ListView):	
	model = criterios	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context

# Periodos
class CrearPeriodos(SuccessMessageMixin,CreateView):
	model = periodos
	form_class = PeriodosForm
	template_name = "evaluaciones/CrearPeriodo.html"
	success_message = "Periodo creado satisfactoriamente."
	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_periodo', args=[self.kwargs['pk']])
		else:
			url = reverse_lazy('evaluaciones:listar_periodo', args=[self.kwargs['pk']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context
## OBJETIVOS
## Creación de Objetivos	
class CrearObjetivos(SuccessMessageMixin,CreateView):
	model = objetivos
	form_class = objetivosForm
	template_name = "evaluaciones/crearObjetivo.html"
	success_message = "Objetivo creado satisfactoriamente."
	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_objetivos', args=[self.kwargs['pk']])
		else:
			url = reverse_lazy('evaluaciones:listar_objetivos', args=[self.kwargs['pk']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context

## Listar Objetivos
class ListarObjetivos(ListView):	
	model = objetivos
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context
# Actualizar Objetivos
class ActualizarObjetivos(SuccessMessageMixin,UpdateView):
	model = objetivos
	form_class = objetivosFormEdit
	template_name = "evaluaciones/ActualizaObjetivo.html"
	success_message = "Empresa actualizada satisfactoriamente."
	error_message = "La empresa no se pudo actualizar, inténtelo nuevamente."
	
	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_objetivos',args=[self.kwargs['id']])
		else:
			url = reverse_lazy('evaluaciones:listar_objetivos', args=[self.kwargs['id']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context
	#fields = ['nombre', 'rtn', 'direccion', 'otros_datos']
#Listas, tablas
