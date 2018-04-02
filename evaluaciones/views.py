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
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from hashlib import md5
from django.core.mail import send_mail
from django.template import loader
from evaluaciones.models import *
from evaluaciones.forms import *
from django.conf import settings

def home(request):
    numbers = [1,2,3,4,5]
    name = 'Hector Machuca'
    args = {'name' :name, 'numbers': numbers}
    return render(request, 'evaluaciones/landing.html',args)

def principal(request):
    return render(request,'evaluaciones/principal.html')

class ResetPasswordNotificacionView(View):	
	def get(self, request, pk=None, id=None):
		return HttpResponse(0)
   
	def post(self, request, pk=None, id=None):
		template_name = "evaluaciones/email_resetPassword.html"
		objColaborador = colaboradores.objects.get(pk=pk)
		objUser = objColaborador.usuario
		oldpass = md5(objColaborador.usuario.password.encode('utf-8')).hexdigest()
		url = reverse_lazy('evaluaciones:actualiza_password', args=[pk,id,oldpass])
		html_message = loader.render_to_string(
		template_name,
			{
				'empresa': objColaborador.empresa.nombre,
				'name':  objColaborador.primer_nombre,
				'usuario' : objColaborador.usuario.username,
				'fecha' : timezone.now(),
				'action_url' : settings.SITE_URL + str(url)
			}
		)
		subject = 'Reestablecer contraseña'
		if not send_mail(subject, '', settings.EMAIL_HOST_USER, [objColaborador.usuario.email], fail_silently=False, html_message=html_message):
			msg = 'No se pudo enviar el correo con las instrucciones de reestablecimiento.'
		else:
			msg = 'Correo de reestablecimiento enviado.'
		return HttpResponse(msg)

class ResetPasswordView(View):	
	def get(self, request, pk=None, id=None, oldpass=None):
		template_name = "evaluaciones/ResetPassword.html"
		objColaborador = colaboradores.objects.get(pk=pk)
		ctx = {
		'empresa' : empresas.objects.get(pk=id),
		'username': objColaborador.usuario.username
		}
		return render(request, template_name, ctx)
   
	def post(self, request, pk=None, id=None, oldpass=None):
		template_name = "evaluaciones/ResetPassword.html"
		objColaborador = colaboradores.objects.get(pk=pk)
		objUser = objColaborador.usuario
		newPass = request.POST['password']
		newRepeatPass = request.POST['password_repeat']
		p1=oldpass
		p2=md5(objColaborador.usuario.password.encode('utf-8')).hexdigest()
		html_message = loader.render_to_string(
		'evaluaciones/email_resetNotificacion.html',
			{
				'empresa': objColaborador.empresa.nombre,
				'name':  objColaborador.primer_nombre,
				'usuario' : objColaborador.usuario.username,
				'fecha' : timezone.now(),
				'action_url' : 'hola'
			}
		)
		subject = 'Cambio de contraseña'
		if p1==p2 and newPass==newRepeatPass:
			objUser.set_password(request.POST['password'].strip())
			objColaborador.fecha_ult_mod_password = timezone.now()
			objUser.save()
			objColaborador.save()
			if not send_mail(subject, '', settings.EMAIL_HOST_USER, [objColaborador.usuario.email], fail_silently=False, html_message=html_message):
				messages.add_message(request,messages.SUCCESS, 'Contraseña actualizada exitosamente. Pero no se pudo enviar el correo de confirmación.')
			else:
				messages.add_message(request,messages.SUCCESS, 'Contraseña actualizada exitosamente.')
		else:
			messages.add_message(request,messages.ERROR, 'Error al actualizar la contraseña, url no válida o caducada.')
		ctx = {
		'empresa' : empresas.objects.get(pk=id),
		'username': objColaborador.usuario.username
		}
		return render(request, template_name, ctx)

