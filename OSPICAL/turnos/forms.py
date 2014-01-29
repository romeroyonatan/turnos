from django import forms
from turnos.models import Especialidad

class ReservarTurnoForm(forms.Form):
    dni = forms.IntegerField(widget=forms.TextInput())
    numero = forms.IntegerField(widget=forms.TextInput())
    nombre = forms.CharField(widget=forms.TextInput(attrs={'disabled':'disabled'}),
                             required=False)
    apellido = forms.CharField(widget=forms.TextInput(attrs={'disabled':'disabled'}),
                               required=False)
    telefono = forms.CharField()
    especialidad = forms.ModelChoiceField(queryset=Especialidad.objects.all(),
                                          empty_label="Seleccionar especialidad",
                                          required=False)
    especialista = forms.IntegerField(widget=forms.Select(attrs={'disabled':'disabled'}),
                                      required=False)
    dia = forms.IntegerField(widget=forms.Select(attrs={'disabled':'disabled'}),
                             required=False)
    hora = forms.IntegerField(widget=forms.Select(attrs={'disabled':'disabled'}),
                              required=False)
    turnos = forms.CharField(widget=forms.HiddenInput(),required=False)
    afiliado = forms.CharField(widget=forms.HiddenInput())

class CrearTurnoForm(forms.Form):
    dias = forms.IntegerField()
