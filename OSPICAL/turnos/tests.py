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
            #Verifico que exista el historial
            self.assertTrue(HistorialTurno.objects.filter(turno=turno).exists())
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
            #Verifico que exista el historial
            self.assertTrue(HistorialTurno.objects.filter(turno=turno).exists())
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
            #Verifico que exista el historial
            self.assertTrue(HistorialTurno.objects.filter(turno=turno).exists())
        self.assertTrue(exito)
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
        logger.debug("t1 %s"%t1)
        logger.debug("t2 %s"%t2)
        self.assertGreater(turnos, 0)
        self.assertGreater(len(t1), 0)
        self.assertGreater(len(t2), 0)
        

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