# coding=utf-8
from dateutil.relativedelta import relativedelta
from datetime import timedelta, datetime
from django.test import TestCase
from turnos.models import *
from turnos.bussiness import *
from django.utils import timezone

import logging
logger = logging.getLogger(__name__)
b = Bussiness()

class ReservarTurnoTest(TestCase):
    """Esta clase agrupa las pruebas de reservar turnos"""
    fixtures = ['turnos.json']
        
    def setUp(self):
        TestCase.setUp(self)
    
    def testGetDiasTurnos(self):
        """Verifica el funcionamiento del algoritmo para la obtencion de turnos disponibles.
        Debe obtener una lista con todos los turnos disponibles"""
        # Creando turno
        Turno.objects.create(fecha=timezone.now() + timedelta(days=1),
                             estado=Turno.DISPONIBLE,
                             sobreturno=False,
                             consultorio=Consultorio.objects.get(id=1),
                             ee=EspecialistaEspecialidad.objects.get(id=1),
                             )
        test = b.getDiaTurnos(1)
        self.assertGreaterEqual(len(test), 1)
    
    def testReservarTurno(self):
        """Verifica que se reserve un turno de forma correcta"""
        afiliado_id = 1
        listaTurnos = [2,3,4]
        reserva = b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        lineas = LineaDeReserva.objects.filter(reserva = reserva)
        self.assertIsNotNone(reserva)
        self.assertEqual(reserva.afiliado.id, afiliado_id)
        self.assertEqual(lineas.count(), len(listaTurnos))
        for turno_id in listaTurnos:
            turno = Turno.objects.get(id=turno_id)
            historial = HistorialTurno.objects.latest('id')
            self.assertEqual(turno.estado, Turno.RESERVADO)
            self.assertIsNotNone(historial)
            self.assertEqual(historial.estadoNuevo, turno.estado)
        for lr in lineas:
            self.assertEqual(lr.reserva.id, reserva.id)
            self.assertIn(lr.turno.id, listaTurnos)
            self.assertEqual(lr.estado, Turno.RESERVADO)
    
    def testTurnoInexistente(self):
        """Verifica que pasa si se quiere reservar un turno que no existe.
        Deberia lanzar una excepcion"""
        afiliado_id = 1
        listaTurnos = [2, 4000]
        with self.assertRaises(TurnoNotExistsException):
            b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        turno = Turno.objects.get(id=2)
        self.assertEqual(turno.estado, Turno.DISPONIBLE)
        
    def testAfiliadoInexistente(self):
        """Verifica que pasa si el afiliado no existe. Debe lanzar una excepcion"""
        afiliado_id = 4000
        listaTurnos = [2,3,4]
        with self.assertRaises(AfiliadoNotExistsException):
            b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        last = LineaDeReserva.objects.latest('id')
        self.assertNotIn(last.turno.id, listaTurnos)

    def testTurnoVacio(self):
        """Verifica que pasa si se quiere reservar turnos con una lista de turnos vacia.
        Deberia fallar silenciosamente"""
        afiliado_id = 1
        listaTurnos = []
        reserva = b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        self.assertIsNone(reserva)

    def testSinTelefono(self):
        """Verifica que pasa si se quiere reservar un turno sin telefono de contacto Debe lanzar una excepcion"""
        afiliado_id = 1
        listaTurnos = [1]
        with self.assertRaises(Exception):
            b.reservarTurnos(afiliado_id, None, listaTurnos)
        
    def testTurnoReservado(self):
        """Verifica que pasa si se quiere reservar un turno que esta reservado"""
        afiliado_id = 1
        listaTurnos = [2, 3]
        b.reservarTurnos(afiliado_id, '41234345', [3])
        with self.assertRaises(TurnoReservadoException):
            b.reservarTurnos(afiliado_id, '41234345', listaTurnos)
        turno = Turno.objects.get(id=2)
        self.assertEqual(turno.estado, Turno.DISPONIBLE)
    
    def testPresentismo(self):
        """Verifica el correcto funcionamiento del algoritmo de presentismo, si el 
        afiliado esta en regla"""
        afiliado_id = 1
        p = b.presentismoOK(afiliado_id)
        self.assertTrue(p)
    
    def testCrearSobreturno(self):
        """Verifica que pasa si no hay mas turnos y se deben crear sobreturnos"""
        #TODO: Hacer test crear sobreturno
        #self.assertTrue(False)
        pass
    def testSinSobreturno(self):
        """Verifica que pasa si no hay mas sobreturnos para un dia"""
        #TODO: Hacer test sin sobreturno
        #self.assertTrue(False)
        pass
    
    def testPresentismoNotOK(self):
        """Verifica el funcionamiento del algoritmo de presentismo con un afiliado que falta mucho.
        Debe devolver falso, indicando que el afiliado falta mucho a los turnos"""
        cantidad = b.AUSENTES_CANTIDAD
        afiliado_id = 1
        # Creando turnos
        listaTurnos = range(1000,1000 + cantidad + 1)
        for i in listaTurnos:
            Turno.objects.create(fecha=timezone.now()+timedelta(days=1),
                                 estado=Turno.DISPONIBLE,
                                 sobreturno=False,
                                 consultorio=Consultorio.objects.get(id=1),
                                 ee=EspecialistaEspecialidad.objects.get(id=1),
                                 id = i,)
        reserva = b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        # Reservando turnos
        lineas = LineaDeReserva.objects.filter(reserva = reserva)
        # Marcando turnos como ausente
        for lr in lineas:
            lr.estado = Turno.AUSENTE
            lr.save()
        # Verificando presentismo
        p = b.presentismoOK(afiliado_id)
        self.assertFalse(p)
        
    def testPresentismoExpirado(self):
        """Verifica el funcionamiento del algoritmo de presentismo con faltas anteriores a las 
        que el sistema debe tener en cuenta. Debe devolver verdadero, dado que el sistema no debe
        tener en cuenta faltas anteriores"""
        cantidad = b.AUSENTES_CANTIDAD
        meses = b.AUSENTES_MESES
        afiliado_id = 1
        # Creando turnos
        listaTurnos = range(1000,1000 + cantidad + 1)
        for i in listaTurnos:
            Turno.objects.create(fecha=timezone.now() + relativedelta(months=-meses, days=-1),
                                 estado=Turno.DISPONIBLE,
                                 sobreturno=False,
                                 consultorio=Consultorio.objects.get(id=1),
                                 ee=EspecialistaEspecialidad.objects.get(id=1),
                                 id = i,)
        reserva = b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        reserva.fecha = timezone.now() + relativedelta(months=-meses, days=-1)
        reserva.save()
        # Reservando turnos
        lineas = LineaDeReserva.objects.filter(reserva = reserva)
        # Marcando turnos como ausente
        for lr in lineas:
            lr.estado = Turno.AUSENTE
            lr.save()
        # Verificando presentismo
        p = b.presentismoOK(afiliado_id)
        self.assertTrue(p)
    
    def testFatiga(self):
        """Reserva una alta cantidad de turnos para verificar como se comporta el algoritmo de reserva.
        Debe reservar los turnos en un tiempo razonable a la cantidad de turnos a reservar"""
        afiliado_id = 1
        listaTurnos = range(1000,1100)
        for i in listaTurnos:
            Turno.objects.create(fecha=timezone.now(),
                                 estado=Turno.DISPONIBLE,
                                 sobreturno=False,
                                 consultorio=Consultorio.objects.get(id=1),
                                 ee=EspecialistaEspecialidad.objects.get(id=1),
                                 id = i,)
        reserva = b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        lineas = LineaDeReserva.objects.filter(reserva = reserva)
        self.assertIsNotNone(reserva)
        self.assertEqual(reserva.afiliado.id, afiliado_id)
        self.assertEqual(lineas.count(), len(listaTurnos))
        for turno_id in listaTurnos:
            turno = Turno.objects.get(id=turno_id)
            historial = HistorialTurno.objects.latest('id')
            self.assertEqual(turno.estado, Turno.RESERVADO)
            self.assertIsNotNone(historial)
            self.assertEqual(historial.estadoNuevo, turno.estado)
        for lr in lineas:
            self.assertEqual(lr.reserva.id, reserva.id)
            self.assertIn(lr.turno.id, listaTurnos)
            self.assertEqual(lr.estado, Turno.RESERVADO)

