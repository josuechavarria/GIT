from django import forms
from .models import empresas, puestos

class empresasForm(forms.ModelForm):
    nombre = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    rtn = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    direccion = forms.CharField(widget=forms.TextInput(attrs={'class':'form-control'}))
    otros_datos = forms.CharField(widget=forms.TextInput(
    attrs={'class': 'form-control'}))
    class Meta:
        model = empresas
        fields = ('nombre', 'rtn','direccion','otros_datos',)

class puestosForm(forms.ModelForm):
    empresa = forms.ModelChoiceField(queryset=empresas.objects.all(
    ),  widget=forms.Select(attrs={'class': 'form-control selectpicker'}))
    perfil = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    nombre = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    orden_jerarquico = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    class Meta:
        model = puestos
        fields = ('empresa', 'perfil', 'nombre', 'orden_jerarquico',)
    pass