class CrearUsuarioView(View):	
	def get(self, request, pk=None):
		form = usuariosForm()
		template_name = "evaluaciones/crearUsuario.html"
		ctx = {'form':form,
		'empresa' : empresas.objects.get(pk=pk),
		'grupos': group_empresas.objects.filter(empresa__pk = pk)
		}
		return render(request, template_name, ctx)
   
	def post(self, request, pk=None):
		ctx={}
		template_name = "evaluaciones/crearUsuario.html"
		formulario = usuariosForm(request.POST)
		password = User.objects.make_random_password(length=8, allowed_chars='0123456789qwertyuiopasdfghjklzxcvbnm%$')
		objUser = User(username=request.POST['email'], email=request.POST['email']
			, first_name=request.POST['primer_nombre'], last_name=request.POST['primer_apellido'])
		objUser.set_password(password)
		
		if formulario.is_valid() and len(User.objects.filter(username=request.POST['email'])) == 0:
			form = formulario.save(commit = False)
			form.usuario_creador = request.user
			form.usuario_modificador = request.user
			objUser.save()
			objUser.groups.add(Group.objects.get(pk=request.POST['grupo']))
			form.usuario = objUser
			form.save()
			subject = 'Bienvenido al sistema de evaluación y desempeño'
			html_message = loader.render_to_string(
			'evaluaciones/email_Bienvenida.html',
				{
					'empresa': empresas.objects.get(pk=pk).nombre,
					'name':  request.POST['primer_nombre'],
					'usuario' : objUser.username,
					'password' : password,
					'action_url' : reverse_lazy('evaluaciones:login')
				}
			)
			messagemail = 'Sus datos de acceso son: usuario-> ' + objUser.username + ' password-> ' + password
			if not send_mail(subject, '', settings.EMAIL_HOST_USER, [objUser.email], fail_silently=False, html_message=html_message):
				messages.add_message(request,messages.SUCCESS,'Usuario Creado Exitosamente. Pero no se pudo enviar el correo al colaborador.')
			else:
				messages.add_message(request,messages.SUCCESS,'Usuario Creado Exitosamente. Se envio un correo con sus datos de acceso a %s'%(objUser.email))
			ctx['form'] = usuariosForm()
		else:
			if len(User.objects.filter(username=request.POST['email'])) == 0:
				messages.add_message(request,messages.ERROR,"Formulario contiene errores!!")
			else:
				messages.add_message(request,messages.ERROR,"Error, ya existe un usuario con el correo <%s>"%(request.POST['email']))
			ctx = {'form': formulario}
			print (formulario.errors)
			#ctx['message'] = message
		ctx['empresa'] = empresas.objects.get(pk=pk)
		#ctx['message'] = message
		ctx['grupos'] = group_empresas.objects.filter(empresa__pk = pk)
		ctx['perfil'] = int(request.POST['grupo'])
		ctx['email'] = request.POST['email']
		if "GuardarNuevo" in request.POST:
			return render(request, template_name, ctx)
		else:
			messages.add_message(request,messages.SUCCESS,"Exito")
			url = reverse_lazy('evaluaciones:listar_usuario', args=[pk,])
		return HttpResponseRedirect(url)

class ListarUsuarioView(TemplateView):	
	template_name = "evaluaciones/usuarios_list.html"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['form'] = usuariosForm()
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		context['object_list'] = colaboradores.objects.filter(empresa__pk = self.kwargs['pk'])
		return context

