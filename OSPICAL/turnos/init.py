# coding=utf-8
from turnos.models import *
from datetime import datetime
from datetime import timedelta
from django.contrib.auth.models import User

a = Afiliado(nombre='Yonatan',apellido='Romero',dni=12345678,numero='000100020003')
a.save()

b = Afiliado(nombre='Un duplicado',apellido='Perez',dni=12345678,numero='000100020033')
b.save()

e=Especialidad(descripcion=u'Odontología')
e.save()

c=Consultorio(numero='1',disponible=True)
c.save()


user = User.objects.create_user(username='operador',
                                 email='operador@ospical.org.ar',
                                 password='qwerty')

em=Empleado(user=user,dni=44556677)
em.save()

d=Disponibilidad(dia='0',horaDesde=1230,horaHasta=1900,consultorio=c)
d.save()

es=Especialista(nombre=u'María de los ángeles', apellido=u'Fernández',dni=11559977)
es.save()
es.disponibilidad.add(d)

ee=EspecialistaEspecialidad(especialista=es, especialidad=e)
ee.save()

fecha = datetime.now() + timedelta(days=4*365)
for i in range (1,20):
    fecha = fecha + timedelta(minutes=15)
    turno = Turno(fecha=fecha, estado=Turno.DISPONIBLE,sobreturno=False,consultorio=c, ee=ee)
    turno.save()

r=Reserva(fecha=datetime.now(),telefono='41234345',afiliado=a)
r.save()

lr=LineaDeReserva(estado=Turno.CANCELADO,reserva=r,turno=turno)
lr.save()

