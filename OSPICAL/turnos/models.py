from django.db import models
from django import forms

# Create your models here.
class Afiliado(models.Model):
    numero = models.CharField(max_length=13)
    dni = models.IntegerField()
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)

class Especialidad(models.Model):
    descripcion = models.CharField(max_length=50)
    fecha_baja = models.DateField(null=True)
    def __str__(self):
        return self.descripcion
    
class Consultorio (models.Model):
    numero = models.CharField(max_length=1)
    disponible = models.BooleanField()
    ubicacion = models.CharField(max_length=50, null=True)
    descripcion = models.CharField(max_length=100, null=True)

class Empleado (models.Model):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    dni = models.IntegerField()
    email = models.EmailField()
    usuario = models.CharField(max_length=50)
    password = models.CharField(max_length=50)
    fecha_baja = models.DateField(null=True)

class Reserva(models.Model):
    fecha = models.DateTimeField()
    telefono = models.CharField(max_length=20)
    afiliado = models.ForeignKey(Afiliado)
       
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
    horaDesde = models.PositiveSmallIntegerField()
    horaHasta = models.PositiveSmallIntegerField()
    consultorio = models.ForeignKey(Consultorio, null=True)
    
class Especialista(models.Model):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    dni = models.IntegerField()
    fecha_baja = models.DateField(null=True)
    especialidades = models.ManyToManyField(Especialidad)
    disponibilidad = models.ManyToManyField(Disponibilidad, null=True)

class Turno (models.Model):
    # Constantes ~
    DISPONIBLE = 'D'
    RESERVADO = 'R'
    PRESENTE = 'P'
    AUSENTE = 'A'
    CANCELADO = 'C'
    NO_RESERVADO = 'N'
    ESTADO = (
              (DISPONIBLE,'DISPONIBLE'),
              (RESERVADO,'RESERVADO'),
              (PRESENTE,'PRESENTE'),
              (AUSENTE,'AUSENTE'),
              (CANCELADO,'CANCELADO'),
              (NO_RESERVADO,'NO RESERVADO'),
              )
    # Atributos ~
    fecha = models.DateTimeField()
    estado = models.CharField(max_length=1, choices=ESTADO)
    sobreturno = models.BooleanField()
    consultorio = models.ForeignKey(Consultorio, null=True)
    especialista = models.ForeignKey(Especialista)
    
class LineaDeReserva (models.Model):
    estado = models.CharField(max_length=1, choices=Turno.ESTADO)
    reserva = models.ForeignKey(Reserva)
    turno = models.ForeignKey(Turno)

class HistorialTurno(models.Model):
    fecha = models.DateTimeField()
    estadoAnterior = models.CharField(max_length=1, null=True)
    estadoNuevo = models.CharField(max_length=1)
    descripcion = models.CharField(max_length=100, null=True)
    turno = models.ForeignKey(Turno)
    empleado = models.ForeignKey(Empleado, null=True)
    
