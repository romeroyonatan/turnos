# coding=utf-8


from datetime import timedelta
import logging

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from bussiness import Bussiness
from models import Turno, Consultorio, EspecialistaEspecialidad, LineaDeReserva, \
    Especialidad, Especialista, Disponibilidad, Afiliado, Reserva
from negocio.commands import OrdenCrearTurno, OrdenCrearTurnos, OrdenReservar
from negocio.excepciones import TurnoNotExistsException, \
    AfiliadoNotExistsException, TurnoReservadoException, ConfirmarReservaException, \
    CancelarReservaException, CancelarTurnoException
from negocio.managers import TurnoManager, ReservaManager
from negocio.service import ReservaTurnosService
from turnos.validators import PasswordValidator


logger = logging.getLogger(__name__)
b = Bussiness()

#===============================================================================
# ReservasTestSuite
#===============================================================================
class ReservasTestSuite(TestCase):
    """Esta clase agrupa las pruebas de reservar turnos"""
    fixtures = ['test.json']
    manager = ReservaManager()
    def setUp(self):
        TestCase.setUp(self)
    
    #===========================================================================
    # test_reservar_unico_turno
    #===========================================================================
    def test_reservar_unico_turno(self):
        """
        Verifica que se reserve un turno de forma correcta.
        """
        # obtengo el afiliado
        afiliado = Afiliado.objects.all().first()
        # creo una lista de turnos con un solo turno (estado=disponible)
        lista_turnos = Turno.objects.filter(estado=Turno.DISPONIBLE).first(),
        # creo la reserva con un numero de telefono cualquiera
        reserva = self.manager.crear_reserva(afiliado, '12345678', lista_turnos)
        # verifico que el objeto reserva se haya creado correctamente
        self.assertIsNotNone(reserva)
        # obtengo las lineas de reserva (una por cada turno reservado)
        lineas = LineaDeReserva.objects.filter(reserva=reserva)
        # verifico que el afiliado coincida en la reserva
        self.assertEqual(reserva.afiliado.id, afiliado.id)
        # verifico que la cantidad de lineas de reserva coincida con la
        # cantidad de turnos a reservar
        self.assertEqual(lineas.count(), len(lista_turnos))
        for t in lista_turnos:
            turno = Turno.objects.get(id=t.id)
            # verifico que el estado de los turnos sea reservado para que no
            # puedan ser reservados nuevamente
            self.assertEqual(turno.estado, Turno.RESERVADO)
        for lr in lineas:
            # verifico que los turnos reservados coincidan con los que queria
            # reservar
            self.assertIn(lr.turno, lista_turnos)
            # verifico que las lineas tengan el estado de reservado
            self.assertEqual(lr.estado, Turno.RESERVADO)
    
    #===========================================================================
    # test_reservar_turnos
    #===========================================================================
    def test_reservar_turnos(self):
        """
        Verifica que se reserve una lista de turnos de forma correcta.
        """
        # obtengo el afiliado
        afiliado = Afiliado.objects.all().first()
        # creo una lista de turnos con todos los turnos disponibles
        lista_turnos = Turno.objects.filter(estado=Turno.DISPONIBLE)
        # creo la reserva con un numero de telefono cualquiera
        reserva = self.manager.crear_reserva(afiliado, '12345678', lista_turnos)
        # verifico que el objeto reserva se haya creado correctamente
        self.assertIsNotNone(reserva)
        # obtengo las lineas de reserva (una por cada turno reservado)
        lineas = LineaDeReserva.objects.filter(reserva=reserva)
        # verifico que el afiliado coincida en la reserva
        self.assertEqual(reserva.afiliado.id, afiliado.id)
        # verifico que la cantidad de lineas de reserva coincida con la
        # cantidad de turnos a reservar
        self.assertEqual(lineas.count(), len(lista_turnos))
        for t in lista_turnos:
            turno = Turno.objects.get(id=t.id)
            # verifico que el estado de los turnos sea reservado para que no
            # puedan ser reservados nuevamente
            self.assertEqual(turno.estado, Turno.RESERVADO)
        for lr in lineas:
            # verifico que los turnos reservados coincidan con los que queria
            # reservar
            self.assertIn(lr.turno, lista_turnos)
            # verifico que las lineas tengan el estado de reservado
            self.assertEqual(lr.estado, Turno.RESERVADO)
    
    #===========================================================================
    # test_turno_inexistente
    #===========================================================================
    def test_turno_inexistente(self):
        """
        Verifica que pasa si se quiere reservar un turno que no existe.
        Deberia lanzar una excepcion
        """
        # obtengo el afiliado
        afiliado = Afiliado.objects.all().first()
        # creo una lista de turnos con todos los turnos disponibles
        lista_turnos = list(Turno.objects.filter(estado=Turno.DISPONIBLE))
        # agrego a la lista de turnos un turno inexistente
        lista_turnos.append(Turno(id=-2000, estado=Turno.DISPONIBLE))
        # espero que lanze la excepcion de turno inexistente
        with self.assertRaises(TurnoNotExistsException):
        # creo la reserva
            self.manager.crear_reserva(afiliado, '12345678', lista_turnos)
        # verifico que los turnos sigan en estado disponible (la accion de
        # reservar debe ser transaccional)
        for turno in lista_turnos:
            self.assertEqual(turno.estado, Turno.DISPONIBLE)
        
    #===========================================================================
    # test_afiliado_inexistente
    #===========================================================================
    def test_afiliado_inexistente(self):
        """
        Verifica que pasa si el afiliado no existe. 
        Debe lanzar una excepcion.
        """
        # creo un afiliado inexistente
        afiliado = Afiliado(id=-2000)
        # creo una lista de turnos con todos los turnos disponibles
        lista_turnos = Turno.objects.filter(estado=Turno.DISPONIBLE)
        # espero que lanze la excepcion de afiliado inexistente
        with self.assertRaises(AfiliadoNotExistsException):
        # creo la reserva
            self.manager.crear_reserva(afiliado, '12345678', lista_turnos)
        # verifico que los turnos sigan en estado disponible (la accion de
        # reservar debe ser transaccional)
        for turno in lista_turnos:
            self.assertEqual(turno.estado, Turno.DISPONIBLE)
    
    #===========================================================================
    # test_sin_afiliado
    #===========================================================================
    def test_sin_afiliado(self):
        """
        Verifica que pasa si el afiliado no existe. 
        Debe lanzar una excepcion.
        """
        # creo una lista de turnos con todos los turnos disponibles
        lista_turnos = Turno.objects.filter(estado=Turno.DISPONIBLE)
        # espero que lanze la excepcion
        with self.assertRaises(ValueError):
            self.manager.crear_reserva(None, '12345678', lista_turnos)
        # verifico que los turnos sigan en estado disponible (la accion de
        # reservar debe ser transaccional)
        for turno in lista_turnos:
            self.assertEqual(turno.estado, Turno.DISPONIBLE)
    
    #===========================================================================
    # test_lista_turnos_vacia
    #===========================================================================
    def test_lista_turnos_vacia(self):
        """
        Verifica que pasa si se quiere reservar turnos con una lista de turnos 
        vacia.
        Debe lanzar una excepcion ValueError
        """
        # obtengo el afiliado
        afiliado = Afiliado.objects.all().first()
        # espero la excepcion por enviar un objeto vacio
        with self.assertRaises(ValueError):
            # creo la reserva
            self.manager.crear_reserva(afiliado, '12345678', [])
        # espero la excepcion por enviar un objeto nulo
        with self.assertRaises(ValueError):
            # creo la reserva
            self.manager.crear_reserva(afiliado, '12345678', None)
        
    #===========================================================================
    # test_sin_telefono
    #===========================================================================
    def test_sin_telefono(self):
        """
        Verifica que pasa si se quiere reservar un turno sin telefono de 
        contacto.
        Debe lanzar un error ValueError
        """
        # obtengo el afiliado
        afiliado = Afiliado.objects.all().first()
        # creo una lista de turnos con todos los turnos disponibles
        lista_turnos = Turno.objects.filter(estado=Turno.DISPONIBLE)
        # espero la excepcion por enviar un objeto nulo
        with self.assertRaises(ValueError):
            self.manager.crear_reserva(afiliado, None, lista_turnos)
        # espero la excepcion por enviar una cadena vacia
        with self.assertRaises(ValueError):
            self.manager.crear_reserva(afiliado, '', lista_turnos)
            
    #===========================================================================
    # test_turno_reservado
    #===========================================================================
    def test_turno_reservado(self):
        """
        Verifica que pasa si se quiere reservar un turno que esta reservado.
        """
        # obtengo el afiliado
        afiliado = Afiliado.objects.all().first()
        # creo una lista de turnos con un solo turno a reservar
        lista_turnos = [Turno.objects.filter(estado=Turno.DISPONIBLE).first()]
        # creo la reserva
        self.manager.crear_reserva(afiliado, '12345678', lista_turnos)
        # agrego a la lista de turnos, mas turnos sin reservar
        lista_turnos = (list(Turno.objects.filter(estado=Turno.DISPONIBLE)) + 
                        lista_turnos) 
        # espero la excepcion de turno reservado
        with self.assertRaises(TurnoReservadoException):
            self.manager.crear_reserva(afiliado, '12345678', lista_turnos)
        # verifico que los turnos sigan en estado disponible (la accion de
        # reservar debe ser transaccional)
        for turno in lista_turnos[:-1]:
            self.assertEqual(turno.estado, Turno.DISPONIBLE)

    #===========================================================================
    # test_fatiga
    #===========================================================================
    def test_fatiga(self):
        """
        Reserva una alta cantidad de turnos para verificar como se comporta el 
        algoritmo de reserva.
        Debe reservar los turnos en un tiempo razonable a la cantidad de turnos 
        a reservar.
        """
        # defino la cantidad de turnos a reservar
        CANTIDAD = 100
        # obtengo el afiliado
        afiliado = Afiliado.objects.all().first()
        # defino la lista de turnos
        lista_turnos = []
        # creo turnos y los agrego a la lista
        for i in range(CANTIDAD):
            turno_manager = TurnoManager()
            turno = turno_manager.crear_turno(fecha=timezone.now(),
                                              ee=(EspecialistaEspecialidad
                                                    .objects.all().first()))
            lista_turnos.append(turno)
            i  # para que no aparezca warning de variable no usada
        # creo la reserva
        self.manager.crear_reserva(afiliado, '12345678', lista_turnos)
            
    #===========================================================================
    # test_get_turnos_reservados
    #===========================================================================
    def test_get_turnos_reservados(self):
        """
        Verifica que se obtenga la lista de turnos reservados correctamente.
        Debe devolver una lista de diccionarios con los turnos reservados.
        """
        # creo una lista de afiliados con reserva
        afiliados_con_reserva = (Afiliado.objects.filter(id__in=
                      Reserva.objects.all().values_list('afiliado', flat=True)))
        # verifico que la lista no este vacia
        self.assertIsNotNone(afiliados_con_reserva)
        # obtengo los turnos reservados de un afiliado con reservas
        reservados = (self.manager.
                      get_turnos_reservados(afiliados_con_reserva.first()))
        # verifico que la lista de turnos reservados no este vacia
        self.assertIsNotNone(reservados)
        # recorro las tuplas devuelta para ver si los datos que contienen
        # son correctos
        for reservado in reservados:
            # obtengo la linea de reserva
            linea = LineaDeReserva.objects.get(id=reservado['id'])
            # verifico que la linea de reserva tenga el estado de reservada
            self.assertEquals(linea.estado, Turno.RESERVADO)
            # verifico que el especialista sea correcto
            self.assertEquals(linea.turno.ee.especialista.full_name(),
                              reservado['especialista'])
            # verifico que la especialidad sea correcta
            self.assertEquals(linea.turno.ee.especialidad.descripcion,
                              reservado['especialidad'])
            # verifico que el consultorio sea correcto
            self.assertEquals(linea.turno.consultorio.id,
                              int(reservado['consultorio']))
            # verifico que la fecha de reserva sea correcta
            self.assertEquals(linea.reserva.fecha,
                              reservado['fecha_reserva'])
            # verifico que la fecha del turno sea correcta
            self.assertEquals(linea.turno.fecha,
                              reservado['fecha_turno'])
   
    #===========================================================================
    # test_get_turnos_reservados_sin_reservas
    #===========================================================================
    def test_get_turnos_reservados_sin_reservas(self):
        """
        Verifica que pasa si se quiere obtener una lista de reservas de un 
        afiliado que no realizo nunca una reserva.
        Debe devolver una lista vacia
        """
        # creo una lista de afiliados sin reserva
        afiliados_sin_reserva = Afiliado.objects.exclude(id__in=
                      Reserva.objects.all().values_list('afiliado', flat=True))
        # verifico que las listas reservadas no esten vacias
        self.assertIsNotNone(afiliados_sin_reserva)
        # recorro lista de afiliados sin reserva
        for afiliado in afiliados_sin_reserva:
            # obtengo los turnos reservados del afiliado sin reservas
            reservados_vacia = self.manager.get_turnos_reservados(afiliado)
            # verifico que la lista de reservas este vacia para un afiliado sin
            # reservas
            self.assertFalse(reservados_vacia)
            
