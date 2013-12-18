from django.test import TestCase
from turnos.models import *
from turnos.bussiness import Bussiness, TurnoNotExistsException

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
            historial = HistorialTurno.objects.get(turno=turno)
            self.assertEqual(turno.estado, Turno.RESERVADO)
            self.assertIsNotNone(historial)
            self.assertEqual(historial.estadoNuevo, turno.estado)
        for lr in lineas:
            self.assertEqual(lr.reserva.id, reserva.id)
            self.assertIn(lr.turno.id, listaTurnos)
            self.assertEqual(lr.estado, Turno.RESERVADO)
    
    def testReservarTurnoInexistente(self):
        afiliado_id = 1
        listaTurnos = [4000]
#         self.assertRaises(TurnoNotExistsException, Bussiness.reservarTurnos, (self.b, afiliado_id, '12345678', listaTurnos))
        with self.assertRaises(TurnoNotExistsException):
            self.b.reservarTurnos(afiliado_id, '12345678', listaTurnos)

    def testReservarTurnoVacio(self):
        afiliado_id = 1
        listaTurnos = []
        reserva = self.b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        self.assertIsNone(reserva)

        