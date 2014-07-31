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
