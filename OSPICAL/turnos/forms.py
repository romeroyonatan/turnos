# coding=utf-8
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from turnos.models import Especialidad, Empleado
from turnos.validators import PasswordValidator
from django.utils.translation import ugettext_lazy as _
import logging

logger = logging.getLogger(__name__)
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
class RegistrarUsuarioForm(UserCreationForm):
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput,
                                validators=[PasswordValidator(lower=True,number=True,min_length=6)],
                                help_text="Debe contener 6 caracteres como mínimo y al menos una \
                                letra minúscula y un dígito")
    dni = forms.IntegerField()
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2","first_name","last_name")

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        dni = self.cleaned_data["dni"]
        if commit:
            user.save()
            Empleado.objects.create(user=user,dni=dni)
        return user
