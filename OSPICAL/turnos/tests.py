from django.test import TestCase
from turnos.models import *
from turnos.bussiness import Bussiness

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class ReservarTurnoTest(TestCase):
    fixtures = ['turnos.json']
    
    def setUp(self):
        TestCase.setUp(self)
        self.b = Bussiness()
    
    def testGetDiasTurnos(self):
        test = self.b.getDiaTurnos(1)
        self.assertGreater(len(test), 1)
    
    def testReservarTurno(self):
        self.b.reservarTurnos(1, '12345678', [20])
        turno = Turno.objects.get(id=20)
        self.assertEqual(turno.estado, Turno.RESERVADO)
    
    def testTransaccion(self):
        turno = Turno.objects.get(id=20)
        self.assertEqual(turno.estado, Turno.DISPONIBLE)
        