from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib.auth.decorators import login_required
from django.views.generic import View, TemplateView, CreateView, ListView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from braces.views import FormInvalidMessageMixin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from tablib import Dataset
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder
import json

# Para la automatización de la creación de los periodos
from celery.schedules import crontab
from celery.task import periodic_task

# Resources
from .resources import ImportarDepartamentos
from hashlib import md5
from django.core.mail import send_mail
from django.template import loader
from evaluaciones.models import *
from evaluaciones.forms import *
from django.conf import settings
from decimal import *
from django.db.models import Q,Count, Sum, Avg
from django.db import transaction


def home(request):
	numbers = [1, 2, 3, 4, 5]
	name = 'Hector Machuca'
	args = {'name': name, 'numbers': numbers}
	return render(request, 'evaluaciones/landing.html', args)


def principal(request):
	return render(request, 'evaluaciones/principal.html')


class RolesView(View):
	def get(self, request, pk=None):
		content_type = ContentType.objects.get_for_model(evaluaciones)
		permissions = Permission.objects.filter(content_type=content_type)
		permission = Permission.objects.filter(
			content_type=content_type, codename__startswith='evaluaciones_')
		permission_delete = Permission.objects.filter(
			content_type=content_type, codename__startswith='eliminar_')
		template_name = "evaluaciones/roles_list.html"
		ctx = {'grupos': group_empresas.objects.filter(empresa__pk=pk),
			   'permisos': permission,
			   'permisos_eliminar': permission_delete,
			   'empresa': empresas.objects.get(pk=pk)
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
		if not Group.objects.filter(name__upper=request.POST['perfil'].strip().upper()+'|'+str(pk)).exists():
			objGroup = Group(name=request.POST['perfil']+'|'+str(pk))
			objGroup.save()
			objGroupEmpresas = group_empresas(
				empresa=empresas.objects.get(pk=pk), perfil=objGroup)
			objGroupEmpresas.save()
		else:
			messages.add_message(request,messages.ERROR, 'Error. Ya existe un perfil con el nombre de %s.'%(request.POST['perfil']))

		return HttpResponseRedirect(reverse('evaluaciones:listar_roles', args=(pk,)))

class RolesActualizarView(View):
	def get(self, request, pk=None, id=None):
		return HttpResponse(0)

	def post(self, request, pk=None, id=None):
		print(request.POST)
		objGroup = Group.objects.get(pk=pk)

		if not Group.objects.filter(name__upper=request.POST['perfil'].strip().upper()+'|'+str(id)).exists() or objGroup.name.upper() == request.POST['perfil'].strip().upper()+'|'+str(id):
			objGroup.name = request.POST['perfil'].strip()+'|'+str(id)
			objGroup.save()
			messages.add_message(request,messages.SUCCESS, "Éxito. Perfil actulizado exitosamente.")
		else:
			messages.add_message(request,messages.ERROR, 'Error. Ya existe un perfil con el nombre de %s.'%(request.POST['perfil']))

		return HttpResponseRedirect(reverse('evaluaciones:listar_roles', args=(id,)))

class RolesEliminarView(View):
	def get(self, request, pk=None, id=None):
		return HttpResponse(0)

	def post(self, request, pk=None, id=None):
		print(request.POST)
		objGroup = Group.objects.get(pk=pk)

		try:
			objGroup.delete()
			messages.add_message(request,messages.SUCCESS,'Exito, Perfil borrado exitosamente')				
		except models.ProtectedError: 
			objGroupEmpresas = group_empresas.objects.get(
				empresa=empresas.objects.get(pk=id), perfil=objGroup)
			objGroupEmpresas.estado = False
			objGroupEmpresas.save() 
			messages.add_message(request,messages.WARNING,'info, Existen Colaboradores que dependen de este Perfil, no se puede eliminar.')

		return HttpResponseRedirect(reverse('evaluaciones:listar_roles', args=(id,)))
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

class ExpiredPasswordView(View):	
	def get(self, request, pk=None, id=None):
		template_name = "evaluaciones/ExpiredPassword.html"
		objColaborador = colaboradores.objects.get(pk=pk)
		ctx = {
		'empresa' : empresas.objects.get(pk=id),
		'username': objColaborador.usuario.username
		}
		return render(request, template_name, ctx)
   
	def post(self, request, pk=None, id=None):
		template_name = "evaluaciones/ExpiredPassword.html"
		objColaborador = colaboradores.objects.get(pk=pk)
		objUser = objColaborador.usuario
		oldPass = request.POST['old_password']
		newPass = request.POST['password']
		newRepeatPass = request.POST['password_repeat']

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
		user = authenticate(username=objColaborador.usuario.username, password=oldPass)
		if user is not None:
			if newPass==newRepeatPass:
				objUser.set_password(newPass.strip())
				objColaborador.fecha_ult_mod_password = timezone.now()
				objColaborador.password_caducado = False
				objUser.save()
				objColaborador.save()
				if not send_mail(subject, '', settings.EMAIL_HOST_USER, [objColaborador.usuario.email], fail_silently=False, html_message=html_message):
					messages.add_message(request,messages.SUCCESS, 'Contraseña actualizada exitosamente. Pero no se pudo enviar el correo de confirmación.')
				else:
					messages.add_message(request,messages.SUCCESS, 'Contraseña actualizada exitosamente.')
			else:
				messages.add_message(request,messages.ERROR, 'Error al actualizar la contraseña, validación de nueva clave falló.')
		else:
			messages.add_message(request,messages.ERROR, 'Error al actualizar la contraseña, contraseña actual incorrecta.')
		ctx = {
		'empresa' : empresas.objects.get(pk=id),
		'username': objColaborador.usuario.username
		}
		return render(request, template_name, ctx)

class CrearUsuarioView(View):	
	def get(self, request, pk=None):
		form = usuariosForm()
		form.fields["puesto"].queryset = puestos.objects.filter(empresa__pk=pk, estado=True)
		form.fields["departamento"].queryset = departamentos.objects.filter(empresa__pk=pk, estado=True)
		form.fields["sucursal"].queryset = sucursales.objects.filter(empresa__pk=pk, estado=True)
		form.fields["supervisor"].queryset = colaboradores.objects.filter(empresa__pk=pk, grupo__name__upper='SUPERVISOR', usuario__is_active=True)
		template_name = "evaluaciones/crearUsuario.html"
		objEmpresa = empresas.objects.get(pk=pk)

		#validar licencias
		usuarios_activos = colaboradores.objects.filter(empresa=objEmpresa, usuario__is_active=True).count()
		licencias = objEmpresa.licencias
		permitir = True
		if usuarios_activos >= licencias:
			messages.add_message(request,messages.WARNING,"Lo sentimos, no tiene licencias disponibles.")
			permitir = False
		#fin validar licencias
		ctx = {'form':form,
		'empresa' : objEmpresa,
		'grupos': group_empresas.objects.filter(empresa__pk = pk),
		'permitir': permitir
		}
		return render(request, template_name, ctx)
   
	def post(self, request, pk=None):
		ctx={}
		template_name = "evaluaciones/crearUsuario.html"
		formulario = usuariosForm(request.POST)
		objEmpresa = empresas.objects.get(pk=pk)
		password = User.objects.make_random_password(length=8, allowed_chars='0123456789qwertyuiopasdfghjklzxcvbnm%$')
		objUser = User(username=request.POST['email'], email=request.POST['email']
			, first_name=request.POST['primer_nombre'], last_name=request.POST['primer_apellido'])
		objUser.set_password(password)

		#validar licencias
		usuarios_activos = colaboradores.objects.filter(empresa=objEmpresa, usuario__is_active=True).count()
		licencias = objEmpresa.licencias
		permitir = True
		if usuarios_activos >= licencias:
			permitir = False
		#fin validar licencias
		
		if formulario.is_valid() and len(User.objects.filter(username=request.POST['email'])) == 0 and permitir is True:
			form = formulario.save(commit = False)
			form.usuario_creador = request.user
			form.usuario_modificador = request.user
			objUser.save()
			objUser.groups.add(Group.objects.get(pk=request.POST['grupo']))
			form.usuario = objUser
			form.save()
			subject = 'Bienvenido al sistema de evaluación y desempeño'
			url = reverse_lazy('login')
			html_message = loader.render_to_string(
			'evaluaciones/email_Bienvenida.html',
				{
					'empresa': empresas.objects.get(pk=pk).nombre,
					'name':  request.POST['primer_nombre'],
					'usuario' : objUser.username,
					'password' : password,
					'action_url' : settings.SITE_URL + str(url)
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

		storage = messages.get_messages(request)
		storage.used=False
		if usuarios_activos >= licencias:
			messages.add_message(request,messages.WARNING,"Lo sentimos, no tiene licencias disponibles.")
		ctx['empresa'] = empresas.objects.get(pk=pk)
		#ctx['message'] = message
		ctx['grupos'] = group_empresas.objects.filter(empresa__pk = pk)
		ctx['perfil'] = int(request.POST['grupo'])
		ctx['email'] = request.POST['email']
		ctx['permitir'] = permitir
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
		form.fields["puesto"].queryset = puestos.objects.filter(empresa__pk=id, estado=True)
		form.fields["departamento"].queryset = departamentos.objects.filter(empresa__pk=id, estado=True)
		form.fields["sucursal"].queryset = sucursales.objects.filter(empresa__pk=id, estado=True)
		form.fields["supervisor"].queryset = colaboradores.objects.filter(empresa__pk=id, usuario__is_active=True)

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
			objUser.first_name = request.POST['primer_nombre']
			objUser.last_name = request.POST['primer_apellido']
			objUser.save()
			objUser.groups.clear()
			objUser.groups.add(Group.objects.get(pk=request.POST['grupo']))
			form.usuario = objUser
			form.save()
			#validar si tiene colaboradores a cargo y asignarle permiso de supervisor
			permission = Permission.objects.get(codename='especiales_es_supervisor')
			for x in colaboradores.objects.filter(empresa__pk=id, empresa__estado=True):
				x.usuario.user_permissions.remove(permission)

			for x in colaboradores.objects.filter(empresa__pk=id, empresa__estado=True).exclude(supervisor__isnull=True):
				x.supervisor.usuario.user_permissions.remove(permission)
				x.supervisor.usuario.user_permissions.add(permission)

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
		objEmpresa = empresas.objects.get(pk=id)
		objUser = User.objects.get(pk=pk)
		#validar licencias
		usuarios_activos = colaboradores.objects.filter(empresa=objEmpresa, usuario__is_active=True).count()
		licencias = objEmpresa.licencias
		permitir = True
		if usuarios_activos >= licencias and objUser.is_active == False:
			permitir = False
		#fin validar licencias
		if permitir:
			objUser.is_active = False if objUser.is_active else True
			objUser.save()
		else:
			messages.add_message(request,messages.WARNING,"Lo sentimos, no tiene licencias disponibles.")
		#return HttpResponse('Activo' if objUser.is_active else 'Inactivo')
		url = reverse_lazy('evaluaciones:listar_usuario', args=[id,])
		return HttpResponseRedirect(url)

class IndexEmpresaView(View):
	def get(self, request, pk=None):
		bandera = False		
		if perfil.objects.filter(usuario_id =request.user.id).exists():
			print('hay algo')
			p = perfil.objects.get(usuario_id=request.user.id)
			print(p)
			request.session['picture'] = p.foto.url
			bandera =True
		else: 			
			print('no hay nada')

		template_name = "evaluaciones/index_empresa.html"

		ctx = {'empresa': empresas.objects.get(pk=pk),
			    'bandera': bandera}
		if colaboradores.objects.filter(usuario=request.user).exists():
			request.session['puesto'] = colaboradores.objects.get(usuario=request.user).puesto.nombre
		else:
			request.session['puesto'] = 'Super Admin'
		return render(request, template_name, ctx)

# Vistas para la creación


class CrearEmpresa(SuccessMessageMixin, CreateView):
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

class ActualizarEmpresa(SuccessMessageMixin, UpdateView):
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
	def get_queryset(self):
		print('usuario')
		return empresas.objects.raw("SELECT e.*,count(c.id) colaboradores FROM evaluaciones_empresas e left outer join evaluaciones_colaboradores c on c.empresa_id = e.id group by e.id ")
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['now'] = timezone.now()		
		return context


class CrearPuesto(SuccessMessageMixin, FormInvalidMessageMixin, CreateView):
	model = puestos
	form_class = puestosForm
	template_name = "evaluaciones/crearpuesto.html"
	success_message = "Puesto creado satisfactoriamente."
	form_invalid_message = 'Error al crear el puesto por favor revise los datos'

	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_puesto',
							   args=[self.kwargs['pk']])
		else:
			url = reverse_lazy('evaluaciones:listar_puesto',
							   args=[self.kwargs['pk']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context

# Vistas para la actualización

class ActualizarPuesto(SuccessMessageMixin, FormInvalidMessageMixin, UpdateView):
	model = puestos
	form_class = puestosForm
	template_name = "evaluaciones/ActualizaPuesto.html"
	success_message = "Puesto actualizado satisfactoriamente."
	form_invalid_message = 'Error al Actualizar el puesto  por favor revise los datos'

	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_puesto',
							   args=[self.kwargs['id']])
		else:
			url = reverse_lazy('evaluaciones:listar_puesto',
							   args=[self.kwargs['id']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context


class ListarPuestos(ListView):

	def get_queryset(self):
		return puestos.objects.filter(empresa__pk=self.kwargs['pk'])

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context


class BorrarPuesto(SuccessMessageMixin, DeleteView):
	model = puestos
	success_message = "Puesto borrado con exito"

	def get_success_url(self):
		empresa_id = self.kwargs['id']
		print(self.request.POST)
		if "Confirm" in self.request.POST:
			url = reverse('evaluaciones:listar_puesto',
						  kwargs={'pk': empresa_id})
		else:
			url = reverse('evaluaciones:listar_puesto',
						  kwargs={'pk': empresa_id})
		return url	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context
	def get_error_url(self):
		error_url = reverse_lazy('evaluaciones:listar_puesto',args=[self.kwargs['id']])
		if error_url:			
			return error_url.format(**self.object.__dict__)
		else:
			raise ImproperlyConfigured(
				"No error URL to redirect to. Provide a error_url.")
	def delete(self, request, *args, **kwargs):		   
		self.object = self.get_object()
		success_url = self.get_success_url()
		error_url = self.get_error_url()
		try:
			self.object.delete()
			messages.add_message(request,messages.SUCCESS,'Exito, Objetivo borrado exitosamente')				
			return HttpResponseRedirect(success_url)
		except models.ProtectedError:  
			puesto = puestos.objects.get(id = self.object.pk)				
			print(puesto.pk)
			messages.add_message(request,messages.WARNING,'info, Existen Colaboradores que dependen de este Puesto, el estado paso a inactivo.')
			self.object.estado = False
			self.object.save()
			return HttpResponseRedirect(error_url)

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


class ActualizarDepartamento(SuccessMessageMixin, UpdateView):
	model = departamentos
	form_class = DepartamentosForm
	template_name = "evaluaciones/ActualizaDepartamento.html"
	success_message = "Departamento actualizado satisfactoriamente."
	error_message = "El Departamento no se pudo actualizar, inténtelo nuevamente."

	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_departamento', args=[
							   self.kwargs['id']])
		else:
			url = reverse_lazy('evaluaciones:listar_departamento', args=[
							   self.kwargs['id']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context


class ListarDepartamentos(ListView):
	def get_queryset(self):
		return departamentos.objects.filter(empresa__pk=self.kwargs['pk'])

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context


class BorrarDepartamento(SuccessMessageMixin, DeleteView):
	model = departamentos

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context

	def get_success_url(self):
		empresa_id = self.kwargs['id']
		print(self.request.POST)
		if "Confirm" in self.request.POST:
			url = reverse('evaluaciones:listar_departamento',
						  kwargs={'pk': empresa_id})
		else:
			url = reverse('evaluaciones:listar_departamento',
						  kwargs={'pk': empresa_id})
		return url
	
	def get_error_url(self):
		error_url = reverse_lazy('evaluaciones:listar_departamento',args=[self.kwargs['id']])
		if error_url:			
			return error_url.format(**self.object.__dict__)
		else:
			raise ImproperlyConfigured(
				"No error URL to redirect to. Provide a error_url.")

	def delete(self, request, *args, **kwargs):
		self.object = self.get_object()
		success_url = self.get_success_url()
		error_url = self.get_error_url()
		try:
			self.object.delete()
			messages.add_message(request,messages.SUCCESS,'Exito, Departamento borrado exitosamente')				
			return HttpResponseRedirect(success_url)
		except models.ProtectedError:			   
			messages.add_message(request,messages.WARNING,'info, Existen Elementos que dependen de este Departamento, el estado paso a inactivo.')
			self.object.estado = False
			self.object.save()
			return HttpResponseRedirect(error_url)


class CrearSucursal(SuccessMessageMixin, CreateView):
	model = sucursales
	form_class = SucursalesForm
	template_name = "evaluaciones/crearSucursal.html"
	success_message = "Sucursal creado satisfactoriamente."

	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_sucursal',
							   args=[self.kwargs['pk']])
		else:
			url = reverse_lazy('evaluaciones:listar_sucursal',
							   args=[self.kwargs['pk']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context

# Vistas para la actualización


class ActualizarSucursal(SuccessMessageMixin, UpdateView):
	model = sucursales
	form_class = SucursalesForm
	template_name = "evaluaciones/ActualizaSucursal.html"
	success_message = "Sucursal actualizado satisfactoriamente."
	error_message = "La Sucursal no se pudo actualizar, inténtelo nuevamente."

	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_sucursal',
							   args=[self.kwargs['id']])
		else:
			url = reverse_lazy('evaluaciones:listar_sucursal',
							   args=[self.kwargs['id']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context


class ListarSucursales(ListView):
	def get_queryset(self):
		return sucursales.objects.filter(empresa__pk=self.kwargs['pk'])

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context


class BorrarSucursal(SuccessMessageMixin, DeleteView):
	model = sucursales
	def get_success_url(self):
		empresa_id = self.kwargs['id']
		print(self.request.POST)
		if "Confirm" in self.request.POST:
			url = reverse('evaluaciones:listar_sucursal',
						  kwargs={'pk': empresa_id})
		else:
			url = reverse('evaluaciones:listar_sucursal',
						  kwargs={'pk': empresa_id})
		return url
	def get_error_url(self):
		error_url = reverse_lazy('evaluaciones:listar_sucursal',args=[self.kwargs['id']])
		if error_url:			
			return error_url.format(**self.object.__dict__)
		else:
			raise ImproperlyConfigured(
				"No error URL to redirect to. Provide a error_url.")

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context

	def delete(self, request, *args, **kwargs):
		self.object = self.get_object()
		success_url = self.get_success_url()
		error_url = self.get_error_url()
		try:
			self.object.delete()
			messages.add_message(
				request,
				messages.SUCCESS,'Exito, Sucursal borrada exitosamente'
				)				
			return HttpResponseRedirect(success_url)
		except models.ProtectedError:  			
			sucursal = sucursales.objects.get(id = self.object.pk)				
			print(sucursal.pk)
			messages.add_message(request,
			messages.WARNING,'info, Existen Colaboradores que dependen de esta Sucursal, el estado paso a inactivo.')
			# messages.add_message(request, messages.INFO,'info, Tendra que ser por acá')
			self.object.estado = False
			self.object.save()
			return HttpResponseRedirect(error_url)


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
					if colaboradores.objects.filter(usuario=user).count() > 0:
						objEmpresa = colaboradores.objects.get(usuario=user).empresa
						if objEmpresa.estado is True:
							objColaborador = colaboradores.objects.get(usuario=user)
							if objColaborador.password_caducado is False:
								return HttpResponseRedirect(reverse('evaluaciones:principal_empresa', args=[objColaborador.empresa.pk]))
							else:
								logout(request)
								return HttpResponseRedirect(reverse('evaluaciones:expired_password', args=[objColaborador.pk,objColaborador.empresa.pk]))
						else:
							messages.error(request, 'Empresa inactiva, comuníquese con el administrador.')
					else:
						return HttpResponseRedirect(reverse('evaluaciones:principal'))
			else:
				messages.error(request, 'Usuario Inactivo')
			return HttpResponseRedirect(reverse('login'))
		else:
			# Mensaje Incorrecto
			if User.objects.filter(username=request.POST['username'], is_active=False).count() > 0:
				messages.error(request, 'Usuario Inactivo, comuníquese con el administrador.')
			else:
				messages.error(request, 'Usuario o contraseña inválidos')
			return HttpResponseRedirect(reverse('login'))

class LogoutView(View):
	def get(self, request):
		logout(request)		
		return HttpResponseRedirect('/accounts/login/')

# Criterios

class Perfil_(View):
	def get(self, request,pk,id):		
		template_name = "evaluaciones/perfil.html"		
		#perfil_ = None
		# Si el colaborador ya tiene perfil ACTUALIZAR		
		if perfil.objects.filter(usuario_id =id).exists():			
			colaborador = colaboradores.objects.get(usuario_id = request.user.id)		
			perfil_ = perfil.objects.get(usuario_id =id)
			form = PerfilForm(instance=perfil_)			
			ctx = {'form':form,
					'empresa': empresas.objects.get(pk = pk),
					'perfil': perfil_,
					'colaborador' : colaborador
					}
			ctx['foto'] = perfil_.foto
			ctx['sexo'] = perfil_.sexo
			ctx['bandera'] = 1
			ctx['fecha_nacimiento'] = perfil_.fecha_nacimiento
			ctx['pasa_tiempos'] = perfil_.pasa_tiempos
		# Si el colaborador no tiene perfil , CREAR
		else:
			form = PerfilForm()
			ctx = {'form':form,
				'empresa': empresas.objects.get(pk = pk)}
		return render(request, template_name, ctx)
		
	def post(self, request,id=None,pk=None):		
		if 'Actualizar' in request.POST and perfil.objects.filter(usuario_id =id).exists():
			perfil_ = perfil.objects.get(usuario_id =id)		
			print('Actualizar')
			formulario = PerfilForm(request.POST,request.FILES, instance = perfil_)			
			print(request.FILES['foto'])
			colaborador = colaboradores.objects.get(usuario_id = id)
			empresa_pk = colaborador.empresa.pk
			usuario_id = id	
			url = reverse_lazy('evaluaciones:perfil_' , kwargs ={'pk' : pk, 'id' : id })		
			if formulario.is_valid():
				form = formulario.save(commit=False)
				print('VALIDO')						
				perfil_.save()
				request.session['picture'] = perfil_.foto.url
				messages.add_message(request, messages.SUCCESS,
			                     "Datos Actualizados con Exito!")
			else:
				print('ERRONEO')
				messages.add_message(request, messages.ERROR,
			                     "Formulario contiene errores!!")
		else:
			print('otro')
			formulario = PerfilForm(request.POST,request.FILES)
			colaborador = colaboradores.objects.get(usuario_id = request.user.id)			
			empresa_pk = colaborador.empresa.pk
			empresa = empresas.objects.get(pk =empresa_pk )
			usuario_id = request.user.id	
			url = reverse_lazy('evaluaciones:perfil_' , kwargs ={'pk' : pk, 'id' : id })		
			if formulario.is_valid():
				print('Valido')				
				form = formulario.save(commit=False)
				form.colaborador_id = colaborador.pk
				form.empresa = empresa
				form.usuario = request.user
				form.save()
				messages.add_message(request, messages.SUCCESS,
			                     "Perfil agregado con Exito!")	
			else:
				messages.add_message(request, messages.ERROR,
			                     "Formulario contiene errores!!")
		return HttpResponseRedirect(url)



class CrearCriterio(SuccessMessageMixin, CreateView):
	model = criterios
	form_class = CriteriosForm	
	template_name = "evaluaciones/crearCriterio.html"

	def post(self,request,pk=None):
		empresa_id = request.POST['empresa']
		print(empresa_id)
		formulario = CriteriosForm(request.POST)
		success_url = reverse('evaluaciones:crear_criterio',
						  kwargs={'pk': empresa_id})				
		if formulario.is_valid():
			new_rec = formulario.save(commit = False)
			# new_rec.periodo = periodos.objects.filter(empresa__pk = empresa_id).order_by('-pk')[:1][0].pk
			new_rec.periodo = periodos.objects.last()
			new_rec.save()
			messages.add_message(request,messages.SUCCESS,'Criterio Creado Exitosamente.')			
		else:
			messages.add_message(request,messages.ERROR,'Criterio Erroneo.')			
		return HttpResponseRedirect(success_url)

	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_criterio',
							   args=[self.kwargs['pk']])
		else:
			url = reverse_lazy('evaluaciones:listar_criterios',
							   args=[self.kwargs['pk']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context


class ActualizarCriterios(SuccessMessageMixin, UpdateView):
	model = criterios
	form_class = CriteriosForm
	template_name = "evaluaciones/ActualizaCriterio.html"
	success_message = "Criterio actualizado satisfactoriamente."
	error_message = "El Criterio no se pudo actualizar, inténtelo nuevamente."

	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:						
			url = reverse_lazy('evaluaciones:crear_criterio',
							  args=[self.kwargs['id']])
		else:			
			url = reverse_lazy('evaluaciones:listar_criterios',
                            args=[self.kwargs['id']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context


class ListarCriterios(ListView):
	def get_queryset(self):
		return criterios.objects.filter(empresa__pk=self.kwargs['pk'])
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context

class BorrarCriterios(SuccessMessageMixin, DeleteView):
	model = criterios		

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context

	def get_success_url(self):
		empresa_id = self.kwargs['id']
		print(self.request.POST)
		if "Confirm" in self.request.POST:
			url = reverse('evaluaciones:listar_criterios',
						  kwargs={'pk': empresa_id})
		else:
			url = reverse('evaluaciones:listar_criterios',
						  kwargs={'pk': empresa_id})
		return url
	def get_error_url(self):
		error_url = reverse_lazy('evaluaciones:listar_criterios',args=[self.kwargs['id']])
		if error_url:			
			return error_url.format(**self.object.__dict__)
		else:
			raise ImproperlyConfigured(
				"No error URL to redirect to. Provide a error_url.")
	def delete(self, request, *args, **kwargs):		   
		self.object = self.get_object()
		success_url = self.get_success_url()
		error_url = self.get_error_url()
		try:
			self.object.delete()
			messages.add_message(request,messages.SUCCESS,'Exito, Criterio borrado exitosamente')				
			return HttpResponseRedirect(success_url)
		except models.ProtectedError:
			messages.add_message(request,messages.WARNING,'info, Existen Criterios que dependen de este Criterio, el estado paso a inactivo.')
			self.object.estado = False
			self.object.save()
			return HttpResponseRedirect(error_url)
# Periodos
class CrearPeriodos(SuccessMessageMixin, CreateView):
	model = periodos	
	form_class = PeriodosForm
	template_name = "evaluaciones/crearPeriodo.html"
	success_message = "Periodo creado satisfactoriamente."
	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context        

	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_periodo',
							   args=[self.kwargs['pk']])
		else:
			url = reverse_lazy('evaluaciones:listar_periodos',
							   args=[self.kwargs['pk']])
		return url


class ListarPeriodos(ListView):
	def get_queryset(self):
		return periodos.objects.filter(empresa__pk=self.kwargs['pk'])

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context

# OBJETIVOS
# Creación de Objetivos
class CrearObjetivos(SuccessMessageMixin, CreateView):
	model = objetivos
	form_class = objetivosForm
	template_name = "evaluaciones/crearObjetivo.html"
	success_message = "Objetivo creado satisfactoriamente."

	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_objetivos',
							   args=[self.kwargs['pk']])
		else:
			url = reverse_lazy('evaluaciones:listar_objetivos',
							   args=[self.kwargs['pk']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context

# Listar Objetivos


class ListarObjetivos(ListView):
	model = objetivos

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context
# Actualizar Objetivos


class ActualizarObjetivos(SuccessMessageMixin, UpdateView):
	model = objetivos
	form_class = objetivosFormEdit
	template_name = "evaluaciones/ActualizaObjetivo.html"
	success_message = "Objetivo actualizado satisfactoriamente."
	error_message = "El objetivo no se pudo actualizar, inténtelo nuevamente."

	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_objetivos',
							   args=[self.kwargs['id']])
		else:
			url = reverse_lazy('evaluaciones:listar_objetivos',
							   args=[self.kwargs['id']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context


class BorrarObjetivos(SuccessMessageMixin, DeleteView):
	model = objetivos	
	success_message = "Objetivo borrado con exito"
	error_message = "El objeto se paso a inactivo"

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context

	def get_success_url(self):
		empresa_id = self.kwargs['id']
		print(self.request.POST)
		if "Confirm" in self.request.POST:
			url = reverse('evaluaciones:listar_objetivos',
						  kwargs={'pk': empresa_id})
		else:
			url = reverse('evaluaciones:listar_objetivos',
						  kwargs={'pk': empresa_id})
		return url
	def get_error_url(self):
		error_url = reverse_lazy('evaluaciones:listar_objetivos',args=[self.kwargs['id']])
		if error_url:			
			return error_url.format(**self.object.__dict__)
		else:
			raise ImproperlyConfigured(
				"No error URL to redirect to. Provide a error_url.")
	def delete(self, request, *args, **kwargs):		   
		self.object = self.get_object()
		success_url = self.get_success_url()
		error_url = self.get_error_url()
		try:
			self.object.delete()
			messages.add_message(request,messages.SUCCESS,'Exito, Objetivo borrado exitosamente')				
			return HttpResponseRedirect(success_url)
		except models.ProtectedError:  
			cri = criterios.objects.get(objetivo_id = self.object.pk)				
			print(cri.pk)
			messages.add_message(request,messages.WARNING,'info, Existen Criterios que dependen de este Objetivo, el estado paso a inactivo.')
			self.object.estado = False
			self.object.save()
			return HttpResponseRedirect(error_url)

def simple_upload(request):
	if request.method == 'POST':
		departamento_import = ImportarDepartamentos()
		dataset = Dataset()
		new_persons = request.FILES['myfile']
		imported_data = dataset.load(new_persons.read())
		result = departamento_import.import_data(
			dataset, dry_run=True)  # Test the data import
		if not result.has_errors():
			departamento_import.import_data(
				dataset, dry_run=False)  # Actually import now

	return render(request, 'evaluaciones/simple_upload.html')

class activar_objetivo(View):
	def post(self,request,pk=None):
		print(request.POST['empresa_id'])
		empresa_id = request.POST['empresa_id']
		messages.add_message(request,messages.SUCCESS,'info,Objetivo activado')
		success_url = reverse('evaluaciones:listar_objetivos',
						  kwargs={'pk': empresa_id})
		objetivo_ = request.POST['pk']
		obj = objetivos.objects.get(pk = objetivo_)
		if obj:
			print(obj.estado)
			obj.estado = True
			obj.save()
			print(obj.estado)		 
		return HttpResponse(success_url)

class activar_empresa(View):
	def post(self, request, pk=None):
		print(request.POST)
		empresa_id = request.POST['pk']		
		obj = empresas.objects.get(pk=empresa_id)	   
		if request.POST['bandera'] == '1':
			mensaje = 'Desactivada'			
			obj.estado = False		   
		else:
			mensaje = 'Activada'
			obj.estado = True
		obj.save()			
		mensaje_ = 'Empresa ' + mensaje + ' con exito.'
		messages.add_message(request, messages.SUCCESS,mensaje_)
		success_url = reverse('evaluaciones:listar_empresa')	
		return HttpResponse(success_url)

class activar_departamento(View):
	def post(self,request,pk=None):
		print(request.POST['empresa_id'])
		empresa_id = request.POST['empresa_id']
		messages.add_message(request,messages.SUCCESS,'Departamento activado')
		success_url = reverse('evaluaciones:listar_departamento',
						  kwargs={'pk': empresa_id})
		departamento_ = request.POST['pk']
		print(departamento_)
		depa = departamentos.objects.get(pk = departamento_)
		if depa:
			print(depa.estado)
			depa.estado = True
			depa.save()
			print(depa.estado)		 
		return HttpResponse(success_url)

class activar_puesto(View):	
	def post(self,request,pk=None):
		print(request.POST['empresa_id'])
		empresa_id = request.POST['empresa_id']
		messages.add_message(request,messages.SUCCESS,'Puesto activado')
		success_url = reverse('evaluaciones:listar_puesto',
						  kwargs={'pk': empresa_id})
		puest = request.POST['pk']
		print(puest)
		puesto = puestos.objects.get(pk = puest)
		if puesto:
			print(puesto.estado)
			puesto.estado = True
			puesto.save()
			print(puesto.estado)		 
		return HttpResponse(success_url)


class activar_sucursal(View):
	def post(self,request,pk=None):
		print(request.POST['empresa_id'])
		empresa_id = request.POST['empresa_id']
		messages.add_message(request,messages.SUCCESS,'Sucursal activada')
		success_url = reverse('evaluaciones:listar_sucursal',
						  kwargs={'pk': empresa_id})
		sucu = request.POST['pk']
		print(sucu)
		sucursal = sucursales.objects.get(pk = sucu)
		if sucursal:
			print(sucursal.estado)
			sucursal.estado = True
			sucursal.save()
			print(sucursal.estado)		 
		return HttpResponse(success_url)

class CrearPerfil(SuccessMessageMixin, CreateView):
	model = perfil
	form_class = PerfilForm
	template_name = "evaluaciones/crearPerfil.html"
	success_message = "Criterio creado satisfactoriamente."

	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_perfil',
							   args=[self.kwargs['pk']])				
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		return context



class ActualizarPeriodos(SuccessMessageMixin, UpdateView):
	model = periodos
	form_class = PeriodosForm
	template_name = "evaluaciones/ActualizaPeriodo.html"
	success_message = "Periodo actualizado satisfactoriamente."
	error_message = "El Periodo no se pudo actualizar, inténtelo nuevamente."

	def get_success_url(self, **kwargs):
		print(self.request.POST)
		if "GuardarNuevo" in self.request.POST:						
			url = reverse_lazy('evaluaciones:crear_periodo',
							  args=[self.kwargs['id']])
		else:			
			url = reverse_lazy('evaluaciones:listar_periodos',
                            args=[self.kwargs['id']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context

class BorrarPeriodo(SuccessMessageMixin, DeleteView):
	model = periodos
	success_message = "Periodo borrado con exito"

	def get_success_url(self):
		empresa_id = self.kwargs['id']
		print(self.request.POST)
		if "Confirm" in self.request.POST:
			url = reverse('evaluaciones:listar_periodos',
						  kwargs={'pk': empresa_id})
		else:
			url = reverse('evaluaciones:listar_periodos',
						  kwargs={'pk': empresa_id})
		return url	
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['id'])
		return context
	def get_error_url(self):
		error_url = reverse_lazy(
			'evaluaciones:listar_periodos', args=[self.kwargs['id']])
		if error_url:			
			return error_url.format(**self.object.__dict__)
		else:
			raise ImproperlyConfigured(
				"No error URL to redirect to. Provide a error_url.")
	def delete(self, request, *args, **kwargs):		   
		self.object = self.get_object()
		success_url = self.get_success_url()
		error_url = self.get_error_url()
		try:
			self.object.delete()
			messages.add_message(request,messages.SUCCESS,'Exito, Periodo borrado exitosamente')				
			return HttpResponseRedirect(success_url)
		except models.ProtectedError:  			
			messages.add_message(request,messages.WARNING,'info, Existen Empresas que dependen de este Periodo, el estado paso a inactivo.')
			self.object.estado = False
			self.object.save()
			return HttpResponseRedirect(error_url)

class activar_periodo(View):
	def post(self,request,pk=None):
		print(request.POST['empresa_id'])
		empresa_id = request.POST['empresa_id']
		messages.add_message(request,messages.SUCCESS,'info,Periodo activado')
		success_url = reverse('evaluaciones:listar_periodos',
						  kwargs={'pk': empresa_id})
		periodo_ = request.POST['pk']
		obj = periodos.objects.get(pk = periodo_)
		if obj:
			print(obj.estado)
			obj.estado = True
			obj.save()
			print(obj.estado)		 
		return HttpResponse(success_url)

class activar_criterio(View):
	def post(self,request,pk=None):
		print(request.POST['empresa_id'])
		empresa_id = request.POST['empresa_id']
		messages.add_message(request,messages.SUCCESS,'info,Criterio activado')
		success_url = reverse('evaluaciones:listar_criterios',
						  kwargs={'pk': empresa_id})
		criterio_ = request.POST['pk']
		obj = criterios.objects.get(pk = criterio_)
		if obj:
			print(obj.estado)
			obj.estado = True
			obj.save()
			print(obj.estado)		 
		return HttpResponse(success_url)

class ColaboradorMisEvaluaciones(View):
	def get(self,request,pk=None, id=None):
		template_name = "evaluaciones/misEvaluaciones.html"
		objEmpresa = empresas.objects.get(pk=pk)
		ctx = {'empresa': objEmpresa}
		try:
			objColaborador = colaboradores.objects.get(usuario__pk=id)
			objEvaluaciones = evaluaciones.objects.filter(empresa__pk=pk, criterio__estado=True, periodo__estado=True, puesto=objColaborador.puesto).order_by('criterio__objetivo__nombre', 'criterio__nombre')
			objEvalColaborador = evaluacion_colaborador.objects.filter(periodo__estado=True, colaborador__usuario=objColaborador.usuario, estado=True)
			objPeriodo = objEvaluaciones[0].periodo
			ctx = {'empresa': objEmpresa,
			'criterios' : objEvaluaciones,
			'colaborador' : objColaborador,
			'periodo' : objPeriodo,
			'evaluacionColaborador' : objEvalColaborador}
		except:
			pass
		return render(request, template_name, ctx)

	@transaction.atomic
	def post(self,request,pk=None, id=None):
		template_name = "evaluaciones/misEvaluaciones.html"
		error = False
		objEmpresa = empresas.objects.get(pk=pk)
		objColaborador = colaboradores.objects.get(usuario__pk=id)
		objEvaluaciones = evaluaciones.objects.filter(empresa__pk=pk, criterio__estado=True, periodo__estado=True, puesto=objColaborador.puesto).order_by('criterio__objetivo__nombre', 'criterio__nombre')
		objEvaluacionesNota = evaluaciones.objects.filter(empresa__pk=pk, criterio__estado=True, periodo__estado=True, puesto=objColaborador.puesto).order_by('criterio__objetivo__nombre', 'criterio__nombre')
		objPeriodo = objEvaluaciones[0].periodo
		print(request.POST)
		try:
			sid = transaction.savepoint()
			for x in objEvaluacionesNota:
				if 'porcentaje_%s_%s'%(x.pk,objColaborador.pk) in request.POST:
					porcentaje = Decimal(request.POST['porcentaje_%s_%s'%(x.pk,objColaborador.pk)])
					porcentaje_meta = x.porcentaje_meta
					if (porcentaje/porcentaje_meta)<1:
						porcentaje_final = (porcentaje/porcentaje_meta)*100
					else:
						porcentaje_final = 100
					nota = x.ponderacion*porcentaje_final/100
					if evaluacion_colaborador.objects.filter(evaluacion=x).exists():
						objEvalColaborador = evaluacion_colaborador.objects.get(empresa__pk=pk,evaluacion=x,colaborador=objColaborador,periodo=objPeriodo, estado = True)
						objEvalColaborador.porcentaje = porcentaje
						objEvalColaborador.porcentaje_final = porcentaje_final
						objEvalColaborador.nota = nota
					else:
						objEvalColaborador=evaluacion_colaborador(
							empresa = objEmpresa,
							periodo = objPeriodo,
							puesto = x.puesto,
							evaluacion = x,
							colaborador = objColaborador,
							porcentaje = porcentaje,
							porcentaje_final = porcentaje_final,
							nota = nota,
							estado = True
						)
					if request.user.has_perm('evaluaciones.especiales_es_supervisor') and request.user.pk != id:
						objEvalColaborador.supervisor = objColaborador.supervisor
						objEvalColaborador.fecha_supervisor = timezone.now()
					else:
						objEvalColaborador.fecha_colaborador = timezone.now()
					objEvalColaborador.save()
			transaction.savepoint_commit(sid)
		except:
			error = True
			transaction.savepoint_rollback(sid)
		
		if error == False:
			messages.add_message(request,messages.SUCCESS,"Evaluación guardada exitosamente.")
		else:
			messages.add_message(request,messages.ERROR,"La Evaluación no se ha guardado.")
		objEvalColaborador = evaluacion_colaborador.objects.filter(periodo__estado=True, colaborador=objColaborador, estado=True)
		ctx = {'empresa': objEmpresa,
		'criterios' : objEvaluaciones,
		'colaborador' : objColaborador,
		'periodo' : objPeriodo,
		'evaluacionColaborador' : objEvalColaborador}
		return render(request, template_name, ctx)

class SupervisorEvaluacionesList(View):
	def get(self,request,pk=None):
		template_name = "evaluaciones/supervisorEvaluacionesList.html"
		objEmpresa = empresas.objects.get(pk=pk)
		data=[]
		totalCriterios = evaluaciones.objects.filter(empresa__pk=pk,estado=True,periodo__estado=True).count()
		evalu = evaluacion_colaborador.objects\
		.filter(empresa__pk=pk, colaborador__supervisor__usuario=request.user, estado=True)\
		.values('empresa__pk','evaluacion__puesto__pk','colaborador__usuario','colaborador__codigo','colaborador__primer_nombre','colaborador__primer_apellido').annotate(SumaNotas=Sum('nota'), TotalNotas=Count('evaluacion'))
		ctx = {'empresa': objEmpresa,
				'evaluaciones': evalu,
				'totalCriterios' : totalCriterios}
		return render(request, template_name, ctx)

	def post(self,request,pk=None):
		pass

class EvaluacionesHistorial(View):
	def get(self,request,pk=None):
		template_name = "evaluaciones/EvaluacionesHistorial.html"
		objEmpresa = empresas.objects.get(pk=pk)
		data=[]
		totalCriterios = evaluaciones.objects.filter(empresa__pk=pk,estado=True,periodo__estado=True).count()
		evalu = evaluacion_colaborador.objects\
		.filter(empresa__pk=pk, colaborador__supervisor__usuario=request.user, estado=True)\
		.values('empresa__pk','evaluacion__puesto__pk','colaborador__usuario','colaborador__codigo','colaborador__primer_nombre','colaborador__primer_apellido').annotate(SumaNotas=Sum('nota'), TotalNotas=Count('evaluacion'))
		ctx = {'empresa': objEmpresa,
				'evaluaciones': evalu,
				'totalCriterios' : totalCriterios}
		return render(request, template_name, ctx)

	def post(self,request,pk=None):
		objEmpresa = empresas.objects.get(pk=pk)
		data=[]
		totalCriterios = evaluaciones.objects.filter(empresa__pk=pk,estado=True,periodo__estado=True).count()
		evalu = evaluacion_colaborador.objects\
		.filter(empresa__pk=pk, colaborador__usuario=request.user, periodo__pk=request.POST['id_periodo'])\
		.values('empresa__pk','evaluacion__puesto__pk','colaborador__usuario','colaborador__codigo','colaborador__primer_nombre','colaborador__primer_apellido').annotate(SumaNotas=Sum('nota'), TotalNotas=Count('evaluacion'))

		html_message = loader.render_to_string(
			'evaluaciones/evaluacionesHistorialRefresh.html',
				{
					'empresa': objEmpresa,
					'evaluaciones': evalu,
					'totalCriterios' : totalCriterios
				}
			)
		return HttpResponse(html_message)

class CrearEvaluacion(SuccessMessageMixin, FormInvalidMessageMixin, CreateView):
	model = evaluaciones
	form_class = EvaluacionesForm
	template_name = "evaluaciones/crearevaluacion.html"	
	form_invalid_message = 'Error al crear la evaluacion por favor revise los datos'
		
	def get_success_url(self, **kwargs):				
		if "GuardarNuevo" in self.request.POST:
			url = reverse_lazy('evaluaciones:crear_evaluacion',
							   args=[self.kwargs['pk']])
		else:
			url = reverse_lazy('evaluaciones:listar_evaluacion',
							   args=[self.kwargs['pk']])
		return url

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		periodo = periodos.objects.filter(empresa_id =self.kwargs['pk']).order_by('-id')[:1]
		criterios_ =  criterios.objects.filter(empresa_id =self.kwargs['pk'], periodo_id = periodo).order_by('id')		
		criterios_usados = evaluaciones.objects.filter(empresa_id = self.kwargs['pk'], periodo_id = periodo )		
		evaluaciones_hechas = evaluaciones.objects.filter(empresa_id = self.kwargs['pk'], periodo_id = periodo )
		print(evaluaciones_hechas)		
		criterios_finales = criterios_.exclude(id__in = criterios_usados.values_list('criterio_id' ))
		puestos_ = puestos.objects.all()			
		puestos_finales = puestos_.exclude(id__in =  evaluaciones_hechas.values_list('puesto_id' ))
		print(puestos_finales)
		context['criterios'] = criterios_finales
		context['periodos'] = periodo	
		context['puestos'] = puestos_finales
		return context

class guardar_evaluacion(View):
	def post(self,request,pk=None):	
		print(request.POST)	
		empresa_id = request.POST['empresa_id']
		periodo_id = request.POST['periodo_id']
		puesto_id = request.POST['puesto_id']
		ponderacion = request.POST.getlist('ponderaciones[]')
		meta = request.POST.getlist('metas[]')
		contador = 0
		for objeto in request.POST.getlist('ids[]'):			
			evaluacion_ = evaluaciones(
				ponderacion=ponderacion[contador],
				porcentaje_meta=meta[contador],
			    criterio_id = objeto,
				empresa_id = empresa_id,
				periodo_id = periodo_id,
				puesto_id = puesto_id)
			evaluacion_.save()
			print(objeto, ponderacion[contador],meta[contador])			
			contador= contador+1
		if contador>0 :
			messages.add_message(request,messages.SUCCESS,'Info,Evaluación Creada con exito')
		else:
			messages.add_message(request,messages.ERROR,'Error,no se pudo crear la evaluación')
		print(empresa_id,periodo_id,puesto_id)			
		
		success_url = reverse('evaluaciones:listar_criterios',
						  kwargs={'pk': empresa_id})
		return HttpResponse(success_url)


class ListarEvaluaciones(ListView):
	def get_queryset(self):				
		return evaluaciones.objects.filter(empresa__pk=self.kwargs['pk'])
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['periodos']  = periodos.objects.filter(empresa_id =self.kwargs['pk']).order_by('-id')[:1]		
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		context['puestos'] = puestos.objects.filter(empresa__id=self.kwargs['pk'])
		return context

class borrar_evaluaciones(View):
	def post(self,request,pk=None):				
		empresa_id = request.POST['empresa_id']
		periodo_id = request.POST['periodo_id']
		puesto_id = request.POST['puesto_id']
		elementos = request.POST.getlist('ids[]')					
		print(empresa_id,periodo_id,puesto_id)
		if	evaluaciones.objects.filter(empresa__pk=empresa_id, puesto__pk = puesto_id).delete():
			messages.add_message(request,messages.SUCCESS, 'Exito. Evaluaciones Borradas')
		else:
			messages.add_message(request,messages.ERROR, 'Error al borrar las evaluaciones')

		success_url = reverse('evaluaciones:listar_criterios',
						  kwargs={'pk': empresa_id})
		return HttpResponse(success_url)

def actualizar_tabla(request):		
		empresa_id = request.POST['empresa_id']
		puesto_id = request.POST['puesto_id']
		for p in empresas.objects.raw('SELECT * FROM evaluaciones_empresas'):

			if puesto_id == '':
				evaluaciones_ = []
			else: 
				evaluaciones_ = list(evaluaciones.objects.filter(
					empresa__pk=empresa_id, puesto__pk = puesto_id).values(
					  'criterio_id',
					  'criterio__nombre',
					  'empresa__id',
					  'empresa__nombre',
					  'criterio__nombre',
					  'puesto__nombre',
					  'periodo__fecha_inico',
					  'periodo__fecha_fin',	
					  'ponderacion',
					  'porcentaje_meta'
					  ))		
		return HttpResponse(json.dumps(evaluaciones_, cls=DjangoJSONEncoder), content_type="application/json")

def actualizar_tablacriterios(request):
		print('actualizando tabla criterios')
		empresa_id = request.POST['empresa_id']
		puesto_id = request.POST['puesto_id']	
		periodo_id = request.POST['periodo_id']			
		if puesto_id == '':
			print('puesto_id vacio' + periodo_id)
			criterios_finales = []
		else: 
			print('al parecer hay algo')
			criterios_ =  criterios.objects.filter(empresa_id =empresa_id, periodo_id = periodo_id).order_by('id')		
			criterios_usados = evaluaciones.objects.filter(empresa_id = empresa_id, periodo_id = periodo_id, puesto_id = puesto_id)
			criterios_finales = list(criterios_.exclude(id__in = criterios_usados.values_list('criterio_id' )).values(
				'id','nombre','descripcion','objetivo__nombre','periodo__fecha_fin','periodo__fecha_inico','empresa__nombre'
			))			
		return HttpResponse(json.dumps(criterios_finales, cls=DjangoJSONEncoder), content_type="application/json")
	
class ListarEvaluaciones_modificar(ListView):
	template_name = 'evaluaciones/evaluaciones_list_modificar.html'
	def get_queryset(self):				
		return evaluaciones.objects.filter(empresa__pk=self.kwargs['pk'])
	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['periodos']  = periodos.objects.filter(empresa_id =self.kwargs['pk']).order_by('-id')[:1]		
		context['empresa'] = empresas.objects.get(pk=self.kwargs['pk'])
		context['puestos'] = puestos.objects.filter(empresa__id=self.kwargs['pk'])
		return context

class modificar_evaluacion(View):
	def post(self,request,pk=None):	
		print(request.POST)	
		empresa_id = request.POST['empresa_id']
		periodo_id = request.POST['periodo_id']
		puesto_id = request.POST['puesto_id']
		ponderacion = request.POST.getlist('ponderaciones[]')
		meta = request.POST.getlist('metas[]')
		contador = 0		 
		for objeto in request.POST.getlist('ids[]'):
				obj,created = evaluaciones.objects.update_or_create(
				criterio_id = objeto,
				empresa_id = empresa_id,
				periodo_id = periodo_id,
				puesto_id = puesto_id,				
				defaults={
				'ponderacion' : ponderacion[contador],
				'porcentaje_meta' : meta[contador],
				}
				)			
				contador= contador+1
		if contador>0 :
			messages.add_message(request,messages.SUCCESS,'Info,Evaluación Creada con exito')
		else:
			messages.add_message(request,messages.ERROR,'Error,no se pudo crear la evaluación')
		print(empresa_id,periodo_id,puesto_id)			
		
		success_url = reverse('evaluaciones:listar_criterios',
						  kwargs={'pk': empresa_id})
		return HttpResponse(success_url)
