from django.db import models
from django.forms.models import model_to_dict
from django.contrib.auth.models import User

class Afiliado(models.Model):
    numero = models.CharField(max_length=13, unique=True)
    dni = models.IntegerField()
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    def __str__(self):
        return u"%s" % model_to_dict(self)
    def full_name(self):
        return u"%s, %s" % (self.apellido, self.nombre)

class Especialidad(models.Model):
    descripcion = models.CharField(max_length=50)
    fecha_baja = models.DateField(null=True, blank=True)
    def __str__(self):
        return u'%s' % self.descripcion
    def __unicode__(self):
        return u'%s' % self.descripcion
class Consultorio (models.Model):
    numero = models.CharField(max_length=4)
    disponible = models.BooleanField()
    ubicacion = models.CharField(max_length=50, null=True, blank=True)
    descripcion = models.CharField(max_length=100, null=True, blank=True)
    def __str__(self):
        return "%s" % model_to_dict(self)
    def __unicode__(self):
        return "%s" % self.numero
class Empleado (models.Model):
    user = models.ForeignKey(User, unique=True)
    dni = models.IntegerField()
    def __str__(self):
        return "%s" % model_to_dict(self)

class Reserva(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    telefono = models.CharField(max_length=20)
    afiliado = models.ForeignKey(Afiliado)
    def __str__(self):
        return "%s" % model_to_dict(self)
    
class Especialista(models.Model):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    dni = models.IntegerField(unique=True)
    fecha_baja = models.DateField(null=True)
    def __str__(self):
        return "%s" % model_to_dict(self)
    def full_name(self):
        return "%s, %s" % (self.apellido, self.nombre)
    def __unicode__(self):
        return u'%s' % self.full_name()
class EspecialistaEspecialidad(models.Model):
    unique_together = ("especialista", "especialidad")
    especialista = models.ForeignKey(Especialista)
    especialidad = models.ForeignKey(Especialidad)
    frecuencia_turnos = models.SmallIntegerField(default=15)
    fechaBaja = models.DateField(null=True)
    def __str__(self):
        return "%s" % model_to_dict(self)

class Disponibilidad(models.Model):
    # Constantes ~
    LUNES = '0'
    MARTES = '1'
    MIERCOLES = '2'
    JUEVES = '3'
    VIERNES = '4'
    SABADO = '5'
    DOMINGO = '6'
    DIA = (
           (LUNES, "LUNES"),
           (MARTES, "MARTES"),
           (MIERCOLES, "MIERCOLES"),
           (JUEVES, "JUEVES"),
           (VIERNES, "VIERNES"),
           (SABADO, "SABADO"),
           (DOMINGO, "DOMINGO"),
           )
    # Atributos ~
    dia = models.CharField(max_length=1, choices=DIA)
    horaDesde = models.TimeField()
    horaHasta = models.TimeField()
    consultorio = models.ForeignKey(Consultorio, null=True)
    ee = models.ForeignKey(EspecialistaEspecialidad)
    def __str__(self):
        return "%s" % model_to_dict(self)

class Turno (models.Model):
    unique_together = ("fecha", "ee", "sobreturno")
    # Constantes ~
    DISPONIBLE = 'D'
    RESERVADO = 'R'
    PRESENTE = 'P'
    AUSENTE = 'A'
    CANCELADO = 'C'
    NO_RESERVADO = 'N'
    ESTADO = ((DISPONIBLE,'DISPONIBLE'),
              (RESERVADO,'RESERVADO'),
              (PRESENTE,'PRESENTE'),
              (AUSENTE,'AUSENTE'),
              (CANCELADO,'CANCELADO'),
              (NO_RESERVADO,'NO RESERVADO'),)
    # Atributos ~
    creado = models.DateTimeField(auto_now_add=True)
    fecha = models.DateTimeField()
    estado = models.CharField(max_length=1, choices=ESTADO)
    sobreturno = models.BooleanField(default=False)
    consultorio = models.ForeignKey(Consultorio, null=True)
    ee = models.ForeignKey(EspecialistaEspecialidad)
    def __str__(self):
        return "%s" % model_to_dict(self)
    def __eq__(self, other):
        return (self.fecha == other.fecha and 
                self.sobreturno == other.sobreturno and 
                self.ee == other.ee)
    class Meta:
        permissions = (
            # Permission identifier     human-readable permission name
            ("crear_turnos",                  "Crear turnos"),
            ("reservar_turnos",               "Reservar turnos"),
            ("cancelar_turnos",               "Cancelar turnos"),
        )
        
class LineaDeReserva (models.Model):
    estado = models.CharField(max_length=1, choices=Turno.ESTADO)
    reserva = models.ForeignKey(Reserva)
    turno = models.ForeignKey(Turno)
    def __str__(self):
        return "%s" % model_to_dict(self)
class HistorialTurno(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    estadoAnterior = models.CharField(max_length=1, null=True, choices=Turno.ESTADO)
    estadoNuevo = models.CharField(max_length=1, choices=Turno.ESTADO)
    descripcion = models.CharField(max_length=100, null=True)
    turno = models.ForeignKey(Turno)
    empleado = models.ForeignKey(Empleado, null=True)
    def __str__(self):
        return "%s" % model_to_dict(self)
class Settings(models.Model):
    """Esta clase almacenara en la base de datos la configuracion de la aplicacion"""
    key = models.CharField(primary_key=True, max_length=255)
    value = models.CharField(max_length=255)
    def __str__(self):
        return "%s" % model_to_dict(self)