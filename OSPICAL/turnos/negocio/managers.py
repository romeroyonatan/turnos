# coding=utf-8
'''
Este modulo agrupa los manipuladores de los servicios que brinda la aplicacion
Created on 30/07/2014

@author: romeroy
'''
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

import excepciones
from turnos.models import Turno, Disponibilidad, Settings, Reserva, \
    LineaDeReserva, Afiliado


# from turnos.models import Turno, Disponibilidad
#===============================================================================
# TurnoManager
#===============================================================================
class TurnoManager():
    '''
    Permite administrar y manipular los turnos
    '''
    #===========================================================================
    # Constructor
    #===========================================================================
    def __init__(self):
        'Constructor'
        self.DIAS = int(self.__getSetting('cantidad_dias_crear_turnos', 7))
    
    #===========================================================================
    # __getSetting
    #===========================================================================
    def __getSetting(self, key, default_value=None):
        'Obtiene un parametro de configuracion desde la base de datos'
        # TODO: Ver si puede hacer esto en el service
        setting = Settings.objects.filter(key=key)
        return setting[0].value if setting else default_value
    
    #===========================================================================
    # crear_turno
    #===========================================================================
    def crear_turno(self, fecha, ee, consultorio=None, sobreturno=False):
        '''
        Permite crear un turno en el sistema.
        
        Parametros:
        @param fecha: -- Fecha/hora que tendra el turno
        @param ee: especialista_especialidad (models.EspecialistaEspecialidad)
                   Es la combinacion del especialista con su especialidad
        
        Retorna:
        @return:  Instancia del turno creado. None en caso que el turno a crear
        esté repetido
        '''
        # valido que el turno no exista
        if not Turno.objects.filter(fecha=fecha,
                                    ee=ee,
                                    sobreturno=sobreturno).exists():
            turno = Turno(fecha=fecha,
                          ee=ee,
                          estado=Turno.DISPONIBLE,
                          consultorio=consultorio,
                          sobreturno=sobreturno)
            turno.save()
            return turno
    
    #===========================================================================
    # borrar_turno
    #===========================================================================
    def borrar_turno(self, turno):
        '''
        Permite borrar un turno en el sistema.
        
        Parametros:
        @param turno: Turno a borrar del sistema
        '''
        return turno.delete()
    
    #===========================================================================
    # crear_turnos
    #===========================================================================
    @transaction.commit_on_success()
    def crear_turnos(self, fecha_inicio, fecha_fin):
        '''
        Crea los turnos en el sistema para todos las especialidades en el rango
        de fechas definidas o por cantidad de dias (empezando por el dia 
        actual).
        
        Parametros
        -------------
        @param fecha_inicio: Fecha por la que se comenzará a crear turnos. Debe
        ser posterior o igual a la fecha actual. Por defecto es la fecha del 
        sistema
        
        @param fecha_fin: Es la fecha hasta donde se crearán turnos. Por defecto
        se agregarán la cantidad de dias definidas en el parametro de 
        configuración 'cantidad_dias_crear_turnos'
        
        Retorna
        -------------
        @return: Lista de turnos creados 
        '''
        # valido las fechas ingresadas por parametro
        self.__crear_turnos_validate(fecha_inicio, fecha_fin)
        
        # inicializo la lista que contendra a los turnos creados
        creados = []
        # defino la fecha en la que se crearan los turnos
        fecha = fecha_inicio
        # recorro todos los dias del rango
        while fecha < fecha_fin:
            # obtengo las disponibilidades del dia
            for disponibilidad in (Disponibilidad.
                                   objects.filter(dia=fecha.weekday())):
                # creo los turnos del dia y los agrego a la lista de creados
                creados += self.__crear_turnos_del_dia(disponibilidad, fecha)
            # pasamos al siguiente dia
            fecha += timedelta(days=1)
        return creados
    
    #===========================================================================
    # __crear_turnos_validate
    #===========================================================================
    def __crear_turnos_validate(self, fecha_inicio, fecha_fin):
        '''
        Valida los parametros incresados en el metodo __crear_turnos_validate
        Parametros
        ------------------
        @param fecha_inicio:  
        @param fecha_fin:
        
        Retorna
        -----------
        @return: nada si todo es valido, en caso que no lanza excepciones
        
        Excepciones
        ------------
        ValueError -- Lanzada si los argumentos no superan la validacion
        '''
        # valido que la fecha de inicio no sea posterior a la fecha de fin
        if fecha_inicio > fecha_fin:
            raise ValueError("La fecha fin debe ser posterior a la fecha \
                             inicio")
        
        # defino un tiempo de gracia de un minuto para evitar problemas 
        # de retrasos
        ahora = timezone.now() - timedelta(minutes=1)
        # valido que no se quiera crear turnos en el pasado
        if fecha_inicio < ahora:
            raise ValueError("La fecha inicio no debe ser en el pasado")
    
    #===========================================================================
    # __crear_turnos_del_dia
    #===========================================================================
    def __crear_turnos_del_dia(self, disponibilidad, dia):
        ''' Crea todos los turnos del dia de un especialista.
        
        Parametros
        -------------
        @param disponibilidad: Instancia de models.Disponibilidad al que se le
        crearan los turnos
        
        @param dia: Dia que se crearan los turnos
        
        Retorna
        ------------
        @return: Lista de turnos creados
        '''
        # configuro la zona horaria
        tz = timezone.get_default_timezone() 
        # configuro la hora que empezara a atender el especialista
        desde = tz.localize(datetime.combine(dia, disponibilidad.horaDesde))
        # configuro la hora que dejara a atender el especialista
        hasta = tz.localize(datetime.combine(dia, disponibilidad.horaHasta))
        # inicializo la lista de turnos creados
        creados = []
        # recorremos el rango de horarios desde que empieza a atender hasta
        # que finaliza
        while desde < hasta:
            # creamos el turno
            turno = self.crear_turno(fecha=desde,
                                     ee=disponibilidad.ee,
                                     consultorio=disponibilidad.consultorio)
            # si el turno fue creado
            if turno:
                # agregamos el turno a la lista de creados
                creados.append(turno)
            # avanzamos al siguiente turno (depende de la frecuencia de cada
            # especialista)
            desde += timedelta(minutes=disponibilidad.ee.frecuencia_turnos)
        return creados
    # TODO:testGetDiasTurnos

