from django import forms
from django.forms import ModelForm, CharField, ImageField,DateField, ModelChoiceField, Select, FileInput, TextInput, Textarea, IntegerField,CheckboxInput
from .models import *
from django.contrib.auth.models import User, Group

class usuariosForm(ModelForm):
    #supervisor = forms.ModelChoiceField(queryset=colaboradores.objects.filter(puesto__nombre__upper='SUPERVISOR'),required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    class Meta:
        model = colaboradores
        exclude = ('usuario','usuario_creador', 'fecha_creacion', 'usuario_modificador', 'fecha_modificacion', 'fecha_ult_mod_password')

class empresasForm(ModelForm):
    nombre = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    rtn = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    licencias = forms.IntegerField(widget=forms.TextInput(attrs={'class':'form-control'}))
    direccion = forms.CharField(widget=forms.Textarea(attrs={'class':'form-control','rows':'2'}))
    otros_datos = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control','rows':'2'}))
    logo = forms.ImageField(widget=forms.FileInput(attrs={'class': 'form-control'}))
    class Meta:
        model = empresas
        fields = ('nombre', 'rtn', 'licencias','direccion','otros_datos','logo')

class empresasFormEdit(ModelForm):
    class Meta:
        model = empresas
        fields = ('nombre', 'rtn', 'licencias','direccion','otros_datos','logo')
        widgets = {
            'nombre': TextInput(attrs={'class': 'form-control'}),
            'rtn': TextInput(attrs={'class': 'form-control'}),
            'licencias' : TextInput(attrs={'class': 'form-control'}),
            'direccion': Textarea(attrs={'class':'form-control','rows':'2'}),
            'otros_datos': Textarea(attrs={'class':'form-control','rows':'2'}),
        }

class puestosForm(ModelForm):
    empresa = forms.ModelChoiceField(queryset=empresas.objects.all(),  widget=forms.Select(attrs={'class': 'form-control'}))
    #perfil = forms.ModelChoiceField(queryset=Group.objects.all(),  widget=forms.Select(attrs={'class': 'form-control'}))
    nombre = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    orden_jerarquico = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta:
        model = puestos
        fields = ('empresa', 'nombre', 'orden_jerarquico',)

class DepartamentosForm(ModelForm):
    class Meta:
        model = departamentos
        fields = ('empresa', 'nombre')
        widgets = {
            'empresa': Select(attrs={'class': 'form-control'}),
            'nombre': TextInput(attrs={'class': 'form-control'}),
        }

class SucursalesForm(ModelForm):
    class Meta:
        model = sucursales
        fields = ('empresa', 'nombre', 'direccion', 'otros_datos')
        widgets = {
            'empresa': Select(attrs={'class': 'form-control'}),
            'nombre': TextInput(attrs={'class': 'form-control'}),
            'direccion': Textarea(attrs={'class':'form-control','rows':'2'}),
            'otros_datos': Textarea(attrs={'class':'form-control','rows':'2'}),
        }

class CriteriosForm(ModelForm):
    class Meta:
        model = criterios
        fields = ('empresa', 'nombre', 'descripcion','objetivo','periodo')
        widgets = {
            'empresa': Select(attrs={'class': 'form-control'}),            
            'nombre': TextInput(attrs={'class': 'form-control'}),
            'descripcion': TextInput(attrs={'class': 'form-control'}),            
            'objetivo': Select(attrs={'class': 'form-control'}),            
        }
        exclude = ('periodo',)
class PeriodosForm(ModelForm):
    class Meta:
        model = periodos
        fields = ('empresa','fecha_inico', 'fecha_fin','tiempo', 'activo')
        widgets = {
            'empresa': Select(attrs={'class': 'form-control'}), 
            'fecha_inico': forms.DateInput( format = '%Y-%m-%d',attrs={'class':'datepicker'}),
            'fecha_fin': forms.DateInput( format = '%Y-%m-%d',attrs={'class':'datepicker'}),
            'activo': CheckboxInput(attrs={'class': 'checkbox'}),                      
            'tiempo': TextInput(attrs={'class': 'form-control'}),
        }

class objetivosForm(ModelForm):
    nombre = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))    
    class Meta:
        model = objetivos
        fields = ('nombre',)


class objetivosFormEdit(ModelForm):
    nombre = forms.CharField(widget=forms.TextInput(
        attrs={'class': 'form-control'}))

    class Meta:
        model = objetivos
        fields = ('nombre',)


class PerfilForm(ModelForm):
    CATEGORY_CHOICES = (('', '-----------------'), ('F', 'FEMENINO'), ('M', 'MASCULINO'),)
    foto =  forms.ImageField(widget=forms.FileInput(attrs={'class': 'form-control'}))    
    sexo = forms.ChoiceField(choices=CATEGORY_CHOICES, widget=forms.Select(
        attrs={'class': 'form-control'}))
    fecha_nacimiento = forms.CharField(widget=forms.DateInput( format = '%Y-%m-%d',attrs={'class': 'datepicker'}),required = False)                                      
    pasa_tiempos = forms.CharField(widget=forms.Textarea(attrs={'class':'form-control'}))
    class Meta:
        model = perfil         
        fields = ('foto','sexo','fecha_nacimiento','pasa_tiempos')        
        

class EvaluacionesForm(ModelForm):
    class Meta:
        model = evaluaciones
        fields = ('empresa','periodo', 'puesto','criterio', 'ponderacion','porcentaje_meta','estado')
        widgets = {
            'empresa': Select(attrs={'class': 'form-control'}), 
            'periodo': Select(attrs={'class': 'form-control'}),
            'puesto':  Select(attrs={'class': 'form-control'}), 
            'criterio': Select(attrs={'class': 'form-control'}), 
            'ponderacion': TextInput(attrs={'class': 'form-control'}),
            'porcentaje': TextInput(attrs={'class': 'form-control'}) 
        }
        exclude = ('periodo','criterio', 'ponderacion','porcentaje_meta', 'estado')






