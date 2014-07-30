# coding=utf-8
'''
Este modulo agrupa los manipuladores de los servicios que brinda la aplicacion
Created on 30/07/2014

@author: romeroy
'''
import logging
from django.db import transaction
from django.utils import timezone
# from turnos.models import Turno, Disponibilidad
from turnos.models import Turno, Disponibilidad, Settings
from datetime import datetime, timedelta
import dateutil

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
        @return:  Instancia del turno creado
        '''
        turno = Turno(fecha=fecha,
                      ee=ee,
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
        logging.info("Borrando turno %s" % turno)
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
        # verifico que se esten creando turnos para el futuro
        if fecha_inicio < timezone.now():
            # TODO: translate
            raise ValueError('No puede crear turnos en una fecha anterior \
                              a la actual')
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
        # XXX: Para solucionar problema de timezone :s
        # Si lo uso de la forma
        # tz = timezone.get_default_timezone() 
        # me da un offset -04:17 para America/Argentina/Buenos_Aires
        tz = dateutil.tz.tzoffset(None, -3 * 60 * 60)
        # configuro la hora que empezara a atender el especialista
        fecha_hora = (datetime.combine(dia, disponibilidad.horaDesde)
                      .replace(tzinfo=tz))
        # configuro la hora que dejara a atender el especialista
        hasta = (datetime.combine(dia, disponibilidad.horaHasta)
                 .replace(tzinfo=tz))
        # inicializo la lista de turnos creados
        creados = []
        # recorremos el rango de horarios desde que empieza a atender hasta
        # que finaliza
        while fecha_hora < hasta:
            # creamos el turno
            turno = self.crear_turno(fecha=fecha_hora,
                                     ee=disponibilidad.ee,
                                     consultorio=disponibilidad.consultorio)
            # agregamos el turno a la lista de creados
            creados.append(turno)
            # avanzamos al siguiente turno (depende de la frecuencia de cada
            # especialista)
            fecha_hora += timedelta(minutes=disponibilidad.ee.frecuencia_turnos)
        return creados
