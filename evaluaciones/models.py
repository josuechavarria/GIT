from django.db import models
from django.contrib.auth.models import User, Group
from django.utils.timezone import now
from django.db.models import Transform, CharField, TextField
import locale


locale.setlocale(locale.LC_ALL, "")
# Create your models here.

#django celery

class samplecount(models.Model):
	numero = models.IntegerField(default=0)
#

# BEGIN CUSTOM LOOKUPS
class UpperCase(Transform):
    lookup_name = 'upper'
    bilateral = True

    def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        return "UPPER(%s)" % lhs, params

CharField.register_lookup(UpperCase)
TextField.register_lookup(UpperCase)

class empresas(models.Model):
	"""docstring for empresas"""
	nombre = models.CharField(max_length=60)
	rtn = models.CharField(max_length=20)
	licencias = models.IntegerField(default=0)
	direccion = models.TextField()
	otros_datos = models.TextField()
	logo = models.ImageField(
		upload_to='evaluaciones/logos', null=True, blank=True, default=None)
	estado = models.BooleanField(default=True)
	def __str__(self):
		return self.nombre
	
	def nombre_(self):
		return self.nombre

class puestos(models.Model):
	"""docstring for puestos"""
	empresa = models.ForeignKey(empresas)
	nombre = models.CharField(max_length=50)
	orden_jerarquico = models.IntegerField()
	estado = models.BooleanField(default=True)
	def __str__(self):
		return self.nombre

class group_empresas(models.Model):
	empresa = models.ForeignKey(empresas)
	perfil = models.ForeignKey(Group)
	estado = models.BooleanField(default=True)

class departamentos(models.Model):
	"""docstring for departamentos"""
	empresa = models.ForeignKey(empresas,)
	nombre = models.CharField(max_length=60)
	estado = models.BooleanField(default=True)
	def __str__(self):
		return self.nombre


class sucursales(models.Model):
	"""docstring for sucursales"""
	empresa = models.ForeignKey(empresas)
	nombre = models.CharField(max_length=60)
	direccion = models.TextField()
	otros_datos = models.TextField()
	estado = models.BooleanField(default=True)
	
	def __str__(self):
		return self.nombre


class colaboradores(models.Model):
	"""docstring for colaborador"""
	empresa = models.ForeignKey(empresas)
	usuario = models.OneToOneField(User)
	codigo = models.CharField(max_length=50, verbose_name = "Código colaborador")
	primer_nombre = models.CharField(max_length=30)
	segundo_nombre = models.CharField(max_length=30, null=True, blank=True, default=None)
	primer_apellido = models.CharField(max_length=30)
	segundo_apellido = models.CharField(max_length=30, null=True, blank=True, default=None)
	password_caducado = models.BooleanField(default=False)
	puesto = models.ForeignKey(puestos,on_delete=models.PROTECT)
	departamento = models.ForeignKey(departamentos, on_delete=models.PROTECT)
	sucursal = models.ForeignKey(sucursales, null=True, blank=True, default=None, on_delete=models.PROTECT)
	supervisor = models.ForeignKey('self',null=True, blank=True, default=None, on_delete=models.CASCADE)
	grupo = models.ForeignKey(Group, default=None, verbose_name = "Perfil", on_delete=models.PROTECT)
	usuario_creador = models.ForeignKey(
		User, related_name='colaborador_usuario_creador')
	fecha_creacion = models.DateField(default=now)
	usuario_modificador = models.ForeignKey(
		User, related_name='colaborador_usuario_modificador')
	fecha_modificacion = models.DateField(default=now)
	fecha_ult_mod_password = models.DateField(default=now)
	estado = models.BooleanField(default=True)

	def _get_full_name(self):
		"Returns the person's full name."
		return '%s %s %s %s' % (self.primer_nombre, '' if self.segundo_nombre is None else self.segundo_nombre, self.primer_apellido, '' if self.segundo_apellido is None else self.segundo_apellido)
	nombre_completo = property(_get_full_name)

	def __str__(self):
		return '%s|%s %s'%(self.codigo,self.primer_nombre,self.primer_apellido)

	class Meta:
		unique_together = ("empresa", "codigo")


class perfil(models.Model):
	empresa = models.ForeignKey(empresas)
	colaborador = models.ForeignKey(colaboradores)
	usuario = models.ForeignKey(User)
	foto = models.ImageField(
		upload_to='profile', null=True, blank=True, default=None)
	sexo = models.CharField(max_length=15, null=True, blank=True, default=None)
	fecha_nacimiento = models.DateField(null=True, blank=True, default=None)
	pasa_tiempos = models.TextField(null=True, blank=True, default=None)
	estado = models.BooleanField(default=True)

