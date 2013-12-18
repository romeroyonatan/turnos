from turnos.models import *
import datetime

a = Afiliado(nombre='Yonatan',apellido='Romero',dni=12345678,numero='000100020003')
a.save()

b = Afiliado(nombre='Un duplicado',apellido='Perez',dni=12345678,numero='000100020033')
b.save()

e=Especialidad(descripcion="Odontología")
e.save()

c=Consultorio(numero='1',disponible=True)
c.save()

em=Empleado(nombre='Fernando',apellido='Peña',dni=44556677,email='fpeña@ospical.org.ar',usuario='fpeña',password='123456')
em.save()

d=Disponibilidad(dia='0',horaDesde=1230,horaHasta=1900,consultorio=c)
d.save()

es=Especialista(nombre='María de los ángeles', apellido='Fernández',dni=11559977)
es.save()
es.disponibilidad.add(d)

ee=EspecialistaEspecialidad(especialista=es, especialidad=e)
ee.save()

_fecha=datetime.datetime.now() + datetime.timedelta(days=3)
t=Turno(fecha=_fecha,estado=Turno.DISPONIBLE,sobreturno=False,consultorio=c,ee=ee)
t.save()

_fecha=_fecha + datetime.timedelta(minutes=15)
t2=Turno(fecha=_fecha,estado=Turno.DISPONIBLE,sobreturno=False,consultorio=c,ee=ee)
t2.save()


r=Reserva(fecha=datetime.datetime.now(),telefono='41234345',afiliado=a)
r.save()

lr=LineaDeReserva(estado=Turno.CANCELADO,reserva=r,turno=t)
lr.save()




from turnos.models import *
from datetime import datetime
from datetime import timedelta
ee = EspecialistaEspecialidad.objects.get(id=1)
consultorio = Consultorio.objects.get(id=1)
fecha = datetime.now() + timedelta(years=4)
for i in range (1,20):
    fecha = fecha + timedelta(minutes=15)
    turno = Turno(fecha=fecha, estado=Turno.DISPONIBLE,sobreturno=False,consultorio=consultorio, ee=ee)
    turno.save()