class ActualizarUsuarioView(View):	
	def get(self, request, pk=None, id=None):
		objColaborador = colaboradores.objects.get(pk=pk)
		form = usuariosForm(instance=objColaborador)
		template_name = "evaluaciones/ActualizaUsuario.html"
		ctx = {'form':form,
		'empresa' : empresas.objects.get(pk=id),
		'grupos': group_empresas.objects.filter(empresa__pk = id)
		}
		ctx['perfil'] = int(objColaborador.usuario.groups.all()[0].pk)
		ctx['email'] = objColaborador.usuario.email
		ctx['colaborador_id'] = pk
		return render(request, template_name, ctx)
   
	def post(self, request, pk=None, id=None):
		ctx={}
		template_name = "evaluaciones/ActualizaUsuario.html"
		objColaborador = colaboradores.objects.get(pk=pk)
		formulario = usuariosForm(request.POST, instance=objColaborador)
		error = False
		objUser = objColaborador.usuario
		
		if formulario.is_valid() and len(User.objects.filter(username=request.POST['email'])) == 1 and objUser.email ==request.POST['email']:
			form = formulario.save(commit = False)
			form.usuario_modificador = request.user
			form.fecha_modificacion = timezone.now()
			objUser.username = request.POST['email']
			objUser.email = request.POST['email']
			objUser.save()
			objUser.groups.clear()
			objUser.groups.add(Group.objects.get(pk=request.POST['grupo']))
			form.usuario = objUser
			form.save()
			subject = 'Bienvenido al sistema de evaluación y desempeño'
			ctx['form'] = usuariosForm()
			messages.add_message(request,messages.SUCCESS,"Usuario actualizado exitosamente.")
		else:
			if len(User.objects.filter(username=request.POST['email'])) == 0:
				messages.add_message(request,messages.ERROR,"Formulario contiene errores!!")
			else:
				messages.add_message(request,messages.ERROR,"Error, ya existe un usuario con el correo <%s>"%(request.POST['email']))
			ctx = {'form': formulario}
			error = True
		ctx['empresa'] = empresas.objects.get(pk=id)
		ctx['grupos'] = group_empresas.objects.filter(empresa__pk = id)
		ctx['perfil'] = int(request.POST['grupo'])
		ctx['email'] = request.POST['email']
		if "GuardarNuevo" in request.POST or error == True:
			url = reverse_lazy('evaluaciones:crear_usuario', args=[id,])
			return HttpResponseRedirect(url)
		else:
			url = reverse_lazy('evaluaciones:listar_usuario', args=[id,])
			return HttpResponseRedirect(url)

class EstadoUsuarioView(View):	
	def get(self, request, pk=None, id=None):
		return HttpResponseRedirect(reverse_lazy('evaluaciones:principal_empresa', args=[id,]))
   
	def post(self, request, pk=None, id=None):
		objUser = User.objects.get(pk=pk)
		objUser.is_active = False if objUser.is_active else True
		objUser.save()
		return HttpResponse('Activo' if objUser.is_active else 'Inactivo')

class RolesView(View):	
	def get(self, request, pk=None):
		content_type = ContentType.objects.get_for_model(evaluaciones)
		permissions = Permission.objects.filter(content_type=content_type)
		permission = Permission.objects.filter(content_type=content_type, codename__startswith='evaluaciones_')
		template_name = "evaluaciones/roles_list.html"
		ctx = {'grupos': group_empresas.objects.filter(empresa__pk = pk),
		'permisos' : permission,
		'empresa' : empresas.objects.get(pk=pk)
		}
		return render(request, template_name, ctx)
   
	def post(self, request, pk=None):
		print(request.POST)
		group = Group.objects.get(pk=request.POST['group'])
		permission = Permission.objects.get(pk=request.POST['permission'])
		if request.POST['accion'] == 'agregar':
			group.permissions.add(permission)
		else:
			group.permissions.remove(permission)
		return HttpResponse(0)

class RolesNuevoView(View):	   
	def get(self, request, pk=None):
		return HttpResponse(0)

	def post(self, request, pk=None):
		print(request.POST)
		objGroup = Group(name = request.POST['perfil']+'|'+str(pk))
		objGroup.save()
		objGroupEmpresas = group_empresas(empresa=empresas.objects.get(pk=pk), perfil=objGroup)
		objGroupEmpresas.save()
		return HttpResponseRedirect(reverse('evaluaciones:listar_roles', args=(pk,)))

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
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
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
		ctx = {}
		return render(request, 'registration/login.html', ctx)
   
	def post(self, request):
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username=username, password=password)
		if user is not None:
			if user.is_active:
				login(request, user)
				if user.is_superuser:
					return HttpResponseRedirect(reverse('evaluaciones:principal'))
				else:
					objColaborador = colaboradores.objects.get(usuario=user)
					return HttpResponseRedirect(reverse('evaluaciones:principal_empresa', args=[objColaborador.empresa.pk]))
			else:
				messages.error(request, 'Usuario Inactivo')
				return HttpResponseRedirect(reverse('login'))
		else:
			# Mensaje Incorrecto
			messages.error(request, 'Usuario o contraseña inválidos')
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
