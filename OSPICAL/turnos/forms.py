# coding=utf-8
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Permission
from django.db import transaction
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import MultipleObjectsReturned
from models import *
from validators import PasswordValidator
import logging
import json
from django.forms.widgets import Widget

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
    CREAR_TURNO = "crear_turnos"
    RESERVAR_TURNO = "reservar_turnos"
    CANCELAR_RESERVA = "cancelar_reserva"
    CANCELAR_TURNOS = "cancelar_turnos"
    CREAR_USUARIOS = "add_user"
    PERMISOS = ((RESERVAR_TURNO,"Reservar turnos"),
                (CANCELAR_RESERVA,"Cancelar reservas"),
                (CREAR_TURNO,"Crear turnos"),
                (CANCELAR_TURNOS, "Cancelar turnos"),
                (CREAR_USUARIOS, "Crear usuarios"),)
    password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput,
                                validators=[PasswordValidator(lower=True,number=True,min_length=6)],
                                help_text="Debe contener 6 caracteres como mínimo y al menos una \
                                letra minúscula y un dígito")
    dni = forms.IntegerField()
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    permisos = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,choices=PERMISOS)
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
            for codename in self.cleaned_data["permisos"]:
                p = Permission.objects.get(codename=codename)
                user.user_permissions.add(p)
        return user
class ConfirmarTurnoForm(forms.Form):
    choices = [('','Ingrese el número de afiliado')]
    afiliado = forms.IntegerField(widget=forms.HiddenInput())
    numero = forms.CharField()
    # XXX:Esta asi para que no me valide lo que envio el usuario con las opciones especificadas
    # dado que lo completo mediante ajax
    turnos = forms.CharField(widget=forms.Select(choices=choices))
class CancelarReservaForm(forms.Form):
    choices = [('','Ingrese el número de afiliado')]
    next = forms.CharField(widget=forms.HiddenInput)
    afiliado = forms.IntegerField(widget=forms.HiddenInput)
    numero = forms.CharField(label="Número de afiliado")
    dni = forms.IntegerField(label="DNI", widget=forms.TextInput())
    # XXX:Esta asi para que no me valide lo que envio el usuario con las opciones especificadas
    # dado que lo completo mediante ajax
    turnos = forms.CharField(widget=forms.Select(choices=choices))
    motivo = forms.CharField(widget=forms.Textarea,label="Motivo",required=False)
    def __init__(self, lr=None, *args, **kwargs):
        super(CancelarReservaForm, self).__init__(*args, **kwargs)
        if lr is not None:
            self.fields['turnos'].widget = forms.Select(choices=[(lr.id, lr.turno.ee.especialidad.descripcion)])
class CancelarTurnoForm(forms.Form):
    especialidad = forms.ModelChoiceField(queryset=Especialidad.objects.all())
    especialista = forms.ModelChoiceField(queryset=Especialista.objects.all(),
                                          widget=forms.Select(attrs={'disabled':'disabled'}))
    fecha = forms.IntegerField(widget=forms.Select(attrs={'disabled':'disabled'}))
class RegistarEspecialistaForm(forms.Form):
    error_messages = {
        'duplicate_dni': "Ya existe un especialista registrado con ese DNI",
    }
    nombre = forms.CharField(max_length="50", required=True)
    apellido = forms.CharField(max_length="50")
    dni = forms.CharField()
    especialidad = forms.ModelChoiceField(queryset=Especialidad.objects.all())
    consultorio = forms.ModelChoiceField(queryset=Consultorio.objects.all())
    dia = forms.ChoiceField(choices=Disponibilidad.DIA)
    desde = forms.CharField(max_length="7", label="Horario")
    hasta = forms.CharField(max_length="7")
    frecuencia = forms.IntegerField(label="Frecuencia entre turnos (en minutos)")
    disponibilidades = forms.CharField(widget=forms.HiddenInput, required=False)
    def clean_dni(self):
        dni = self.cleaned_data["dni"]
        try:
            Especialista.objects.get(dni=dni)
        except Especialista.DoesNotExist:
            return dni
        raise forms.ValidationError(
            self.error_messages['duplicate_dni'],
            code='duplicate_dni',
        )
    def clean_disponibilidades(self):
        disponibilidades = list()
        lista = json.loads(self.cleaned_data["disponibilidades"]) if self.cleaned_data["disponibilidades"] else None
        if lista:
            for item in lista:
                disponibilidades.append(Disponibilidad(dia=item['dia_id'],
                                       horaDesde=item['desde'],
                                       horaHasta=item['hasta'],
                                       consultorio=Consultorio.objects.get(id=item['consultorio'])))
        else:
            disponibilidades.append(Disponibilidad(dia=self.cleaned_data["dia"],
                                   horaDesde=self.cleaned_data["desde"],
                                   horaHasta=self.cleaned_data["hasta"],
                                   consultorio=self.cleaned_data["consultorio"]))
        return disponibilidades
    @transaction.commit_on_success()
    def save(self):
        especialista = Especialista.objects.create(nombre=self.cleaned_data["nombre"],
                                    apellido=self.cleaned_data["apellido"],
                                    dni=self.cleaned_data.get("dni"))
        logger.info("Registrando especialista %s" % especialista)
        ee = EspecialistaEspecialidad.objects.create(especialista=especialista,
                                                     especialidad=self.cleaned_data["especialidad"],
                                                     frecuencia_turnos=self.cleaned_data["frecuencia"])
        disponibilidades = self.cleaned_data["disponibilidades"]
        for disponibilidad in disponibilidades:
            disponibilidad.ee=ee
        logger.debug("Guardando disponibilidades %s" % disponibilidades)
        Disponibilidad.objects.bulk_create(disponibilidades)
        return especialista
class ConsultarReservaForm(forms.Form):
    error_messages = {
        'multiple_object_returned': "DNI duplicado. Intente buscar por numero de afiliado",
        'does_not_exists': "Afiliado inexistente"
    }
    choices = [('',"---------"),
               (Turno.RESERVADO,'Reservado'),
               (Turno.CANCELADO,'Cancelado'),
               (Turno.AUSENTE,'Ausente'),
               (Turno.PRESENTE,'Presente'),]
    especialidad = forms.ModelChoiceField(queryset=Especialidad.objects.all(), required=False)
    especialista = forms.ModelChoiceField(queryset=Especialista.objects.all(), required=False)
    fecha_turno = forms.DateField(required=False)
    fecha_reserva = forms.DateField(required=False)
    afiliado = forms.IntegerField(required=False, help_text="Puede ingresar numero de afiliado o DNI")
    estado = forms.ChoiceField(choices=choices,required=False)
    def clean_afiliado(self):
            try:
                parametro = self.cleaned_data["afiliado"]
                afiliado = Afiliado.objects.get(Q(dni=parametro)|Q(numero=parametro)) if parametro else None
                return afiliado
            except Afiliado.DoesNotExist:
                raise forms.ValidationError(
                    self.error_messages['does_not_exists'],
                    code='does_not_exists',
                )
            except MultipleObjectsReturned:
                raise forms.ValidationError(
                    self.error_messages['multiple_object_returned'],
                    code='multiple_object_returned',
                )