#------------------------------------------------------------------------------ 
    #===========================================================================
    # test_presentismo
    # TODO: test_presentismo - Pasarlo a AfiliadoManager
    #===========================================================================
    def test_presentismo(self):
        """
        Verifica el correcto funcionamiento del algoritmo de presentismo, si el 
        afiliado esta en regla.
        """
        afiliado_id = 1
        p = b.presentismoOK(afiliado_id)
        self.assertTrue(p)
    
    #===========================================================================
    # test_presentismo_no_ok
    # TODO: test_presentismo_no_ok - Pasarlo a AfiliadoManager
    #===========================================================================
    def test_presentismo_no_ok(self):
        """
        Verifica el funcionamiento del algoritmo de presentismo con un afiliado 
        que falta mucho. Debe devolver falso, indicando que el afiliado falta 
        mucho a los turnos.
        """
        cantidad = b.AUSENTES_CANTIDAD
        afiliado_id = 1
        # Creando turnos
        listaTurnos = range(1000, 1000 + cantidad + 1)
        for i in listaTurnos:
            Turno.objects.create(fecha=timezone.now(),
                                 estado=Turno.DISPONIBLE,
                                 sobreturno=False,
                                 consultorio=Consultorio.objects.get(id=1),
                                 ee=EspecialistaEspecialidad.objects.get(id=1),
                                 id=i,)
        reserva = b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        # Reservando turnos
        lineas = LineaDeReserva.objects.filter(reserva=reserva)
        # Marcando turnos como ausente
        for lr in lineas:
            lr.estado = Turno.AUSENTE
            lr.save()
        # Verificando presentismo
        p = b.presentismoOK(afiliado_id)
        self.assertFalse(p)
        
    #===========================================================================
    # test_presentismo_expirado
    # TODO: test_presentismo_expirado - Pasarlo a AfiliadoManager
    #===========================================================================
    def test_presentismo_expirado(self):
        """
        Verifica el funcionamiento del algoritmo de presentismo con faltas 
        anteriores a las que el sistema debe tener en cuenta. Debe devolver 
        verdadero, dado que el sistema no debe tener en cuenta faltas 
        anteriores.
        """
        cantidad = b.AUSENTES_CANTIDAD
        meses = b.AUSENTES_MESES
        afiliado_id = 1
        # Creando turnos
        listaTurnos = range(1000, 1000 + cantidad + 1)
        for i in listaTurnos:
            Turno.objects.create(fecha=timezone.now(),
                                 estado=Turno.DISPONIBLE,
                                 sobreturno=False,
                                 consultorio=Consultorio.objects.get(id=1),
                                 ee=EspecialistaEspecialidad.objects.get(id=1),
                                 id=i,)
        reserva = b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        reserva.fecha = timezone.now() + relativedelta(months=-meses, days=-1)
        reserva.save()
        # Reservando turnos
        lineas = LineaDeReserva.objects.filter(reserva=reserva)
        # Marcando turnos como ausente
        for lr in lineas:
            lr.estado = Turno.AUSENTE
            lr.save()
        # Verificando presentismo
        p = b.presentismoOK(afiliado_id)
        self.assertTrue(p)

        
    #===========================================================================
    # test_crear_sobreturno
    # TODO: test_crear_sobreturno - Pasarlo a TurnoManager
    #===========================================================================
    def test_crear_sobreturno(self):
        """
        Verifica que pasa si no hay mas turnos y se deben crear sobreturnos.
        Se reservan todos los turnos de un dia, luego se consultan los turnos 
        disponibles y debe devolver los turnos con estado SOBRETURNO.
        """
        afiliado_id = 1
        listaTurnos = range(1000, 1100)
        fecha = timezone.now()
        ee = EspecialistaEspecialidad.objects.get(id=1)
        for i in listaTurnos:
            Turno.objects.create(fecha=fecha,
                                 estado=Turno.DISPONIBLE,
                                 sobreturno=False,
                                 consultorio=Consultorio.objects.get(id=1),
                                 ee=ee,
                                 id=i,)
        # Reservamos todos los turnos
        b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        # Consultamos turnos disponibles
        disponibles = b.getTurnosDisponibles(ee.id, fecha)
        self.assertGreater(len(disponibles), 0)
        for turno in disponibles:
            self.assertTrue(turno.sobreturno)
            
    #===========================================================================
    # test_sin_sobreturno
    # TODO: test_sin_sobreturno - Pasarlo a TurnoManager
    #===========================================================================
    def test_sin_sobreturno(self):
        """
        Verifica que pasa si no hay mas sobreturnos para un dia. Se reservan
        todos los turnos de un dia, luego se crean sobreturnos y tambien se 
        reservan. Se consulta una vez mas por los turnos disponibles y debe 
        devolver una lista vacia.
        """
        afiliado_id = 1
        listaTurnos = range(1000, 1100)
        fecha = timezone.now()
        ee = EspecialistaEspecialidad.objects.get(id=1)
        for i in listaTurnos:
            Turno.objects.create(fecha=fecha,
                                 estado=Turno.DISPONIBLE,
                                 sobreturno=False,
                                 consultorio=Consultorio.objects.get(id=1),
                                 ee=ee,
                                 id=i,)
        # Reservamos todos los turnos
        b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        # Consultamos turnos disponibles, debe devolver sobreturnos
        disponibles = b.getTurnosDisponibles(ee.id, fecha)
        # Reservamos los sobreturnos
        listaTurnos = [turno.id for turno in disponibles]
        logger.debug("listaTurnos %s" % listaTurnos)
        b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        # Consultamos los turnos disponibles de nuevo
        disponibles = b.getTurnosDisponibles(ee.id, fecha)
        self.assertEqual(len(disponibles), 0)
    
        
    #===========================================================================
    # testGetDiasTurnos
    # TODO: pasarlo a TurnoManager
    #===========================================================================
    def testGetDiasTurnos(self):
        """
        Verifica el funcionamiento del algoritmo para la obtencion de turnos 
        disponibles.
        Debe obtener una lista con todos los turnos disponibles.
        """
        # Creando turno
        Turno.objects.create(fecha=timezone.now() + timedelta(days=1),
                             estado=Turno.DISPONIBLE,
                             sobreturno=False,
                             consultorio=Consultorio.objects.get(id=1),
                             ee=EspecialistaEspecialidad.objects.get(id=1),
                             )
        test = b.getDiaTurnos(1)
        self.assertGreaterEqual(len(test), 1)
        
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
        listaTurnos = [2, 3, 4]
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
        linea_inexistente = 4000
        with self.assertRaises(ConfirmarReservaException):
            b.confirmar_reserva([linea_inexistente])
