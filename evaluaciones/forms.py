from django import forms
from django.forms import ModelForm, CharField, ImageField, ModelChoiceField, Select, FileInput, TextInput, Textarea, IntegerField
from .models import *
from django.contrib.auth.models import User, Group

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