#===============================================================================
# ReservaManager
#===============================================================================
class ReservaManager:
    '''
    Permite administrar las operaciones sobre las reservas de los turnos tales
    como crear una reserva, cancelarla, confirmarla o modificarla. 
    Implementa la logica de negocio sobre las reservas
    '''
    #===========================================================================
    # crear_reserva
    #===========================================================================
    @transaction.atomic()
    def crear_reserva(self, afiliado, telefono, turnos):
        '''
        Crea una reserva de turnos para un afiliado.
        
        Parametros
        ------------------
        @param afiliado: Instancia de la clase models.Afiliado al cual se le
                         asignara la reserva
        @param telefono: Telefono de contacto del afiliado para comunicarse 
                         en caso de algun problema con la reserva
        @param turnos: Lista o tupla de models.Turno a reservar
        
        @type afiliado: models.Afiliado
        @type telefono: __builtin__.string
        
        Retorna
        -----------
        @return: Objeto reserva con los datos de la misma.

        Excepciones
        -------------------
        TurnoNotExistsException -- En caso que algun turno a reserva no exista
        AfiliadoNotExistsException -- En caso que el afiliado no exista
        ValueError -- En caso que se pase algun parametro como objeto nulo
        TurnoReservadoException -- En caso que algun turno a reservar
                                   ya este reservado
        '''
        self.__crear_reserva_validate(afiliado, telefono, turnos)
        reserva = Reserva.objects.create(afiliado=afiliado,
                                         telefono=telefono)
        for turno in turnos:
            turno.estado = Turno.RESERVADO
            turno.save()
            LineaDeReserva.objects.create(turno=turno,
                                          reserva=reserva,
                                          estado=Turno.RESERVADO)
        return reserva
    
    #===========================================================================
    # __crear_reserva_validate
    #===========================================================================
    def __crear_reserva_validate(self, afiliado, telefono, turnos):
        '''
        Valida los parametros para crear una reserva
        
        Parametros
        ------------------
        @param afiliado: Instancia de la clase models.Afiliado al cual se le
                         asignara la reserva
        @param telefono: Telefono de contacto del afiliado para comunicarse 
                         en caso de algun problema con la reserva
        @param turnos: Lista o tupla de models.Turno a reservar
        
        Retorna
        -----------
        @return: Nada si todo esta bien, en caso contrario devuelve una
                excepcion

        Excepciones
        -------------------
        TurnoNotExistsException -- En caso que algun turno a reserva no exista
        AfiliadoNotExistsException -- En caso que el afiliado no exista
        ValueError -- En caso que se pase algun parametro como objeto nulo
        TurnoReservadoException -- En caso que algun turno a reservar
                                   ya este reservado
        '''
        # valido que la lista de turnos no este vacia
        if not turnos:
            raise ValueError("Lista de turnos vacia")
        # valido que ningun parametro sea nulo
        if not afiliado or not telefono:
            raise ValueError("Invalid parameters")
        # valido que el afiliado exista
        if not Afiliado.objects.filter(id=afiliado.id).exists():
            raise excepciones.AfiliadoNotExistsException("Afiliado inexistente")
        # valido si los turnos a reservar existen
        for turno in turnos:
            if not Turno.objects.filter(id=turno.id).exists():
                raise excepciones.TurnoNotExistsException("Turno inexistente")
            if not (Turno.objects.filter(id=turno.id, estado=Turno.DISPONIBLE)
                    .exists()):
                raise excepciones.TurnoReservadoException("Turno reservado")
    
    def get_turnos_reservados(self, afiliado):
        '''
        Obtiene una tupla de diccionarios con los turnos reservados del afiliado
        
        Parametros
        ------------------
        @param afiliado: Instancia de la clase models.Afiliado al cual se le
                         desea consultar sus reservas
        
        Retorna
        -----------
        @return: Tupla de diccionarios con los turnos reservados del afiliado o
                 None si el afiliado no tiene ninguna reserva
                 
                 Cada elemento de la tupla es un diccionario con estas claves:
                 especialista, especialidad, fecha_reserva, fecha_turno y 
                 consultorio 
        '''
        pass
    