class CancelarReservaTest(TestCase):
    """Esta clase agrupa las pruebas de cancelacion de reservas"""
    fixtures = ['test.json']
    def testCancelarReserva(self):
        """Verifica que se cancelen las reservas correctamente"""
        afiliado_id = 1
        listaTurnos = [2, 3, 4]
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
        listaTurnos = [2, 3, 4]
        b.reservarTurnos(afiliado_id, '12345678', listaTurnos)
        reservados = b.get_turnos_reservados(afiliado_id)
        linea_reserva_id = reservados[1]["id"]
        b.cancelar_reserva(linea_reserva_id)
        with self.assertRaises(CancelarReservaException):
            b.cancelar_reserva(linea_reserva_id)
    def testCancelarReservaInexistente(self):
        """Verifica que sucede cuando se quiere cancelar una reserva inexistente.
        Deberia fallar con una excepcion CancelarReservaException"""
        linea_inexistente = 4000
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
        self.assertEquals(len(cancelados), 0)
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
        self.assertTrue(b._Bussiness__isCancelado(ee.id, fecha))
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
        self.assertTrue(b._Bussiness__isCancelado(ee.id, fecha))
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
        self.assertTrue(b._Bussiness__isCancelado(ee.id, fecha))
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
        self.assertTrue(b._Bussiness__isCancelado(ee.id, fecha))
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
            self.assertIn(lr.estado, (Turno.CANCELADO, Turno.PRESENTE))
        self.assertNotIn(reservas[0].id, ids_cancelados)
        lr = LineaDeReserva.objects.get(reserva__id=reservas[0].id)
        self.assertEquals(lr.turno.estado, Turno.PRESENTE)
        self.assertTrue(b._Bussiness__isCancelado(ee.id, fecha))
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
        self.assertTrue(b._Bussiness__isCancelado(ee.id, fecha))
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
        self.assertTrue(b._Bussiness__isCancelado(ee.id, fecha))
    def testCancelarTurnosDistintoDiaDisponible(self):
        """Prueba cancelar turnos de un dia distinto al dia que atiende el especialista"""
        fecha = timezone.now().date()
        es = Especialidad.objects.create(descripcion="Clinico")
        e = Especialista.objects.create(nombre='n1', apellido='n1', dni=1234)
        ee = EspecialistaEspecialidad.objects.create(especialista=e, especialidad=es)
        Disponibilidad.objects.create(dia=fecha.weekday() + 1, horaDesde="10:00", horaHasta="13:00", ee=ee)
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
            turno.fecha = fecha
            turno.save()
        # Cancelo los turnos
        with self.assertRaises(CancelarTurnoException):
            b.cancelar_turnos(ee.especialista.id, fecha)
        turnos = Turno.objects.filter(ee=ee, fecha=fecha)
        for turno in turnos:
            t = Turno.objects.get(id=turno.id)
            self.assertEquals(t.estado, Turno.DISPONIBLE)
        self.assertFalse(b._Bussiness__isCancelado(ee.id, fecha))
    def testFatiga(self):
        """Prueba cancelar la mayor cantidad de turnos de un especialista"""
        fecha = timezone.now()
        es = Especialidad.objects.create(descripcion="Clinico")
        e = Especialista.objects.create(nombre='n1', apellido='n1', dni=1234)
        ee = EspecialistaEspecialidad.objects.create(especialista=e, especialidad=es)
        Disponibilidad.objects.create(dia=fecha.weekday(), horaDesde="00:00", horaHasta="23:59", ee=ee)
        # Creo los turnos
        turnos = b.crear_turnos_del_especialista(ee, 1)
        # Reservo todos los turnos
        logger.debug('turnos %s' % turnos)
        reservas = list()
        for turno in turnos:
            reservas.append(b.reservarTurnos(1, '12345678', [turno.id]))
        # Cancelo los turnos
        cancelados = b.cancelar_turnos(ee.especialista.id, fecha)
        self.assertEquals(len(reservas), len(cancelados))
        self.assertTrue(b._Bussiness__isCancelado(ee.id, fecha))
        
