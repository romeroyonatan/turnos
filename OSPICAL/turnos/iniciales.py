# coding=utf-8
from turnos.models import *
from datetime import datetime
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User, Permission

a = Afiliado(nombre='Yonatan',apellido='Romero',dni=12345678,numero='000100020003')
a.save()

b = Afiliado(nombre='Un duplicado',apellido='Perez',dni=12345678,numero='000100020033')
b.save()

e=Especialidad(descripcion=u'Odontología')
e.save()

c=Consultorio(numero='1',disponible=True)
c.save()

r = Permission.objects.get(codename="reservar_turnos")
c = Permission.objects.get(codename="crear_turnos")
p = Permission.objects.get(codename="add_user")
user = User.objects.create_user(username='operador',
                                 email='operador@ospical.org.ar',
                                 password='qwerty')
user.user_permissions = [r]

em=Empleado(user=user,dni=44556677)
em.save()


es=Especialista(nombre=u'María de los ángeles', apellido=u'Fernández',dni=11559977)
es.save()

ee=EspecialistaEspecialidad(especialista=es, especialidad=e)
ee.save()

d=Disponibilidad(dia='0',horaDesde='12:30',horaHasta='19:00', ee = ee, consultorio=c)
d.save()

Disponibilidad.objects.create(dia='1',horaDesde='12:30',horaHasta='13:00', ee = ee,)
Disponibilidad.objects.create(dia='2',horaDesde='12:30',horaHasta='13:00', ee = ee,)
Disponibilidad.objects.create(dia='3',horaDesde='12:30',horaHasta='13:00', ee = ee,)
Disponibilidad.objects.create(dia='4',horaDesde='12:30',horaHasta='13:00', ee = ee,)
Disponibilidad.objects.create(dia='5',horaDesde='12:30',horaHasta='13:00', ee = ee,)
Disponibilidad.objects.create(dia='6',horaDesde='12:30',horaHasta='13:00', ee = ee,)

fecha = datetime.now() + timedelta(days=4*365)
for i in range (1,20):
    fecha = fecha + timedelta(minutes=15)
    turno = Turno(fecha=fecha, estado=Turno.DISPONIBLE,sobreturno=False,consultorio=c, ee=ee)
    HistorialTurno.objects.create(fecha=timezone.now(),turno=turno,estadoNuevo=Turno.DISPONIBLE,)
    turno.save()

r=Reserva(fecha=datetime.now(),telefono='41234345',afiliado=a)
r.save()

lr=LineaDeReserva(estado=Turno.CANCELADO,reserva=r,turno=turno)
lr.save()


# Cantidad de meses que se tendran en cuenta para el calculo de presentismo
Settings.objects.create(key="ausente_meses",value="6")
# Cantidad de ausentes maximos que se tendran en cuenta para no declarar al afiliado como ausente recurrente 
Settings.objects.create(key="ausente_cantidad",value="3")
# Minutos entre turnos al crearlos
Settings.objects.create(key="crear_minutos_entre_turnos",value="15")
# Cantidad de dias que se crearan los turnos
Settings.objects.create(key="crear_cantidad_dias_turnos",value="7")

