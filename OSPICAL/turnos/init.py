from turnos.models import *
import datetime

a = Afiliado(nombre='Yonatan',apellido='Romero',dni=12345678,numero='000100020003')
a.save()

b = Afiliado(nombre='Un duplicado',apellido='Perez',dni=12345678,numero='000100020033')
b.save()

e=Especialidad(descripcion="Odontologia")
e.save()

c=Consultorio(numero='1',disponible=True)
c.save()

em=Empleado(nombre='Fernando',apellido='Peña',dni=44556677,email='fpeña@ospical.org.ar',usuario='fpeña',password='123456')
em.save()

d=Disponibilidad(dia='0',horaDesde=1230,horaHasta=1900,consultorio=c)
d.save()

es=Especialista(nombre='María de los ángeles', apellido='Fernández',dni=11559977)
es.especialidades.add(e)
es.disponibilidad.add(d)
es.save()

_fecha=datetime.datetime.now() + datetime.timedelta(days=3)
t=Turno(fecha=_fecha,estado=Turno.DISPONIBLE,sobreturno=False,consultorio=c,especialista=es)
t.save()