#===============================================================================
# CrearTurnoTestSuite
#===============================================================================
class CrearTurnoTestSuite(TestCase):
    """Esta clase agrupa las pruebas de crear turnos"""
    # defino las clases que estaran en la base de datos de prueba
    fixtures = ['test.json']
    # configuro el manager
    manager = TurnoManager()
    #===========================================================================
    # testUnDia
    #===========================================================================
    def testUnDia(self):
        """
        Crea turnos para un dia. Debe devolver una lista con mas de un turno
        """
        DIAS = 1
        # seteo rango de fechas
        fecha_inicio = timezone.now()
        fecha_fin = timezone.now() + timedelta(days=DIAS)
        # creo los turnos
        turnos = self.manager.crear_turnos(fecha_inicio, fecha_fin)
        # valido que haya al menos un turno creado
        self.assertGreater(len(turnos), 1)
        # valido que los turnos se hayan creado en el rango de fechas
        for turno in turnos:
            self.assertGreaterEqual(turno.fecha.date(), fecha_inicio.date())
            self.assertLessEqual(turno.fecha.date(), fecha_fin.date())
        
    #===========================================================================
    # test8Dias
    #===========================================================================
    def test_una_semana(self):
        """
        Crea una semana de turnos. Debe devolver una lista de turnos creados
        """
        DIAS = 7
        # seteo rango de fechas
        fecha_inicio = timezone.now()
        fecha_fin = timezone.now() + timedelta(days=DIAS)
        # creo los turnos
        turnos = self.manager.crear_turnos(fecha_inicio, fecha_fin)
        # valido que haya al menos un turno creado
        self.assertGreater(len(turnos), 1)
        # diferencia_dias: valida que la diferencia dias entre el primer y
        # ultimo turno se cumplan
        diferencia_dias = 0
        # valido que los turnos se hayan creado en el rango de fechas
        for turno in turnos:
            self.assertGreaterEqual(turno.fecha.date(), fecha_inicio.date())
            self.assertLessEqual(turno.fecha.date(), fecha_fin.date())
            diff = turno.fecha - fecha_inicio
            diferencia_dias = (diff.days if diff.days > diferencia_dias 
                                         else diferencia_dias)
        # valido que la diferencia de dias entre primer y ultimo turno se cumpla
        self.assertEqual(diferencia_dias, DIAS - 1)
        
    #===========================================================================
    # test_un_ano
    #===========================================================================
    def test_un_ano(self):
        """
        Crea turnos a un año para ver cuanto tarda. Debe devolver una lista de 
        turnos creados.
        """
        DIAS = 365
        # seteo rango de fechas
        fecha_inicio = timezone.now()
        fecha_fin = timezone.now() + timedelta(days=DIAS)
        # creo los turnos
        turnos = self.manager.crear_turnos(fecha_inicio, fecha_fin)
        # valido que haya al menos un turno creado
        self.assertGreater(len(turnos), 1)
        # diferencia_dias: valida que la diferencia dias entre el primer y
        # ultimo turno se cumplan
        diferencia_dias = 0
        # valido que los turnos se hayan creado en el rango de fechas
        for turno in turnos:
            self.assertGreaterEqual(turno.fecha.date(), fecha_inicio.date())
            self.assertLessEqual(turno.fecha.date(), fecha_fin.date())
            diff = turno.fecha - fecha_inicio
            diferencia_dias = (diff.days if diff.days > diferencia_dias 
                                         else diferencia_dias)
        # valido que la diferencia de dias entre primer y ultimo turno se cumpla
        self.assertEqual(diferencia_dias, DIAS - 1)
        
    #===========================================================================
    # test_dias_negativos
    #===========================================================================
    def test_dias_negativos(self):
        """
        Prueba que pasa si se pasan dias negativos a crear turnos. Debe devolver
        una lista vacia.
        """
        DIAS = -7
        # seteo rango de fechas
        fecha_inicio = timezone.now()
        fecha_fin = timezone.now() + timedelta(days=DIAS)
        # esperemos que lanze una excepcion por los dias
        with self.assertRaises(ValueError):
            # creo los turnos
            self.manager.crear_turnos(fecha_inicio, fecha_fin)
        
    #===========================================================================
    # test_rango_cero
    #===========================================================================
    def test_rango_cero(self):
        '''
        Prueba que pasa si se pasa el mismo dia de inicio y de fin. Debe 
        devolver una lista vacia.
        '''
        # seteo rango de fechas
        fecha_inicio = timezone.now()
        fecha_fin = fecha_inicio
        # creo los turnos
        turnos = self.manager.crear_turnos(fecha_inicio, fecha_fin)
        self.assertFalse(turnos)

    #===========================================================================
    # test_turnos_existentes
    #===========================================================================
    def test_turnos_existentes(self):
        """
        Prueba de crear turnos si todos los turnos a crear ya existen (doble 
        llamada a la funcion). Debe devolver una lista vacia de turnos creados, 
        fallando silenciosamente.
        """
        # seteo rango de fechas
        fecha_inicio = timezone.now()
        fecha_fin = timezone.now() + timedelta(days=1)
        # creo los turnos
        self.manager.crear_turnos(fecha_inicio, fecha_fin)
        # contamos la cantidad de elementos antes de crear por segunda vez
        antes = Turno.objects.all().count()  
        # intentamos crear turnos nuevamente. Falla silenciosa
        creados = self.manager.crear_turnos(fecha_inicio, fecha_fin) 
        # contamos la cantidad de elementos despues de crear
        despues = Turno.objects.all().count()
        # verifico que la cantidad de turnos antes y despues de crearlos
        # por segunda vez sea la misma
        self.assertEqual(antes, despues)
        # no deberia haber creado ningun turno repetido
        self.assertFalse(creados)
        
    #===========================================================================
    # test_algunos_existentes
    #===========================================================================
    def test_algunos_existentes(self):
        """
        Prueba de crear turnos si hay un turno existente. Debe devolver una 
        lista de turnos creados y el turno existente no debe estar en esa lista.
        """
        # seteo rango de fechas
        fecha_inicio = timezone.now()
        fecha_fin = timezone.now() + timedelta(days=1)
        # creamos el turno existente
        ee = EspecialistaEspecialidad.objects.all().first()
        turno = Turno.objects.create(fecha=fecha_inicio,
                                     ee=ee,
                                     sobreturno=False,
                                     estado=Turno.RESERVADO)
        # cuento la cantidad de elementos antes de crear
        antes = Turno.objects.all().count()
        # creo los turnos
        creados = self.manager.crear_turnos(fecha_inicio, fecha_fin)
        # cuento la cantidad de elementos despues de crear
        despues = Turno.objects.all().count()
        # verifico que el turno existente no este en la lista de turnos creados
        self.assertTrue(turno not in creados)
        # verifico que se hayan creado en la base de datos correctamente
        self.assertEqual(antes + len(creados), despues)

    #===========================================================================
    # test_sin_disponibilidad
    #===========================================================================
    def test_sin_disponibilidad(self):
        """
        Prueba que pasa si se crean turnos de un especialista que no posee 
        disponibilidad. Debe devolver una lista que no posea un turno del
        especialista en cuestion.
        """
        # creo un especialista mock
        es = Especialidad.objects.all().first()
        e = Especialista.objects.create(nombre='n', apellido='n', dni=1234)
        ee = EspecialistaEspecialidad.objects.create(especialista=e,
                                                     especialidad=es)
        # seteo rango de fechas
        fecha_inicio = timezone.now()
        fecha_fin = timezone.now() + timedelta(days=1)
        # creo los turnos de todos los especialistas
        creados = self.manager.crear_turnos(fecha_inicio, fecha_fin)
        # verifico que no se haya creado ningun turno para el especialista en 
        # cuestion
        for turno in creados:
            self.assertNotEqual(turno.ee.id, ee.id)
        
