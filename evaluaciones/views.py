from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.generic import View, TemplateView
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

def home(request):
    numbers = [1,2,3,4,5]
    name = 'Hector Machuca'
    args = {'name' :name, 'numbers': numbers}
    return render(request, 'evaluaciones/landing.html',args)

def principal(request):
    return render(request,'evaluaciones/principal.html')

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
