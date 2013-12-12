from django import forms
from turnos.models import Especialidad

class ReservarTurnoForm(forms.Form):
    OPCIONES = (("0", "Seleccionar"),)
    dni = forms.IntegerField()
    numero = forms.IntegerField()
    nombre = forms.CharField(widget=forms.TextInput(attrs={'disabled':'disabled'}))
    apellido = forms.CharField(widget=forms.TextInput(attrs={'disabled':'disabled'}))
    telefono = forms.CharField()
    
    especialidad = forms.ModelChoiceField(queryset=Especialidad.objects.all(),
                                          empty_label="Seleccionar especialidad")
    
    especialista = forms.ChoiceField(choices=OPCIONES,
                                     widget=forms.Select(attrs={'disabled':'disabled'}))
    
    dia = forms.ChoiceField(choices=OPCIONES,
                            widget=forms.Select(attrs={'disabled':'disabled'}))
    
    hora = forms.ChoiceField(choices=OPCIONES,
                             widget=forms.Select(attrs={'disabled':'disabled'}))
    
    turnos = forms.CharField(widget=forms.HiddenInput())
    afiliado = forms.CharField(widget=forms.HiddenInput())