#      #==========================================================================
#      # testCrearSobreturnos
#      #==========================================================================
#      def testCrearSobreturnos(self):
#         """Prueba el proceso de creacion de sobreturnos"""
#         FRECUENCIA = 10  # minutos
#         es = Especialidad.objects.create(descripcion="Oftamologia")
#         e = Especialista.objects.create(nombre='n2', apellido='n2', dni=12345)
#         ee = EspecialistaEspecialidad.objects.create(especialista=e, especialidad=es, frecuencia_turnos=FRECUENCIA)
#         Disponibilidad.objects.create(dia='0', horaDesde="10:00", horaHasta="11:10", ee=ee)
#         fecha = b._Bussiness__proximoDia(0, timezone.now())
#         creados = b._Bussiness__crearSobreturnos(ee.id, fecha)
#         self.assertGreater(len(creados), 0)
#         turnos = Turno.objects.filter(ee__especialista=e, sobreturno=True).order_by('-fecha')
#         self.assertTrue(turnos.exists())
#         self.assertEqual(turnos.count(), b.MAX_SOBRETURNOS)
#         # Verificamos la diferencia en minutos de cada turno
#         for i in range(len(turnos) - 1):
#             diff = turnos[i].fecha - turnos[i + 1].fecha
#             minutos = (diff.seconds % 3600) // 60
#             self.assertEqual(minutos, FRECUENCIA * 2)


