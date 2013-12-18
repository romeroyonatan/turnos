from django.test import TestCase
from turnos.models import *
from turnos.bussiness import *
from django.utils import timezone

class ReservarTurnoTest(TestCase):
    fixtures = ['turnos.json']
    b = Bussiness()
        
    def setUp(self):
        TestCase.setUp(self)
    
    def testGetDiasTurnos(self):
        test = self.b.getDiaTurnos(1)
        self.assertGreater(len(test), 1)
    
    def testReservarTurno(self):
        afiliado_id = 1
        listaTurnos = [20,21,22,23]
        reserva = self.b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
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
        listaTurnos = [20, 4000]
        with self.assertRaises(TurnoNotExistsException):
            self.b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        turno = Turno.objects.get(id=20)
        self.assertEqual(turno.estado, Turno.DISPONIBLE)
        
    def testAfiliadoInexistente(self):
        afiliado_id = 4000
        listaTurnos = [20,21,22,23]
        with self.assertRaises(AfiliadoNotExistsException):
            self.b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        last = LineaDeReserva.objects.latest('id')
        self.assertNotIn(last.turno, listaTurnos)

    def testTurnoVacio(self):
        afiliado_id = 1
        listaTurnos = []
        reserva = self.b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        self.assertIsNone(reserva)
        
    def testTurnoReservado(self):
        afiliado_id = 1
        listaTurnos = [20, 3]
        with self.assertRaises(TurnoReservadoException):
            self.b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        turno = Turno.objects.get(id=20)
        self.assertEqual(turno.estado, Turno.DISPONIBLE)
        
    def testFatiga(self):
        afiliado_id = 1
        listaTurnos = range(1000,2000)
        for i in listaTurnos:
            Turno.objects.create(fecha=timezone.now(),
                                 estado=Turno.DISPONIBLE,
                                 sobreturno=False,
                                 consultorio=Consultorio.objects.get(id=1),
                                 ee=EspecialistaEspecialidad.objects.get(id=1),
                                 id = i,
                                 )
        reserva = self.b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
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
