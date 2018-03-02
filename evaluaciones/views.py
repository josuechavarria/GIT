from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.generic import View, TemplateView,CreateView, ListView, UpdateView
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.utils import timezone

from evaluaciones.models import empresas, puestos
from evaluaciones.forms import empresasForm, puestosForm

def home(request):
    numbers = [1,2,3,4,5]
    name = 'Hector Machuca'
    args = {'name' :name, 'numbers': numbers}
    return render(request, 'evaluaciones/landing.html',args)

def principal(request):
    return render(request,'evaluaciones/principal.html')

## Vistas para la creación
class CrearEmpresa(CreateView):
	model = empresas
	form_class = empresasForm
	template_name = "evaluaciones/crearEmpresa.html"
	#Succes_Url
	def get_succes_url(self):
		return reverse('evaluaciones:listar_empresa')
	#fields = ['nombre', 'rtn', 'direccion', 'otros_datos']
class CrearPuesto(CreateView):
	model = puestos
	form_class = puestosForm
	template_name = "evaluaciones/crearpuesto.html"
# Vistas para la actualización
class ActualizarEmpresa(UpdateView):
	model = empresas
	form_class = empresasForm
	template_name = "evaluaciones/ActualizaEmpresa.html"
	def get_succes_url(self):
		return reverse('evaluaciones:listar_empresa')
	#fields = ['nombre', 'rtn', 'direccion', 'otros_datos']
#Listas, tablas
class ListarEmpresas(ListView):	
	model = empresas
	print(empresas.objects.all())
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['now'] = timezone.now()
		print(context)
		return context

class IndexView(View):
	def get(self, request):
		template_name = "evaluaciones/landing.html"
		ctx={'s':'s'}
		return render_to_response(template_name,ctx)

class LoginView(View):	
	def get(self, request):
		if request.user.is_authenticated():
			return HttpResponseRedirect(reverse('evaluaciones:landy'))
		form = LoginForm()
		ctx = {'form':form}
		return render_to_response('login.html', ctx, context_instance=RequestContext(request))
   
	def post(self, request):
		print("hola post")
		print(request.POST)
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:
				login(request, user)
				return HttpResponseRedirect(reverse('evaluaciones:landy'))
			else:
				messages.error(request, 'Usuario Inactivo')
				return HttpResponseRedirect(reverse('evaluaciones:login'))
		else:
			# Mensaje Incorrecto
			messages.error(request, 'Correo o contraseña inválidos')
			return HttpResponseRedirect(reverse('login'))