#===============================================================================
# ValidadoresTestSuite
#===============================================================================
class ValidadoresTestSuite(TestCase):
    #===========================================================================
    # test_longitud
    #===========================================================================
    def test_longitud(self):
        """
        Prueba que el validador funcione cuando una contraseña es menor a la 
        longitud permitida.
        """
        invalid_password = '12345'
        valid_password = '123456'
        other_valid_password = '1234567'
        validator = PasswordValidator(min_length=6)
        self.assertFalse(validator(valid_password))
        self.assertFalse(validator(other_valid_password))
        with self.assertRaises(ValidationError):
            validator(invalid_password)
            
    #===========================================================================
    # test_caracter_minuscula
    #===========================================================================
    def test_caracter_minuscula(self):
        """Prueba una contraseña con y sin caracteres minusculas"""
        invalid_password = '12345ASD'
        valid_password = '123456asd'
        validator = PasswordValidator(lower=True)
        self.assertFalse(validator(valid_password))
        with self.assertRaises(ValidationError):
            validator(invalid_password)
            
    #===========================================================================
    # test_caracter_mayuscula
    #===========================================================================
    def test_caracter_mayuscula(self):
        """Prueba una contraseña con y sin caracter mayuscula"""
        invalid_password = '12345asd'
        valid_password = '123456ASD'
        validator = PasswordValidator(upper=True)
        self.assertFalse(validator(valid_password))
        with self.assertRaises(ValidationError):
            validator(invalid_password)
            
    #===========================================================================
    # test_caracter_especial
    #===========================================================================
    def test_caracter_especial(self):
        """Prueba una contraseña con y sin caracteres especiales"""
        invalid_password = '12345ASD'
        valid_password = '123456asd_*'
        validator = PasswordValidator(special_characters=True)
        self.assertFalse(validator(valid_password))
        with self.assertRaises(ValidationError):
            validator(invalid_password)
            
    #===========================================================================
    # test_numero
    #===========================================================================
    def test_numero(self):
        """Prueba una contraseña con y sin numeros"""
        invalid_password = 'ASDasdf'
        valid_password = '123456asd'
        validator = PasswordValidator(number=True)
        self.assertFalse(validator(valid_password))
        with self.assertRaises(ValidationError):
            validator(invalid_password)
            
    #===========================================================================
    # test_caracter_minuscula_y_numero
    #===========================================================================
    def test_caracter_minuscula_y_numero(self):
        """
        Prueba una contraseña con varias politicas juntas. En este caso 
        minuscula y numero.
        """
        invalid_password = '12345ASD'
        valid_password = '123456asd'
        validator = PasswordValidator(lower=True, number=True)
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
        listaTurnos = [2, 3, 4]
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
        listaTurnos = range(1000, 1100)
        for i in listaTurnos:
            Turno.objects.create(fecha=timezone.now(),
                                 estado=Turno.DISPONIBLE,
                                 sobreturno=False,
                                 consultorio=Consultorio.objects.get(id=1),
                                 ee=EspecialistaEspecialidad.objects.get(id=1),
                                 id=i,)
        b.reservarTurnos(1, '12345678', listaTurnos)
        lreservas = b.consultar_reservas()
        self.assertTrue(lreservas)
    def testSinCoincidencia(self):
        '''Se filtran de forma tal que ninguna reserva coincida'''
        especialidad = Especialidad.objects.create(descripcion='dummy')
        afiliado = Afiliado.objects.create(numero='1', dni=1, nombre='1', apellido='1')
        especialista = Especialista.objects.create(nombre='a', apellido='a', dni=1)
        self.assertFalse(b.consultar_reservas(especialidad=especialidad))
        self.assertFalse(b.consultar_reservas(afiliado=afiliado))
        self.assertFalse(b.consultar_reservas(especialista=especialista))
    def testVariosFiltrosDisjuntos(self):
        '''Se filtra de manera que los filtros generen conjuntos disjuntos 
        (ej un especialista y una especialidad que no corresponde)'''
        especialidad = Especialidad.objects.create(descripcion='dummy')
        afiliado = Afiliado.objects.create(numero='1', dni=1, nombre='1', apellido='1')
        especialista = Especialista.objects.create(nombre='a', apellido='a', dni=1)
        self.assertFalse(b.consultar_reservas(especialidad=especialidad, especialista=especialista))
        self.assertFalse(b.consultar_reservas(afiliado=afiliado, especialista=especialista))
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

#===============================================================================
# Test utilizando servicios
#===============================================================================
class ServiceTestSuite(TestCase):
    # defino las clases que estaran en la base de datos de prueba
    fixtures = ['test.json']
    # defino el servicio a probar
    service = ReservaTurnosService()
    def setup(self):
        TestCase.setUp(self)
    #===========================================================================
    # test_crear_turnos
    #===========================================================================
    def test_crear_turnos(self):
        ' Crea un turno en la aplicacion.'
        # Solicitamos al servicio que cree un turno
        turno = self.service.crear_turno(timezone.now(),
                            EspecialistaEspecialidad.objects.get(id=1))
        # Verificamos que el turno se haya creado correctamente
        self.assertTrue(Turno.objects.filter(id=turno.id).exists())
    
    #===========================================================================
    # test_deshacer_creacion
    #===========================================================================
    def test_deshacer_creacion(self):
        ' Crea un turno en la aplicacion y deshace la ultima operacion. ' 
        # Creamos un turno para ver si lo deshace
        turno = self.service.crear_turno(timezone.now(),
                            EspecialistaEspecialidad.objects.get(id=1))
        # Verificamos que se haya creado
        self.assertTrue(Turno.objects.filter(id=turno.id).exists())    
        # Deshacemos la ultima accion 
        self.service.deshacer()
        # Verificamos que se haya cumplido
        self.assertFalse(Turno.objects.filter(id=turno.id).exists())
    
    #===========================================================================
    # test_deshacer_ultima_creacion
    #===========================================================================
    def test_deshacer_ultima_creacion(self):
        '''
        Crea varios turnos en la aplicacion y deshace la ultima operacion.
        Solo debe deshacer el ultimo turno creado
        ''' 
        # Deshacemos la nada 
        self.service.deshacer()
        # Creamos el primer turno
        turno1 = self.service.crear_turno(timezone.now(),
                            EspecialistaEspecialidad.objects.get(id=1))
        # Verificamos que se haya creado
        self.assertTrue(Turno.objects.filter(id=turno1.id).exists())    
        # Creamos un segundo turno para ver si lo deshace
        turno2 = self.service.crear_turno(timezone.now(),
                            EspecialistaEspecialidad.objects.get(id=1))
        # Verificamos que se haya creado
        self.assertTrue(Turno.objects.filter(id=turno2.id).exists())
        # Deshacemos la ultima accion 
        self.service.deshacer()
        # Verificamos que se haya cumplido
        self.assertTrue(Turno.objects.filter(id=turno1.id).exists())
        self.assertFalse(Turno.objects.filter(id=turno2.id).exists())
    
    #===========================================================================
    # test_crear_turnos_rango_un_dia
    #===========================================================================
    def test_crear_turnos_rango_un_dia(self):
        """
        Crea turnos para un dia. Debe devolver una lista con mas de un turno
        """
        # creo los turnos
        turnos = self.service.crear_turnos(dias=1)
        # valido que se hayan creado
        self.assertGreater(len(turnos), 1)
    
    #===========================================================================
    # test_crear_turnos_rango_fechas
    #===========================================================================
    def test_crear_turnos_rango_fechas(self):
        '''
        Crea turnos para un rango de fechas. 
        Debe devolver una lista con mas de un turno y estos deben tener fecha
        entre los rangos especificados.
        '''
        # defino fecha de inicio y fecha de fin
        fecha_inicio = timezone.now()
        fecha_fin = timezone.now() + timedelta(days=7)  # una semana
        # creo los turnos
        turnos = self.service.crear_turnos(fecha_inicio=fecha_inicio,
                                           fecha_fin=fecha_fin)
        # valido que se hayan creado al menos un turno
        self.assertGreater(len(turnos), 1)
        # valido que los turnos creados esten en el rango de fechas definidos
        for turno in turnos:
            self.assertGreaterEqual(turno.fecha.date(), fecha_inicio.date())
            self.assertLessEqual(turno.fecha.date(), fecha_fin.date())
    
    #===========================================================================
    # test_crear_turnos_sin_dias
    #===========================================================================
    def test_crear_turnos_sin_dias(self):
        """
        Prueba que pasa si se llama a la funcion de crear sin indicarle el 
        numero de dias. Debe devolver una lista de turnos creados. Debe tomar
        la cantidad de dias por defecto
        """
        # creo los turnos sin indicar la cantida de dias. Debe tomar el valor
        # por defecto
        turnos = self.service.crear_turnos()
        # valido la salida
        self.assertGreater(len(turnos), 1)
    
    #===========================================================================
    # test_varios_especialistas
    #===========================================================================
    def test_varios_especialistas(self):
        """
        Prueba que pasa si se crean turnos de varios especialistas.
        """
        # creo especialidades
        es1 = Especialidad.objects.create(descripcion="Clinico")
        es2 = Especialidad.objects.create(descripcion="Oftamologia")
        # creo especialistas
        e1 = Especialista.objects.create(nombre='n1', apellido='n1', dni=1234)
        e2 = Especialista.objects.create(nombre='n2', apellido='n2', dni=12345)
        # creo asociacion entre especialistas y especialidades
        ee1 = EspecialistaEspecialidad.objects.create(especialista=e1,
                                                      especialidad=es1)
        ee2 = EspecialistaEspecialidad.objects.create(especialista=e2,
                                                      especialidad=es2)
        # creo las disponibilidades
        Disponibilidad.objects.create(dia='0', horaDesde="10:00",
                                      horaHasta="13:00", ee=ee1)
        Disponibilidad.objects.create(dia='1', horaDesde="15:00",
                                      horaHasta="20:00", ee=ee2)
        # creo los turnos para una semana
        turnos = self.service.crear_turnos(dias=7)
        # verifico que que se hayan creado los turnos
        self.assertGreater(turnos, 0)
        # obtengo los turnos de los especialistas
        t1 = Turno.objects.filter(ee__especialista=e1)
        t2 = Turno.objects.filter(ee__especialista=e2)
        # verifico que se hayan creado turnos para cada especialista
        self.assertGreater(len(t1), 0)
        self.assertGreater(len(t2), 0)
        
    #===========================================================================
    # test_distinta_frecuencia
    #===========================================================================
    def test_distinta_frecuencia(self):
        """
        Prueba el algoritmo de creacion de turnos cambiando la frecuencia en 
        minutos de cada turno.
        """
        FRECUENCIA = 1  # minutos
        # obtengo especialidad
        es = Especialidad.objects.all().first()
        # obtengo especialista
        e = Especialista.objects.all().first()
        # creo asociacion entre especialista y especialidad y le seteo la 
        # frecuencia
        ee = (EspecialistaEspecialidad.objects
              .create(especialista=e, especialidad=es,
                      frecuencia_turnos=FRECUENCIA))
        # creo el objeto disponibilidad
        Disponibilidad.objects.create(dia='0', horaDesde="10:00",
                                      horaHasta="13:00", ee=ee)
        # creo los turnos para una semana
        creados = self.service.crear_turnos(dias=7)
        # obtengo los turnos del especialista
        turnos = Turno.objects.filter(ee=ee).order_by('-fecha')
        # verifico que se hayan creado correctamente
        self.assertGreater(creados, 0)
        # Verificamos la diferencia en minutos de cada turno
        for i in range(len(turnos) - 1):
            diff = turnos[i].fecha - turnos[i + 1].fecha
            minutos = (diff.seconds % 3600) // 60
            self.assertEqual(minutos, FRECUENCIA)
    #===========================================================================
    # test_crear_reserva
    #===========================================================================
    def test_crear_reserva(self):
        '''
        Verifica que se cree la reserva correctamente
        '''
        afiliado = Afiliado.objects.all().first()
        turnos = Turno.objects.filter(estado=Turno.DISPONIBLE)
        reserva = self.service.crear_reserva(afiliado, '12345678', turnos)
        reserva = Reserva.objects.get(id=reserva.id)
        self.assertTrue(reserva)
        self.assertEqual(reserva.afiliado, afiliado)
        for lr in LineaDeReserva.objects.filter(reserva=reserva):
            self.assertIn(lr.turno, turnos)
            self.assertEqual(lr.turno.estado, Turno.RESERVADO)
        
