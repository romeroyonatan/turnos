from dateutil.relativedelta import relativedelta
from datetime import timedelta, datetime
from django.test import TestCase
from turnos.models import *
from turnos.bussiness import *
from django.utils import timezone
from django.conf import settings

import logging
logger = logging.getLogger(__name__)
b = Bussiness()

class ReservarTurnoTest(TestCase):
    fixtures = ['turnos.json']
        
    def setUp(self):
        TestCase.setUp(self)
    
    def testGetDiasTurnos(self):
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
        afiliado_id = 1
        listaTurnos = [2, 4000]
        with self.assertRaises(TurnoNotExistsException):
            b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        turno = Turno.objects.get(id=2)
        self.assertEqual(turno.estado, Turno.DISPONIBLE)
        
    def testAfiliadoInexistente(self):
        afiliado_id = 4000
        listaTurnos = [2,3,4]
        with self.assertRaises(AfiliadoNotExistsException):
            b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        last = LineaDeReserva.objects.latest('id')
        self.assertNotIn(last.turno, listaTurnos)

    def testTurnoVacio(self):
        afiliado_id = 1
        listaTurnos = []
        reserva = b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        self.assertIsNone(reserva)

    def testSinTelefono(self):
        afiliado_id = 1
        listaTurnos = [1]
        with self.assertRaises(Exception):
            b.reservarTurnos(afiliado_id, None, listaTurnos)
        
    def testTurnoReservado(self):
        afiliado_id = 1
        listaTurnos = [2, 3]
        b.reservarTurnos(afiliado_id, '41234345', [3])
        with self.assertRaises(TurnoReservadoException):
            b.reservarTurnos(afiliado_id, '41234345', listaTurnos)
        turno = Turno.objects.get(id=2)
        self.assertEqual(turno.estado, Turno.DISPONIBLE)
    
    def testPresentismo(self):
        afiliado_id = 1
        p = b.presentismoOK(afiliado_id)
        self.assertTrue(p)
    
    def testCrearSobreturno(self):
        #TODO: Hacer test crear sobreturno
        #self.assertTrue(False)
        pass
    def testSinSobreturno(self):
        #TODO: Hacer test sin sobreturno
        #self.assertTrue(False)
        pass
    
    def testPresentismoNotOK(self):
        s = getattr(settings, 'TURNOS', {})
        cantidad = s.get('ausente_cantidad', 6)
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
        logger.debug("testPresentismoExpirado")
        s = getattr(settings, 'TURNOS', {})
        cantidad = s.get('ausente_cantidad', 6)
        meses = s.get('ausente_meses', 6)
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
    fixtures = ['turnos.json']
    def testUnDia(self):
        ee = EspecialistaEspecialidad.objects.get(id=1)
        Disponibilidad.objects.create(dia="%s" % datetime.datetime.now().weekday(),
                                          horaDesde="12:00",
                                          horaHasta="13:00",
                                          ee=ee)
        turnos = b.crearTurnos(ee, 1)
        self.assertGreater(len(turnos), 1)
    def test8Dias(self):
        DIAS = 8
        ee = EspecialistaEspecialidad.objects.get(id=1)
        Disponibilidad.objects.create(dia="%s" % datetime.datetime.now().weekday(),
                                          horaDesde="12:00",
                                          horaHasta="13:00",
                                          ee=ee)
        turnos = b.crearTurnos(ee, DIAS)
        exito = False
        for turno in turnos:
            diff = turno.fecha - (datetime.datetime.now() + datetime.timedelta(days=DIAS - 1))
            exito = exito or diff.days == 0
        self.assertTrue(exito)
    def test365Dias(self):
        DIAS = 365
        ee = EspecialistaEspecialidad.objects.get(id=1)
        Disponibilidad.objects.create(dia="%s" % datetime.datetime.now().weekday(),
                                          horaDesde="12:00",
                                          horaHasta="13:00",
                                          ee=ee)
        turnos = b.crearTurnos(ee, DIAS)
        exito = False
        for turno in turnos:
            diff = turno.fecha - (datetime.datetime.now() + datetime.timedelta(days=DIAS - 1))
            exito = exito or diff.days == 0
        self.assertTrue(exito)
    def testDosAnos(self):
        DIAS = 365 * 2
        ee = EspecialistaEspecialidad.objects.get(id=1)
        Disponibilidad.objects.create(dia="%s" % datetime.datetime.now().weekday(),
                                          horaDesde="12:00",
                                          horaHasta="13:00",
                                          ee=ee)
        turnos = b.crearTurnos(ee, DIAS)
        self.assertTrue(turnos)
    def testDiasNegativos(self):
        DIAS = -7
        ee = EspecialistaEspecialidad.objects.get(id=1)
        Disponibilidad.objects.create(dia="%s" % datetime.datetime.now().weekday(),
                                          horaDesde="12:00",
                                          horaHasta="13:00",
                                          ee=ee)
        turnos = b.crearTurnos(ee, DIAS)
        self.assertFalse(turnos)
    def testSinDias(self):
        ee = EspecialistaEspecialidad.objects.get(id=1)
        Disponibilidad.objects.create(dia="%s" % datetime.datetime.now().weekday(),
                                          horaDesde="12:00",
                                          horaHasta="13:00",
                                          ee=ee)
        turnos = b.crearTurnos(ee)
        self.assertTrue(turnos)
#     def testTurnosExistentes(self):
#         self.assertTrue(False)
#     def testAlgunosExistentes(self):
#         self.assertTrue(False)
    def testProximoDia(self):
        base = datetime.datetime(2014,01,01) # miercoles
        target = datetime.datetime(2014,01,04) # sabado
        dia = 5 # sabado
        fecha = b._Bussiness__proximoDia(dia, base)
        self.assertEquals(target, fecha)
    def testSinDisponibilidad(self):
        es=Especialidad.objects.get(id=1)
        e=Especialista.objects.create(nombre='n',apellido='n',dni=1234)
        ee = EspecialistaEspecialidad.objects.create(especialista=e, especialidad=es)
        turnos = b.crearTurnos(ee)
        self.assertFalse(turnos)