class periodos(models.Model):
	"""periodo a evaluar, se llenara una vez, luego automatico
	   hasta que se cambie, se tomara como base el activo"""
	empresa = models.ForeignKey(empresas)
	fecha_inico = models.DateTimeField()
	fecha_fin = models.DateTimeField()
	estado = models.BooleanField(default=True)
	activo = models.NullBooleanField(default=True)
	tiempo = models.IntegerField(default=1, verbose_name='Frecuencia de evaluaciones')
	def year(self):		
		return self.fecha_inico.strftime('%Y')
	
	def anio(self):		
		return self.fecha_fin.strftime('%Y')

	def mesini(self):		
		return self.fecha_inico.strftime('%B')
	
	def mesfina(self):		
		return self.fecha_fin.strftime('%B')

	def __str__(self):
		return str(self.fecha_inico.year)

	
	

class objetivos(models.Model):
	"""objetivo estrategico del criterio"""
	nombre = models.CharField(max_length=30, unique=True)
	estado = models.BooleanField(default=True)

	def __str__(self):
		return self.nombre



class criterios(models.Model):
	"""Al crear no se debe mostrar el periodo ni la empresa, debe guardarse el activo por empresa"""
	empresa = models.ForeignKey(empresas,on_delete=models.PROTECT)
	periodo = models.ForeignKey(periodos,on_delete=models.PROTECT)
	nombre = models.CharField(max_length=120, unique=True)
	descripcion = models.TextField()
	objetivo = models.ForeignKey(objetivos,on_delete=models.PROTECT)
	estado = models.BooleanField(default=True)

	def __str__(self):
		return self.nombre

	def natural_key(self):
		return self.nombre

class evaluaciones(models.Model):
	empresa = models.ForeignKey(empresas)
	periodo = models.ForeignKey(periodos)
	puesto = models.ForeignKey(puestos)
	criterio = models.ForeignKey(criterios, on_delete=models.PROTECT)
	ponderacion = models.DecimalField(max_digits=5, decimal_places=2)
	porcentaje_meta = models.DecimalField(max_digits=5, decimal_places=2)
	estado = models.BooleanField(default=True)

	class Meta:
		permissions = (
			("evaluaciones_roles", "Configurar Roles y permisos"),
			("evaluaciones_listasdesplegables", "Configurar listas de selección"),
			("evaluaciones_usuarios", "Administrar usuarios"),
			("evaluaciones_periodos", "Configurar Períodos"),
			("evaluaciones_criterios", "Configurar Criterios"),
			("eliminar_roles", "Eliminar roles"),
			("eliminar_listasdesplegables", "Eliminar listas de selección"),
			("eliminar_usuarios", "Eliminar usuarios"),
			("eliminar_períodos", "Eliminar períodos"),
			("eliminar_criterios", "Eliminar criterios"),
			("evaluaciones_mis_evaluaciones", "Mis evaluaciones"),
			("evaluaciones_ingresar_cualitativos", "Ingresar nota Criterios Cualitativos"),
			("evaluaciones_ingresar_cuantitativos", "Ingresar nota Criterios Cuantitativos"),
			("evaluaciones_ingresar_sus_cualitativos", "Ingresar sus Criterios Cualitativos"),
			("evaluaciones_ingresar_sus_cuantitativos", "Ingresar sus Criterios Cuantitativos"),
			("especiales_es_supervisor", "Es supervisor")
		)

class evaluacion_colaborador(models.Model):
	empresa = models.ForeignKey(empresas)
	periodo = models.ForeignKey(periodos)
	puesto = models.ForeignKey(puestos)
	evaluacion = models.ForeignKey(evaluaciones)
	colaborador = models.ForeignKey(colaboradores)
	porcentaje = models.DecimalField(max_digits=5, decimal_places=2)
	porcentaje_final = models.DecimalField(max_digits=5, decimal_places=2)
	nota = models.DecimalField(max_digits=5, decimal_places=2)
	estado = models.BooleanField(default=True)
	supervisor = models.ForeignKey(colaboradores,null=True, blank=True, default=None,related_name='supervisor_eval_colab')
	fecha_supervisor = models.DateTimeField(null=True, blank=True, default=None)
	fecha_colaborador = models.DateTimeField(null=True, blank=True, default=None)

class notificaciones(models.Model):
	usuario = models.ForeignKey(User)
	texto = models.CharField(max_length=60)
	url = models.URLField(max_length=200)
	fecha = models.DateField(default=now)
	estado = models.BooleanField(default=True)

## Para la carga de archivos
