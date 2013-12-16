from django import forms
from turnos.models import Especialidad
from django.core.validators import validate_comma_separated_integer_list
class ReservarTurnoForm(forms.Form):
    dni = forms.IntegerField()
    numero = forms.IntegerField()
    nombre = forms.CharField(widget=forms.TextInput(attrs={'disabled':'disabled'}),required=False)
    apellido = forms.CharField(widget=forms.TextInput(attrs={'disabled':'disabled'}),required=False)
    telefono = forms.CharField()
    especialidad = forms.ModelChoiceField(queryset=Especialidad.objects.all(),
                                          empty_label="Seleccionar especialidad")
    especialista = forms.IntegerField(widget=forms.Select(attrs={'disabled':'disabled'}))
    dia = forms.IntegerField(widget=forms.Select(attrs={'disabled':'disabled'}))
    hora = forms.IntegerField(widget=forms.Select(attrs={'disabled':'disabled'}))
    turnos = forms.CharField(widget=forms.HiddenInput(),required=False)
    afiliado = forms.CharField(widget=forms.HiddenInput())