#===============================================================================
# CommandTestSuite
#===============================================================================
class CommandTestSuite(TestCase):
    '''
    Prueba que los comandos funcionen correctamente
    '''
    # defino las clases que estaran en la base de datos de prueba
    fixtures = ['test.json']
    #===========================================================================
    # setup
    #===========================================================================
    def setup(self):
        TestCase.setUp(self)
        
    #===========================================================================
    # test_crear_turno
    #===========================================================================
    def test_crear_turno(self):
        '''
        Verifica que la command de crear turno funcione correctamente. Debe 
        crear solo un turno
        '''
        # creo la command
        receiver = TurnoManager()
        command = OrdenCrearTurno(receiver=receiver)
        # seteo los parametros para crear el turno
        command.fecha = timezone.now()
        command.ee = EspecialistaEspecialidad.objects.all().first()
        # cuento la cantidad de turnos antes de ejecutar la command
        antes = Turno.objects.all().count()
        # ejecuto la command
        command.execute()
        # verifico cuantos turnos hay despues de ejecutar la command
        despues = Turno.objects.all().count()
        # verifico que la command me devuelva el turno creado
        self.assertTrue(command.turno)
        # verifico que despues tenga un turno mas que antes
        self.assertEquals(despues, antes + 1)
    
    #===========================================================================
    # test_crear_turno_validation
    #===========================================================================
    def test_crear_turno_validation(self):
        '''
        Verifica que la validacion de la command de crear turno funcione 
        correctamente. Debe lanzar una error ValueError
        '''
        # creo la command
        receiver = TurnoManager()
        command = OrdenCrearTurno(receiver)
        # verifico cuantos turnos hay antes de ejecutar la command
        antes = Turno.objects.all().count()
        # espero que lanze la excepcion
        with self.assertRaises(ValueError):
            # ejecuto la command
            command.execute()
        # verifico cuantos turnos hay despues de ejecutar la command
        despues = Turno.objects.all().count()
        # verifico que despues haya la misma cantidad que antes
        self.assertEquals(despues, antes)
    
    #===========================================================================
    # test_crear_turno_undo
    #===========================================================================
    def test_crear_turno_undo(self):
        '''
        Verifica que la orden crear turno se pueda deshacer
        '''
        # creo el command
        receiver = TurnoManager()
        command = OrdenCrearTurno(receiver=receiver)
        # seteo los parametros para crear el turno
        command.fecha = timezone.now()
        command.ee = EspecialistaEspecialidad.objects.all().first()
        # ejecuto la command
        command.execute()
        # obtengo el turno creado
        turno = command.turno
        # cuento la cantidad de turnos antes de DESHACER el command
        antes = Turno.objects.all().count()
        # deshago el command
        command.undo()
        # verifico cuantos turnos hay despues de deshacer el command
        despues = Turno.objects.all().count()
        # verifico que despues haya un turno menos
        self.assertEquals(despues, antes - 1)
        # verifico que el turno creado no exista mas
        self.assertFalse(Turno.objects.filter(id=turno.id).exists())
        # verifico que pasa si lo llamo de nuevo
        command.undo()
        
    #===========================================================================
    # test_crear_turnos
    #===========================================================================
    def test_crear_turnos(self):
        '''
        Verifica que la orden de crear turnos funcione correctamente. Debe 
        crear turnos en un rango de fechas
        '''
        # creo el command
        receiver = TurnoManager()
        command = OrdenCrearTurnos(receiver=receiver)
        # seteo los parametros para crear el turno
        command.fecha_inicio = timezone.now()
        command.fecha_fin = timezone.now() + timedelta(days=1)
        # cuento la cantidad de turnos antes de ejecutar el command
        antes = Turno.objects.all().count()
        # ejecuto la command
        command.execute()
        # verifico cuantos turnos hay despues de ejecutar el command
        despues = Turno.objects.all().count()
        # obtengo los turnos creados
        creados = command.turnos_creados
        # verifico que la lista no este vacia
        self.assertTrue(creados)
        # verifico que despues haya un turno menos
        self.assertEquals(despues, antes + len (creados))

    #===========================================================================
    # test_crear_turnos_undo
    #===========================================================================
    def test_crear_turnos_undo(self):
        '''
        Verifica que la orden crear turnos se pueda deshacer
        '''
        # creo el command
        receiver = TurnoManager()
        command = OrdenCrearTurnos(receiver=receiver)
        # seteo los parametros para crear el turno
        command.fecha_inicio = timezone.now()
        command.fecha_fin = timezone.now() + timedelta(days=1)
        # cuento la cantidad de turnos antes de ejecutar el command
        antes = Turno.objects.all().count()
        # ejecuto la command
        command.execute()
        # obtengo los turnos creados
        creados = command.turnos_creados
        # deshago el command
        command.undo()
        # verifico cuantos turnos hay despues de DESHACER el command
        despues = Turno.objects.all().count()
        # verifico que la lista no este vacia
        self.assertTrue(creados)
        # verifico que despues haya un turno menos
        self.assertEquals(antes, despues)
        # verifico que los turnos creados no existan en la base de datos
        for turno in creados:
            self.assertFalse(Turno.objects.filter(id=turno.id).exists())
        # verifico que pasa si lo llamo de nuevo
        command.undo()
            
    #===========================================================================
    # test_crear_turnos_validation
    #===========================================================================
    def test_crear_turnos_validation(self):
        '''
        Verifica que la validacion de la command de crear turnos funcione 
        correctamente. Debe lanzar una error ValueError
        '''
        # creo la command
        receiver = TurnoManager()
        command = OrdenCrearTurnos(receiver)
        # verifico cuantos turnos hay antes de ejecutar la command
        antes = Turno.objects.all().count()
        # espero que lanze la excepcion
        with self.assertRaises(ValueError):
            # ejecuto la command
            command.execute()
        # agrego solo fecha de inicio
        command.fecha_inicio = timezone.now()
        with self.assertRaises(ValueError):
            # ejecuto la command
            command.execute()
        # agrego solo fecha de fin
        command.fecha_inicio = None
        command.fecha_fin = timezone.now()
        with self.assertRaises(ValueError):
            # ejecuto la command
            command.execute()
        # verifico cuantos turnos hay despues de ejecutar la command
        despues = Turno.objects.all().count()
        # verifico que despues haya la misma cantidad que antes
        self.assertEquals(despues, antes)
        
    #===========================================================================
    # test_crear_reserva
    #===========================================================================
    def test_crear_reserva(self):
        '''
        Verifica que la orden de crear reserva funcione correctamente
        '''
        # creo el command
        receiver = ReservaManager()
        command = OrdenReservar(receiver=receiver)
        # seteo los parametros para reservar turnos turno
        command.afiliado = Afiliado.objects.all().first()
        command.telefono = '12345678'
        # selecciono todos los turnos disponibles
        command.turnos = Turno.objects.filter(estado=Turno.DISPONIBLE)
        # cuento la cantidad de reservas antes de ejecutar el command
        antes = Reserva.objects.all().count()
        # ejecuto la command
        command.execute()
        # verifico cuantos reservas hay despues de ejecutar el command
        despues = Reserva.objects.all().count()
        # obtengo la reserva creada
        reserva = command.reserva
        # verifico que haya una reserva mas
        self.assertEquals(despues, antes + 1)
        # verifico que los turnos esten reservados
        for lr in LineaDeReserva.objects.filter(reserva=reserva):
            self.assertEquals(lr.turno.estado, Turno.RESERVADO)
            self.assertEquals(lr.estado, Turno.RESERVADO)
    
    #===========================================================================
    # test_crear_reserva_undo
    #===========================================================================
    def test_crear_reserva_undo(self):
        '''
        Verifica que la orden de crear reserva se pueda deshacer
        '''
        # creo el command
        receiver = ReservaManager()
        command = OrdenReservar(receiver=receiver)
        # seteo los parametros para reservar turnos turno
        command.afiliado = Afiliado.objects.all().first()
        command.telefono = '12345678'
        # selecciono todos los turnos disponibles
        turnos = Turno.objects.filter(estado=Turno.DISPONIBLE)
        command.turnos = turnos
        # ejecuto la command
        command.execute()
        # obtengo la reserva creada
        reserva = command.reserva
        # deshago el comando
        command.undo()
        # verifico que la reserva creada no exista
        self.assertFalse(Reserva.objects.filter(id=reserva.id).exists())
        # verifico que los turnos esten disponibles
        for turno in turnos:
            # refresco el objeto desde la base de datos
            turno = Turno.objects.get(id=turno.id)
            self.assertEquals(turno.estado, Turno.DISPONIBLE)
        # verifico que pasa si lo llamo de nuevo
        command.undo()
    
    #===========================================================================
    # test_crear_reserva_validation
    #===========================================================================
    def test_crear_reserva_validation(self):
        '''
        Verifica que la validacion del la orden de crear reserva funcione
        correctamente
        '''
        # creo la command
        receiver = TurnoManager()
        command = OrdenReservar(receiver)
        # verifico cuantas reservas hay antes de ejecutar el command
        antes = Turno.objects.all().count()
        # espero que lanze la excepcion
        with self.assertRaises(ValueError):
            # ejecuto la command
            command.execute()
        # agrego solo afiliado
        command.afiliado = Afiliado.objects.all().first()
        # espero que lanze la excepcion
        with self.assertRaises(ValueError):
            command.execute()
        # agrego solo telefono
        command.afiliado = None
        command.telefono = '12345678'
        # espero que lanze la excepcion
        with self.assertRaises(ValueError):
            command.execute()
        # agrego solo turnos
        command.afiliado = None
        command.telefono = None
        command.turnos = Turno.objects.all()
        # espero que lanze la excepcion
        with self.assertRaises(ValueError):
            command.execute()
        # verifico cuantas reservas hay despues de ejecutar el command
        despues = Turno.objects.all().count()
        # verifico que despues haya la misma cantidad que antes
        self.assertEquals(despues, antes)
        