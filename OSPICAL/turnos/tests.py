# coding=utf-8
from dateutil.relativedelta import relativedelta
from datetime import timedelta, datetime
from turnos.models import *
from turnos.bussiness import *
from turnos.validators import PasswordValidator
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

import logging
from models import *
from bussiness import *
logger = logging.getLogger(__name__)
b = Bussiness()

class ReservarTurnoTest(TestCase):
    """Esta clase agrupa las pruebas de reservar turnos"""
    fixtures = ['test.json']
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
        """Verifica que pasa si no hay mas turnos y se deben crear sobreturnos.
        Se reservan todos los turnos de un dia, luego se consultan los turnos disponibles
        y debe devolver los turnos con estado SOBRETURNO"""
        afiliado_id = 1
        listaTurnos = range(1000,1100)
        fecha = timezone.now()
        ee = EspecialistaEspecialidad.objects.get(id=1)
        for i in listaTurnos:
            Turno.objects.create(fecha=fecha,
                                 estado=Turno.DISPONIBLE,
                                 sobreturno=False,
                                 consultorio=Consultorio.objects.get(id=1),
                                 ee=ee,
                                 id = i,)
        # Reservamos todos los turnos
        b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        # Consultamos turnos disponibles
        disponibles = b.getTurnosDisponibles(ee.id, fecha)
        self.assertGreater(len(disponibles), 0)
        for turno in disponibles:
            self.assertTrue(turno.sobreturno)
    def testSinSobreturno(self):
        """Verifica que pasa si no hay mas sobreturnos para un dia. Se reservan
        todos los turnos de un dia, luego se crean sobreturnos y tambien se reservan.
        Se consulta una vez mas por los turnos disponibles y debe devolver una lista vacia"""
        afiliado_id = 1
        listaTurnos = range(1000,1100)
        fecha = timezone.now()
        ee = EspecialistaEspecialidad.objects.get(id=1)
        for i in listaTurnos:
            Turno.objects.create(fecha=fecha,
                                 estado=Turno.DISPONIBLE,
                                 sobreturno=False,
                                 consultorio=Consultorio.objects.get(id=1),
                                 ee=ee,
                                 id = i,)
        # Reservamos todos los turnos
        b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        # Consultamos turnos disponibles, debe devolver sobreturnos
        disponibles = b.getTurnosDisponibles(ee.id, fecha)
        # Reservamos los sobreturnos
        listaTurnos=[turno.id for turno in disponibles]
        logger.debug("listaTurnos %s"%listaTurnos)
        b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        # Consultamos los turnos disponibles de nuevo
        disponibles = b.getTurnosDisponibles(ee.id, fecha)
        self.assertEqual(len(disponibles), 0)
    def testPresentismoNotOK(self):
        """Verifica el funcionamiento del algoritmo de presentismo con un afiliado que falta mucho.
        Debe devolver falso, indicando que el afiliado falta mucho a los turnos"""
        cantidad = b.AUSENTES_CANTIDAD
        afiliado_id = 1
        # Creando turnos
        listaTurnos = range(1000,1000 + cantidad + 1)
        for i in listaTurnos:
            Turno.objects.create(fecha=timezone.now(),
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
            Turno.objects.create(fecha=timezone.now(),
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
    def testGetTurnosReservados(self):
        """Verifica que se obtenga la lista de turnos reservados correctamente.
        Debe devolver una lista de diccionarios con los turnos reservados"""
        afiliado_id = 1
        afiliado_falla=2
        listaTurnos = [2,3,4]
        b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        reservados = b.get_turnos_reservados(afiliado_id)
        reservados_falla = b.get_turnos_reservados(afiliado_falla)
        self.assertIsNotNone(reservados)
        self.assertFalse(reservados_falla)
        for reservado in reservados:
            linea = LineaDeReserva.objects.get(id=reservado['id'])
            self.assertEquals(linea.estado, Turno.RESERVADO)
            self.assertEquals(linea.turno.ee.especialista.full_name(), reservado['especialista'])
            self.assertEquals(linea.turno.ee.especialidad.descripcion, reservado['especialidad'])
            self.assertEquals(linea.turno.consultorio.id, int(reservado['consultorio']))
            self.assertEquals(linea.reserva.fecha, reservado['fecha_reserva'])
class ConfirmarReservaTest:
    def testConfirmarReserva(self):
        """Verifica que se confirmen las reservas correctamente"""
        afiliado_id = 1
        ee = EspecialistaEspecialidad.objects.get(id=1)
        turno = Turno.objects.create(fecha=timezone.now(),
                                     ee=ee,
                                     sobreturno=False,
                                     estado=Turno.DISPONIBLE)
        b.reservarTurnos(afiliado_id, '12345678', [turno.id])
        reservados = b.get_turnos_reservados(afiliado_id)
        for reservado in reservados:
            b.confirmar_reserva([reservado['id']])
            linea = LineaDeReserva.objects.get(id=reservado['id'])
            self.assertEquals(linea.estado, Turno.PRESENTE)
            self.assertEquals(linea.turno.estado, Turno.PRESENTE)
    def testConfirmarReservaOtroDia(self):
        """Verifica que pasa si se quiere confirmar una reserva de un turno con una fecha distinta a la fecha actual.
        Deberia fallar con una excepcion ConfirmarTurnoException"""
        afiliado_id = 1
        listaTurnos = [2,3,4]
        b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        reservados = b.get_turnos_reservados(afiliado_id)
        for reservado in reservados:
            with self.assertRaises(ConfirmarReservaException):
                b.confirmar_reserva([reservado['id']])
    def testConfirmarReservaConfirmada(self):
        """Verifica que pasa si se quiere confirmar una reserva ya confirmada.
        Deberia fallar con una excepcion ConfirmarTurnoException"""
        afiliado_id = 1
        ee = EspecialistaEspecialidad.objects.get(id=1)
        turno = Turno.objects.create(fecha=timezone.now(),
                                     ee=ee,
                                     sobreturno=False,
                                     estado=Turno.DISPONIBLE)
        b.reservarTurnos(afiliado_id, '12345678', [turno.id])
        reservados = b.get_turnos_reservados(afiliado_id)
        for reservado in reservados:
            b.confirmar_reserva([reservado['id']])
            with self.assertRaises(ConfirmarReservaException):
                b.confirmar_reserva([reservado['id']])
    def testConfirmarReservaCancelada(self):
        """Verifica que pasa si se quiere confirmar una reserva cancelada.
        Deberia fallar con una excepcion ConfirmarTurnoException"""
        afiliado_id = 1
        ee = EspecialistaEspecialidad.objects.get(id=1)
        turno = Turno.objects.create(fecha=timezone.now(),
                                     ee=ee,
                                     sobreturno=False,
                                     estado=Turno.DISPONIBLE)
        b.reservarTurnos(afiliado_id, '12345678', [turno.id])
        reservados = b.get_turnos_reservados(afiliado_id)
        for reservado in reservados:
            b.cancelar_reserva(reservado['id'])
            with self.assertRaises(ConfirmarReservaException):
                b.confirmar_reserva([reservado['id']])
    def testConfirmarReservaInexistente(self):
        """Verifica que pasa si se quiere confirmar una reserva inexistente.
        Deberia fallar con una excepcion ConfirmarTurnoException"""
        linea_inexistente=4000
        with self.assertRaises(ConfirmarReservaException):
            b.confirmar_reserva([linea_inexistente])
class CancelarReservaTest(TestCase):
    """Esta clase agrupa las pruebas de cancelacion de reservas"""
    fixtures = ['test.json']
    def testCancelarReserva(self):
        """Verifica que se cancelen las reservas correctamente"""
        afiliado_id = 1
        listaTurnos = [2,3,4]
        b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        reservados = b.get_turnos_reservados(afiliado_id)
        linea_reserva_id = reservados[1]["id"]
        b.cancelar_reserva(linea_reserva_id)
        linea = LineaDeReserva.objects.get(id=linea_reserva_id)
        self.assertEquals(linea.estado, Turno.CANCELADO)
        self.assertEquals(linea.turno.estado, Turno.DISPONIBLE)
    def testCancelarReservaCancelada(self):
        """Verifica que sucede cuando se quiere cancelar una reserva ya cancelada.
        Deberia fallar con una excepcion CancelarReservaException"""
        afiliado_id = 1
        listaTurnos = [2,3,4]
        b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        reservados = b.get_turnos_reservados(afiliado_id)
        linea_reserva_id = reservados[1]["id"]
        b.cancelar_reserva(linea_reserva_id)
        with self.assertRaises(CancelarReservaException):
            b.cancelar_reserva(linea_reserva_id)
    def testCancelarReservaInexistente(self):
        """Verifica que sucede cuando se quiere cancelar una reserva inexistente.
        Deberia fallar con una excepcion CancelarReservaException"""
        linea_inexistente=4000
        with self.assertRaises(CancelarReservaException):
            b.cancelar_reserva(linea_inexistente)

class CancelarTurnoTest(TestCase):
    """Esta clase agrupa las pruebas de cancelacion de turnos"""
    fixtures = ['test.json']
    def testCancelarTurnosSinTurnosCreados(self):
        """Prueba cancelar turnos de un dia antes de que se creen. Debe devolver una lista vacia"""
        ee = EspecialistaEspecialidad.objects.get(id=1)
        fecha = timezone.now() + timedelta(days=1)
        cancelados = b.cancelar_turnos(ee.especialista.id, fecha)
        self.assertEquals(len(cancelados),0)
    def testCancelarTurnosSinTurnosReservados(self):
        """Prueba cancelar turnos de un dia sin ningun turno reservado. Debe devolver una lista vacia
        y los turnos de ese dia debe estar con el estado CANCELADO"""
        ee = EspecialistaEspecialidad.objects.get(id=1)
        fecha = timezone.now().date()
        turnos = b.crear_turnos_del_especialista(ee, 1)
        cancelados = b.cancelar_turnos(ee.especialista.id, fecha)
        for turno in turnos:
            t = Turno.objects.get(id=turno.id)
            self.assertEquals(t.estado, Turno.CANCELADO)
        self.assertFalse(cancelados)
        self.assertTrue(b._Bussiness__isCancelado(ee.id,fecha))
    def testCancelarTurnosUnoReservados(self):
        """Prueba cancelar turnos de un dia con un turno reservado. Debe devolver una lista con la reserva
        que relacionada con el turno reservado y los turnos de ese dia debe estar con el 
        estado CANCELADO"""
        ee = EspecialistaEspecialidad.objects.get(id=1)
        fecha = timezone.now().date()
        turnos = b.crear_turnos_del_especialista(ee, 1)
        reserva = b.reservarTurnos(1, '12345678', [turnos[0].id])
        cancelados = b.cancelar_turnos(ee.especialista.id, fecha)
        for turno in turnos:
            t = Turno.objects.get(id=turno.id)
            self.assertEquals(t.estado, Turno.CANCELADO)
        self.assertEquals(reserva.id, cancelados[0].id)
        self.assertTrue(b._Bussiness__isCancelado(ee.id,fecha))
    def testCancelarTurnosTodosReservadosUnaReserva(self):
        """Prueba cancelar turnos de un diacon todos los turnos reservados en una reserva. Debe devolver una lista 
        con una unica reserva y los turnos de ese dia debe estar con el estado CANCELADO"""
        ee = EspecialistaEspecialidad.objects.get(id=1)
        fecha = timezone.now().date()
        turnos = b.crear_turnos_del_especialista(ee, 1)
        reserva = b.reservarTurnos(1, '12345678', [turno.id for turno in turnos])
        cancelados = b.cancelar_turnos(ee.especialista.id, fecha)
        for turno in turnos:
            t = Turno.objects.get(id=turno.id)
            self.assertEquals(t.estado, Turno.CANCELADO)
        for cancelado in cancelados:
            self.assertEquals(reserva.id, cancelado.id)
        # Verifico que se haya cancelado la linea de reserva
        for lr in LineaDeReserva.objects.filter(reserva__id=reserva.id):
            self.assertEqual(lr.estado, Turno.CANCELADO)
        self.assertTrue(b._Bussiness__isCancelado(ee.id,fecha))
    def testCancelarTurnosTodosReservados(self):
        """Prueba cancelar turnos de un di acon todos los turnos reservados en varias reserva. Debe 
        devolver una lista con las reservas que esten relacionados con los turnos reservados y 
        los turnos de ese dia debe estar con el estado CANCELADO"""
        ee = EspecialistaEspecialidad.objects.get(id=1)
        fecha = timezone.now().date()
        turnos = b.crear_turnos_del_especialista(ee, 1)
        reservas = list()
        for turno in turnos:
            reservas.append(b.reservarTurnos(1, '12345678', [turno.id]))
        ids_reservas = [reserva.id for reserva in reservas]
        cancelados = b.cancelar_turnos(ee.especialista.id, fecha)
        for turno in turnos:
            t = Turno.objects.get(id=turno.id)
            self.assertEquals(t.estado, Turno.CANCELADO)
        for cancelado in cancelados:
            self.assertIn(cancelado.id, ids_reservas)
        # Verifico que se haya cancelado la linea de reserva
        for lr in LineaDeReserva.objects.filter(reserva__id__in=ids_reservas):
            self.assertEqual(lr.estado, Turno.CANCELADO)
        self.assertTrue(b._Bussiness__isCancelado(ee.id,fecha))
    def testCancelarTurnosConPresentes(self):
        """Prueba cancelar turnos de un dia con algunos turnos con estado PRESENTE. 
        Debe devolver una lista con las reservas que esten relacionados con los turnos 
        reservados y los turnos reservados de ese dia debe estar con el estado CANCELADO.
        Los turnos con estados presente deben mantener su estado"""
        ee = EspecialistaEspecialidad.objects.get(id=1)
        fecha = timezone.now().date()
        # Creo los turnos
        turnos = b.crear_turnos_del_especialista(ee, 1)
        # Reservo todos los turnos
        reservas = list()
        for turno in turnos:
            reservas.append(b.reservarTurnos(1, '12345678', [turno.id]))
        # Obtengo una linea de reserva y la confirmo
        lr = LineaDeReserva.objects.get(reserva__id=reservas[0].id)
        b.confirmar_reserva([lr.id])
        # Cancelo los turnos
        cancelados = b.cancelar_turnos(ee.especialista.id, fecha)
        ids_cancelados = [cancelado.id for cancelado in cancelados]
        # Verifico que todo sea correcto
        for turno in turnos[1:]:
            t = Turno.objects.get(id=turno.id)
            self.assertEquals(t.estado, Turno.CANCELADO)
        # Verifico que se haya cancelado la linea de reserva
        for lr in LineaDeReserva.objects.filter(reserva__in=reservas):
            self.assertIn(lr.estado, (Turno.CANCELADO,Turno.PRESENTE))
        self.assertNotIn(reservas[0].id, ids_cancelados)
        lr = LineaDeReserva.objects.get(reserva__id=reservas[0].id)
        self.assertEquals(lr.turno.estado, Turno.PRESENTE)
        self.assertTrue(b._Bussiness__isCancelado(ee.id,fecha))
    def testCancelarTurnosConCancelados(self):
        """Prueba cancelar turnos de un dia con todos los turnos con estado CANCELADO. 
        Debe devolver una lista vacia y los turnos no deben cambiar de estado"""
        ee = EspecialistaEspecialidad.objects.get(id=1)
        fecha = timezone.now().date()
        # Creo los turnos
        turnos = b.crear_turnos_del_especialista(ee, 1)
        # Reservo todos los turnos
        reservas = list()
        for turno in turnos:
            reservas.append(b.reservarTurnos(1, '12345678', [turno.id]))
        # Cancelo los turnos dos veces
        b.cancelar_turnos(ee.especialista.id, fecha)
        cancelados = b.cancelar_turnos(ee.especialista.id, fecha)
        # Verifico que todo sea correcto
        for turno in turnos[1:]:
            t = Turno.objects.get(id=turno.id)
            self.assertEquals(t.estado, Turno.CANCELADO)
        self.assertFalse(cancelados)
        self.assertTrue(b._Bussiness__isCancelado(ee.id,fecha))
    def testCancelarTurnosConAusentes(self):
        """Prueba cancelar turnos de un dia con algunos turnos con estado AUSENTE. 
        Debe devolver una lista con las reservas de los turnos con estado RESERVADO 
        y los turnos con estado AUSENTE no deben cambiar de estado"""
        ee = EspecialistaEspecialidad.objects.get(id=1)
        fecha = timezone.now().date()
        # Creo los turnos
        turnos = b.crear_turnos_del_especialista(ee, 1)
        # Reservo todos los turnos
        reservas = list()
        for turno in turnos:
            reservas.append(b.reservarTurnos(1, '12345678', [turno.id]))
        # Obtengo una linea de reserva y la pongo como ausente
        lr = LineaDeReserva.objects.get(reserva__id=reservas[0].id)
        lr.turno.estado = Turno.AUSENTE
        lr.estado = Turno.AUSENTE
        lr.turno.save()
        lr.save()
        # Cancelo los turnos
        cancelados = b.cancelar_turnos(ee.especialista.id, fecha)
        ids_cancelados = [cancelado.id for cancelado in cancelados]
        # Verifico que todo sea correcto
        for turno in turnos[1:]:
            t = Turno.objects.get(id=turno.id)
            self.assertEquals(t.estado, Turno.CANCELADO)
        self.assertNotIn(reservas[0].id, ids_cancelados)
        lr = LineaDeReserva.objects.get(reserva__id=reservas[0].id)
        self.assertEquals(lr.turno.estado, Turno.AUSENTE)
        self.assertTrue(b._Bussiness__isCancelado(ee.id,fecha))
    def testCancelarTurnosDistintoDiaDisponible(self):
        """Prueba cancelar turnos de un dia distinto al dia que atiende el especialista"""
        fecha = timezone.now().date()
        es=Especialidad.objects.create(descripcion="Clinico")
        e=Especialista.objects.create(nombre='n1',apellido='n1',dni=1234)
        ee = EspecialistaEspecialidad.objects.create(especialista=e, especialidad=es)
        Disponibilidad.objects.create(dia=fecha.weekday() + 1,horaDesde="10:00",horaHasta="13:00",ee=ee)
        # Creo los turnos
        b.crear_turnos_del_especialista(ee, 1)
        # Cancelo los turnos
        cancelados = b.cancelar_turnos(ee.especialista.id, fecha)
        self.assertFalse(cancelados)
    def testCancelarTurnosAnteriores(self):
        """Prueba cancelar turnos de un dia anterior a la fecha actual. 
        Debe devolver una excepcion CancelarTurnoException"""
        ee = EspecialistaEspecialidad.objects.get(id=1)
        fecha = timezone.now() + timedelta(days=-1)
        # Creo los turnos
        turnos = b.crear_turnos_del_especialista(ee, 1)
        # Cambio la fecha a los turnos
        for turno in turnos:
            turno.fecha=fecha
            turno.save()
        # Cancelo los turnos
        with self.assertRaises(CancelarTurnoException):
            b.cancelar_turnos(ee.especialista.id, fecha)
        turnos = Turno.objects.filter(ee=ee, fecha = fecha)
        for turno in turnos:
            t = Turno.objects.get(id=turno.id)
            self.assertEquals(t.estado, Turno.DISPONIBLE)
        self.assertFalse(b._Bussiness__isCancelado(ee.id,fecha))
    def testFatiga(self):
        """Prueba cancelar la mayor cantidad de turnos de un especialista"""
        fecha = timezone.now()
        es=Especialidad.objects.create(descripcion="Clinico")
        e=Especialista.objects.create(nombre='n1',apellido='n1',dni=1234)
        ee = EspecialistaEspecialidad.objects.create(especialista=e, especialidad=es)
        Disponibilidad.objects.create(dia=fecha.weekday(),horaDesde="00:00",horaHasta="23:59",ee=ee)
        # Creo los turnos
        turnos = b.crear_turnos_del_especialista(ee, 1)
        # Reservo todos los turnos
        logger.debug('turnos %s'%turnos)
        reservas = list()
        for turno in turnos:
            reservas.append(b.reservarTurnos(1, '12345678', [turno.id]))
        # Cancelo los turnos
        cancelados = b.cancelar_turnos(ee.especialista.id, fecha)
        self.assertEquals(len(reservas), len(cancelados))
        self.assertTrue(b._Bussiness__isCancelado(ee.id,fecha))
class CrearTurnoTest(TestCase):
    """Esta clase agrupa las pruebas de crear turnos"""
    fixtures = ['test.json']
    def testUnDia(self):
        """Crea turnos para un dia. Debe devolver una lista con mas de un turno"""
        #ee = EspecialistaEspecialidad.objects.get(id=1)
        #turnos1 = b.crear_turnos_del_especialista(ee, 1)
        #self.assertGreater(len(turnos), 1)
        from negocio.managers import TurnoManager
        manager = TurnoManager()
        turnos = manager.crear_turnos(timezone.now(), 
                                      timezone.now() + timedelta(days=1))
        self.assertGreater(len(turnos), 1)
        
    def test8Dias(self):
        """Crea una semana de turnos. Debe devolver una lista de turnos creados"""
        DIAS = 8
        ee = EspecialistaEspecialidad.objects.get(id=1)
        turnos = b.crear_turnos_del_especialista(ee, DIAS)
        maximo = 0
        for turno in turnos:
            diff = turno.fecha - timezone.now()
            maximo = diff.days if diff.days > maximo else maximo
            #Verifico que exista el historial
            self.assertTrue(HistorialTurno.objects.filter(turno=turno).exists())
        self.assertEqual(maximo, DIAS-1)
    def test365Dias(self):
        """Crea un año de turnos y verifica que sea correcto. Debe devolver una lista de turnos creados"""
        DIAS = 365
        ee = EspecialistaEspecialidad.objects.get(id=1)
        turnos = b.crear_turnos_del_especialista(ee, DIAS)
        maximo = 0
        for turno in turnos:
            diff = turno.fecha - timezone.now()
            maximo = diff.days if diff.days > maximo else maximo
            #Verifico que exista el historial
            self.assertTrue(HistorialTurno.objects.filter(turno=turno).exists())
        self.assertEqual(maximo, DIAS-1)
    def testDosAnos(self):
        """Crea turnos a dos años. Debe devolver una lista de turnos creados"""
        DIAS = 365 * 2
        ee = EspecialistaEspecialidad.objects.get(id=1)
        turnos = b.crear_turnos_del_especialista(ee, DIAS)
        maximo = 0
        for turno in turnos:
            diff = turno.fecha - timezone.now()
            maximo = diff.days if diff.days > maximo else maximo
            #Verifico que exista el historial
            self.assertTrue(HistorialTurno.objects.filter(turno=turno).exists())
        self.assertEqual(maximo, DIAS-1)
    def testDiasNegativos(self):
        """Prueba que pasa si se pasan dias negativos a crear turnos. Debe devolver una lista vacia"""
        DIAS = -7
        ee = EspecialistaEspecialidad.objects.get(id=1)
        turnos = b.crear_turnos_del_especialista(ee, DIAS)
        self.assertFalse(turnos)
    def testDiasCero(self):
        """Prueba que pasa si se pasan cero dias a crear turnos. Debe devolver una lista vacia"""
        DIAS = 0
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
    def testGetHistorialCreacion(self):
        """Prueba que se obtenga el historial de turnos creados"""
        historial = b.get_historial_creacion_turnos()
        self.assertTrue(historial)
    def testVariosEspecialistas(self):
        """Prueba que pasa si se crean turnos de varios especialistas"""
        es1=Especialidad.objects.create(descripcion="Clinico")
        es2=Especialidad.objects.create(descripcion="Oftamologia")
        e1=Especialista.objects.create(nombre='n1',apellido='n1',dni=1234)
        e2=Especialista.objects.create(nombre='n2',apellido='n2',dni=12345)
        ee1 = EspecialistaEspecialidad.objects.create(especialista=e1, especialidad=es1)
        ee2 = EspecialistaEspecialidad.objects.create(especialista=e2, especialidad=es2)
        Disponibilidad.objects.create(dia='0',horaDesde="10:00",horaHasta="13:00",ee=ee1)
        Disponibilidad.objects.create(dia='1',horaDesde="15:00",horaHasta="20:00",ee=ee2)
        turnos = b.crear_turnos()
        t1 = Turno.objects.filter(ee__especialista=e1)
        t2 = Turno.objects.filter(ee__especialista=e2)
        self.assertGreater(turnos, 0)
        self.assertGreater(len(t1), 0)
        self.assertGreater(len(t2), 0)
    def testDistintaFrecuencia(self):
        """Prueba el algoritmo de creacion de turnos cambiando la frecuencia en minutos de cada turno"""
        FRECUENCIA = 1 # minutos
        es=Especialidad.objects.create(descripcion="Oftamologia")
        e=Especialista.objects.create(nombre='n2',apellido='n2',dni=12345)
        ee = EspecialistaEspecialidad.objects.create(especialista=e, especialidad=es, frecuencia_turnos=FRECUENCIA)
        Disponibilidad.objects.create(dia='0',horaDesde="10:00",horaHasta="13:00",ee=ee)
        creados = b.crear_turnos()
        turnos = Turno.objects.filter(ee__especialista=e).order_by('-fecha')
        self.assertGreater(creados, 0)
        # Verificamos la diferencia en minutos de cada turno
        for i in range(len(turnos) - 1):
            diff = turnos[i].fecha - turnos[i+1].fecha
            minutos = (diff.seconds % 3600) // 60
            self.assertEqual(minutos, FRECUENCIA)
    def testCrearSobreturnos(self):
        """Prueba el proceso de creacion de sobreturnos"""
        FRECUENCIA = 10 # minutos
        es=Especialidad.objects.create(descripcion="Oftamologia")
        e=Especialista.objects.create(nombre='n2',apellido='n2',dni=12345)
        ee = EspecialistaEspecialidad.objects.create(especialista=e, especialidad=es, frecuencia_turnos=FRECUENCIA)
        Disponibilidad.objects.create(dia='0',horaDesde="10:00",horaHasta="11:10",ee=ee)
        fecha = b._Bussiness__proximoDia(0, timezone.now())
        creados = b._Bussiness__crearSobreturnos(ee.id,fecha)
        self.assertGreater(len(creados), 0)
        turnos = Turno.objects.filter(ee__especialista=e, sobreturno=True).order_by('-fecha')
        self.assertTrue(turnos.exists())
        self.assertEqual(turnos.count(), b.MAX_SOBRETURNOS)
        # Verificamos la diferencia en minutos de cada turno
        for i in range(len(turnos) - 1):
            diff = turnos[i].fecha - turnos[i+1].fecha
            minutos = (diff.seconds % 3600) // 60
            self.assertEqual(minutos, FRECUENCIA * 2)
class TestValidadores(TestCase):
    def testLongitud(self):
        """Prueba que el validador funcione cuando una contraseña es menor a la longitud permitida"""
        invalid_password='12345'
        valid_password='123456'
        other_valid_password='1234567'
        validator = PasswordValidator(min_length=6)
        self.assertFalse(validator(valid_password))
        self.assertFalse(validator(other_valid_password))
        with self.assertRaises(ValidationError):
            validator(invalid_password)
    def testCaracterMinuscula(self):
        """Prueba una contraseña con y sin caracteres minusculas"""
        invalid_password='12345ASD'
        valid_password='123456asd'
        validator = PasswordValidator(lower=True)
        self.assertFalse(validator(valid_password))
        with self.assertRaises(ValidationError):
            validator(invalid_password)
    def testCaracterMayuscula(self):
        """Prueba una contraseña con y sin caracter mayuscula"""
        invalid_password='12345asd'
        valid_password='123456ASD'
        validator = PasswordValidator(upper=True)
        self.assertFalse(validator(valid_password))
        with self.assertRaises(ValidationError):
            validator(invalid_password)
    def testCaracterEspecial(self):
        """Prueba una contraseña con y sin caracteres especiales"""
        invalid_password='12345ASD'
        valid_password='123456asd_*'
        validator = PasswordValidator(special_characters=True)
        self.assertFalse(validator(valid_password))
        with self.assertRaises(ValidationError):
            validator(invalid_password)
    def testNumero(self):
        """Prueba una contraseña con y sin numeros"""
        invalid_password='ASDasdf'
        valid_password='123456asd'
        validator = PasswordValidator(number=True)
        self.assertFalse(validator(valid_password))
        with self.assertRaises(ValidationError):
            validator(invalid_password)
    def testCaracterMinusculayNumero(self):
        """Prueba una contraseña con varias politicas juntas. En este caso minuscula y numero"""
        invalid_password='12345ASD'
        valid_password='123456asd'
        validator = PasswordValidator(lower=True,number=True)
        self.assertFalse(validator(valid_password))
        with self.assertRaises(ValidationError):
            validator(invalid_password)
class ConsultaReservaTest(TestCase):
    """Esta clase agrupa las pruebas de consulta de reservas"""
    fixtures = ['test.json']
    def testSinReservas(self):
        '''Consulta las reservas sin que haya ninguna cargada.
        Debe devolver una lista vacia'''
        LineaDeReserva.objects.all().delete()
        reservas = b.consultar_reservas()
        self.assertFalse(reservas)
    def testSinFiltro(self):
        '''Trae todas las reservas cargadas'''
        afiliado_id = 1
        listaTurnos = [2,3,4]
        reserva = b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        lreservas = b.consultar_reservas()
        id_reservas = [linea.reserva.id for linea in lreservas]
        self.assertIn(reserva.id, id_reservas)
    def testEspecialidad(self):
        '''Obtiene las reservas de una especialidad en particular'''
        turno = Turno.objects.get(id=2)
        b.reservarTurnos(1, '12345678', [turno.id])
        lreservas = b.consultar_reservas(especialidad=turno.ee.especialidad)
        id_reservas = [linea.turno.id for linea in lreservas]
        self.assertIn(turno.id, id_reservas)
    def testEspecialista(self):
        '''Obtiene las reservas de un especialista en particular'''
        turno = Turno.objects.get(id=2)
        b.reservarTurnos(1, '12345678', [turno.id])
        lreservas = b.consultar_reservas(especialista=turno.ee.especialista)
        id_turnos = [linea.turno.id for linea in lreservas]
        self.assertIn(turno.id, id_turnos)
    def testAfiliado(self):
        '''Obtiene todas las reservas de un afiliado en particular'''
        afiliado = Afiliado.objects.get(id=1)
        b.reservarTurnos(afiliado.id, '12345678', [2])
        lreservas = b.consultar_reservas(afiliado=afiliado)
        id_afiliados = [linea.reserva.afiliado.id for linea in lreservas]
        self.assertIn(afiliado.id, id_afiliados)
    def testFechaReserva(self):
        '''Obtiene todas las reservas de una fecha en particular'''
        turno = Turno.objects.get(id=2)
        b.reservarTurnos(1, '12345678', [turno.id])
        lreservas = b.consultar_reservas(fecha_reserva=timezone.now())
        id_turnos = [linea.turno.id for linea in lreservas]
        self.assertIn(turno.id, id_turnos)
    def testFechaTurno(self):
        '''Obtiene todas las reservas de una fecha en particular'''
        turno = Turno.objects.get(id=2)
        b.reservarTurnos(1, '12345678', [turno.id])
        lreservas = b.consultar_reservas(fecha_turno=turno.fecha.date())
        id_turnos = [linea.turno.id for linea in lreservas]
        self.assertIn(turno.id, id_turnos)
    def testEstado(self):
        '''Obtiene todas las reservas con un estado particular'''
        turno = Turno.objects.get(id=2)
        b.reservarTurnos(1, '12345678', [turno.id])
        lreservas = b.consultar_reservas(estado=Turno.RESERVADO)
        id_turnos = [linea.turno.id for linea in lreservas]
        self.assertIn(turno.id, id_turnos)
        b.cancelar_reserva(lreservas, '', None)
        lreservas = b.consultar_reservas(estado=Turno.CANCELADO)
        id_turnos = [linea.turno.id for linea in lreservas]
        self.assertIn(turno.id, id_turnos)
    def testMuchasReservasSinFiltro(self):
        '''Fatiga: Se reservan muchos turnos y se obtienen todas las reservas.
        Debe devolver el resultado en un tiempo razonable'''
        listaTurnos = range(1000,1100)
        for i in listaTurnos:
            Turno.objects.create(fecha=timezone.now(),
                                 estado=Turno.DISPONIBLE,
                                 sobreturno=False,
                                 consultorio=Consultorio.objects.get(id=1),
                                 ee=EspecialistaEspecialidad.objects.get(id=1),
                                 id = i,)
        b.reservarTurnos(1, '12345678', listaTurnos)
        lreservas = b.consultar_reservas()
        self.assertTrue(lreservas)
    def testSinCoincidencia(self):
        '''Se filtran de forma tal que ninguna reserva coincida'''
        especialidad = Especialidad.objects.create(descripcion='dummy')
        afiliado = Afiliado.objects.create(numero='1',dni=1,nombre='1',apellido='1')
        especialista = Especialista.objects.create(nombre='a',apellido='a',dni=1)
        self.assertFalse(b.consultar_reservas(especialidad=especialidad))
        self.assertFalse(b.consultar_reservas(afiliado=afiliado))
        self.assertFalse(b.consultar_reservas(especialista=especialista))
    def testVariosFiltrosDisjuntos(self):
        '''Se filtra de manera que los filtros generen conjuntos disjuntos 
        (ej un especialista y una especialidad que no corresponde)'''
        especialidad = Especialidad.objects.create(descripcion='dummy')
        afiliado = Afiliado.objects.create(numero='1',dni=1,nombre='1',apellido='1')
        especialista = Especialista.objects.create(nombre='a',apellido='a',dni=1)
        self.assertFalse(b.consultar_reservas(especialidad=especialidad,especialista=especialista))
        self.assertFalse(b.consultar_reservas(afiliado=afiliado,especialista=especialista))
        self.assertFalse(b.consultar_reservas(afiliado=afiliado,
                                              especialista=especialista,
                                              especialidad=especialidad))        
    def testVariosFiltrosUnion(self):
        '''Se filtran por varios filtros simultaneamente'''
        turno = Turno.objects.get(id=2)
        afiliado = Afiliado.objects.get(id=1)
        reserva = b.reservarTurnos(afiliado.id, '12345678', [turno.id])
        lreservas = b.consultar_reservas(especialista=turno.ee.especialista,
                                         especialidad=turno.ee.especialidad,
                                         afiliado=afiliado,
                                         fecha_reserva=timezone.now())
        id_turnos = [linea.reserva.id for linea in lreservas]
        self.assertIn(reserva.id, id_turnos)
        self.assertEqual(len(lreservas), 1)