class CrearTurnoTest(TestCase):
    """Esta clase agrupa las pruebas de crear turnos"""
    fixtures = ['turnos.json']
    def testUnDia(self):
        """Crea turnos para un dia. Debe devolver una lista con mas de un turno"""
        ee = EspecialistaEspecialidad.objects.get(id=1)
        turnos = b.crear_turnos_del_especialista(ee, 1)
        self.assertGreater(len(turnos), 1)
    def test8Dias(self):
        """Crea una semana de turnos. Debe devolver una lista de turnos creados"""
        DIAS = 8
        ee = EspecialistaEspecialidad.objects.get(id=1)
        turnos = b.crear_turnos_del_especialista(ee, DIAS)
        exito = False
        for turno in turnos:
            diff = turno.fecha.replace(tzinfo=None) - (datetime.now() + timedelta(days=DIAS - 1))
            exito = exito or diff.days == 0
        self.assertTrue(exito)
    def test365Dias(self):
        """Crea un año de turnos y verifica que sea correcto. Debe devolver una lista de turnos creados"""
        DIAS = 365
        ee = EspecialistaEspecialidad.objects.get(id=1)
        turnos = b.crear_turnos_del_especialista(ee, DIAS)
        exito = False
        for turno in turnos:
            diff = turno.fecha.replace(tzinfo=None) - (datetime.now() + timedelta(days=DIAS - 1))
            exito = exito or diff.days == 0
        self.assertTrue(exito)
    def testDosAnos(self):
        """Crea turnos a dos años. Debe devolver una lista de turnos creados"""
        DIAS = 365 * 2
        ee = EspecialistaEspecialidad.objects.get(id=1)
        turnos = b.crear_turnos_del_especialista(ee, DIAS)
        exito = False
        for turno in turnos:
            diff = turno.fecha.replace(tzinfo=None) - (datetime.now() + timedelta(days=DIAS - 1))
            exito = exito or diff.days == 0
        self.assertTrue(exito)
    def testDiasNegativos(self):
        """Prueba que pasa si se pasan dias negativos a crear turnos. Debe devolver una lista de turnos creados"""
        DIAS = -7
        ee = EspecialistaEspecialidad.objects.get(id=1)
        turnos = b.crear_turnos_del_especialista(ee, DIAS)
        self.assertFalse(turnos)
    def testSinDias(self):
        """Prueba que pasa si se llama a la funcion de crear sin indicarle el numero de dias. 
        Debe devolver una lista de turnos creados"""
        ee = EspecialistaEspecialidad.objects.get(id=1)
        turnos = b.crear_turnos_del_especialista(ee)
        self.assertTrue(turnos)
    def testTurnosExistentes(self):
        """Prueba de crear turnos si todos los turnos a crear ya existen (doble llamada a la funcion).
        Debe devolver una lista vacia de turnos creados, fallando silenciosamente"""
        fecha = datetime(2014,1,20,12,30, tzinfo=timezone.utc)
        ee = EspecialistaEspecialidad.objects.get(id=1)
        b.crear_turnos_del_especialista(ee, 1, fecha) # Creamos los turnos
        antes = Turno.objects.all().count() # contamos la cantidad de elementos antes de crear
        creados = b.crear_turnos_del_especialista(ee, 1, fecha)  # No deberia dejarlo crear nuevamente. Falla silenciosa
        despues = Turno.objects.all().count() # contamos la cantidad de elementos despues de crear
        self.assertFalse(creados)
        # verifico que se hayan creado en la base de datos correctamente
        self.assertEqual(antes, despues)
    def testAlgunosExistentes(self):
        """Prueba de crear turnos si hay un turno existente.
        Debe devolver una lista de turnos creados y el turno existente no debe estar en esa lista"""
        fecha = datetime(2014,1,20,12,30, tzinfo=timezone.utc)
        ee = EspecialistaEspecialidad.objects.get(id=1)
        turno = Turno.objects.create(fecha=fecha,
                                     ee=ee,
                                     sobreturno=False,
                                     estado=Turno.RESERVADO)
        antes = Turno.objects.all().count() # contamos la cantidad de elementos antes de crear
        creados = b.crear_turnos_del_especialista(ee,a_partir_de=fecha)
        despues = Turno.objects.all().count() # contamos la cantidad de elementos despues de crear
        self.assertTrue(turno not in creados)
        # verifico que se hayan creado en la base de datos correctamente
        self.assertEqual(antes + len(creados), despues) 
    def testProximoDia(self):
        """Prueba para obtener el proximo dia a partir de una fecha conocida.
        Debe devolver mismo dia conocido"""
        base = datetime(2014,01,01) # miercoles
        target = datetime(2014,01,04) # sabado
        dia = 5 # sabado
        fecha = b._Bussiness__proximoDia(dia, base)
        self.assertEquals(target, fecha)
    def testSinDisponibilidad(self):
        """Prueba que pasa si se crean turnos de un especialista que no posee disponibilidad.
        Debe devolver una lista vacia, fallando silenciosamente"""
        es=Especialidad.objects.get(id=1)
        e=Especialista.objects.create(nombre='n',apellido='n',dni=1234)
        ee = EspecialistaEspecialidad.objects.create(especialista=e, especialidad=es)
        turnos = b.crear_turnos_del_especialista(ee)
        self.assertFalse(turnos)
