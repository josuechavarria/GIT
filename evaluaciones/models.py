from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.timezone import now
# Create your models here.

class empresas(models.Model):
	"""docstring for empresas"""
	nombre = models.CharField(max_length=60)
	rtn = models.CharField(max_length=20)
	direccion = models.TextField()
	otros_datos = models.TextField()
	def __str__(self):
		return self.nombre

class puestos(models.Model):
	"""docstring for puestos"""
	empresa = models.ForeignKey(empresas)
	perfil = models.ForeignKey(Group)
	nombre = models.CharField(max_length=50)
	orden_jerarquico = models.IntegerField()
	def __str__(self):
		return self.empresa


class departamentos(models.Model):
	"""docstring for departamentos"""
	empresa = models.ForeignKey(empresas)
	nombre = models.CharField(max_length=60)
	def __str__(self):
		return self.nombre


class sucursales(models.Model):
	"""docstring for sucursales"""
	empresa = models.ForeignKey(empresas)
	nombre = models.CharField(max_length=60)
	direccion = models.TextField()
	otros_datos = models.TextField()
	def __str__(self):
		return self.nombre


class colaboradores(models.Model):
	"""docstring for colaborador"""
	empresa = models.ForeignKey(empresas)
	usuario = models.ForeignKey(User)
	codigo = models.CharField(max_length=50, unique=True)
	primer_nombre = models.CharField(max_length=30)
	segundo_nombre = models.CharField(max_length=30)
	primer_apellido = models.CharField(max_length=30)
	segundo_apellido = models.CharField(max_length=30)
	password_caducado = models.BooleanField(default=False)
	puesto = models.ForeignKey(puestos)
	departamento = models.ForeignKey(departamentos)
	sucursal = models.ForeignKey(sucursales, null=True, blank=True, default=None)
	supevisor = models.ForeignKey('self')
	usuario_creador = models.ForeignKey(
		User, related_name='colaborador_usuario_creador')
	fecha_creacion = models.DateField(default=now)
	usuario_modificador = models.ForeignKey(
		User, related_name='colaborador_usuario_modificador')
	fecha_modificacion = models.DateField(default=now)
	fecha_ult_mod_password = models.DateField(default=now)

	def _get_full_name(self):
		"Returns the person's full name."
		return '%s %s %s %s' % (self.primer_nombre, self.segundo_nombre, self.primer_apellido, self.segundo_apellido)
	nombre_completo = property(_get_full_name)


class perfil(models.Model):
	empresa = models.ForeignKey(empresas)
	colaborador = models.ForeignKey(colaboradores)
	usuario = models.ForeignKey(User)
	foto = models.ImageField(
		upload_to='profile', null=True, blank=True, default=None)
	sexo = models.CharField(max_length=15, null=True, blank=True, default=None)
	fecha_nacimiento = models.DateField(null=True, blank=True, default=None)
	pasa_tiempos = models.TextField(null=True, blank=True, default=None)

class periodos(models.Model):
	"""periodo a evaluar, se llenara una vez, luego automatico
	   hasta que se cambie, se tomara como base el activo"""
	empresa = models.ForeignKey(empresas)
	fecha_inico = models.DateTimeField()
	fecha_fin = models.DateTimeField()
	activo = models.BooleanField()
	def get_year(self):
		return self.fecha_inico.year


class objetivos(models.Model):
	"""objetivo estrategico del criterio"""
	nombre = models.CharField(max_length=30, unique=True)


class criterios(models.Model):
	"""Al crear no se debe mostrar el periodo ni la empresa, debe guardarse el activo por empresa"""
	empresa = models.ForeignKey(empresas)
	periodo = models.ForeignKey(periodos)
	nombre = models.CharField(max_length=120, unique=True)
	descripcion = models.TextField()
	objetivo = models.ForeignKey(objetivos)


class evaluaciones(models.Model):
	empresa = models.ForeignKey(empresas)
	periodo = models.ForeignKey(periodos)
	puesto = models.ForeignKey(puestos)
	criterio = models.ForeignKey(criterios)
	ponderacion = models.DecimalField(max_digits=3, decimal_places=2)
	porcentaje_meta = models.DecimalField(max_digits=3, decimal_places=2)


class evaluacion_colaborador(models.Model):
	empresa = models.ForeignKey(empresas)
	periodo = models.ForeignKey(periodos)
	puesto = models.ForeignKey(puestos)
	evaluacion = models.ForeignKey(evaluaciones)
	colaborador = models.ForeignKey(colaboradores)
	porcentaje = models.DecimalField(max_digits=3, decimal_places=2)
	porcentaje_final = models.DecimalField(max_digits=3, decimal_places=2)
	nota = models.DecimalField(max_digits=3, decimal_places=2)
