from django import forms

class ReservarTurnoForm(forms.Form):
    OPCIONES = (("0", "Seleccionar especialidad"),)
    dni = forms.IntegerField()
    numero = forms.IntegerField()
    telefono = forms.CharField()
    especialidad = forms.ChoiceField(choices=OPCIONES)
    especialista = forms.ChoiceField(choices=OPCIONES)
    dia = forms.ChoiceField(choices=OPCIONES)
    hora = forms.ChoiceField(choices=OPCIONES)
    turnos = forms.CharField(widget=forms.HiddenInput())