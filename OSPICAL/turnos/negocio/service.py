# coding=utf-8
'''
Este modulo agrupa los servicios ofrecidos por la aplicacion
Created on 30/07/2014

@author: romeroy
'''
import managers
import commands
from turnos.models import Settings

from django.utils import timezone
from datetime import timedelta

#===============================================================================
# ReservaTurnosService
#===============================================================================
class ReservaTurnosService(object):
    '''
    Muestra una interfaz para la manipulacion de turnos y reservas 
    '''

    #===========================================================================
    # constructor
    #===========================================================================
    def __init__(self):
        '''
        Constructor
        '''
        self.turno_manager = managers.TurnoManager()
        self.reserva_manager = managers.ReservaManager()
        self.DIAS = int(self.__getSetting('cantidad_dias_crear_turnos', 7))
        
    #===========================================================================
    # __getSetting
    #===========================================================================
    def __getSetting(self, key, default_value=None):
        '''
        Obtiene un parametro de configuracion (key) y se puede setear un valor 
        por defecto.
        '''
        setting = Settings.objects.filter(key=key)
        return setting[0].value if setting else default_value
        
    #===========================================================================
    # __ejecutar
    #===========================================================================
    def __ejecutar(self, command):
        '''
        Ejecuta un comando
        
        Parametros
        ------------------
        @param command: Comando a ejecutar
        
        Retorna
        -----------
        @return: lo que devuelva el metodo 'execute' del comando
        '''
        r = command.execute()
        self.last_command = command
        return r
    
    #===========================================================================
    # crear_turno
    #===========================================================================
    def crear_turno(self, fecha, ee):
        '''Permite crear 1 (uno) turno para un especialista y una especialidad.
        
        Parametros:
        * fecha: Fecha en la que se creara el turno
        * ee: Instancia de models.EspecialistaEspecialidad
        '''
        orden = commands.OrdenCrearTurno(self.turno_manager,
                                           fecha,
                                           ee)
        self.__ejecutar(orden)
        return orden.turno
    
    #===========================================================================
    # crear_turnos
    #===========================================================================
    def crear_turnos(self, fecha_inicio=None, fecha_fin=None, dias=None):
        '''
        Crea turnos para todas las especialidades en el rango de fechas indicado
        por fecha_inicio y fecha_fin o por la cantidad de dias contando desde
        la fecha actual del sistema. Si no se define ningun rango utilizará
        la cantidad de dias definida en el parámetro de configuración 
        'cantidad_dias_crear_turnos'
        
        Parametros
        ------------------
        @param fecha_inicio(opcional): Fecha en la que se empezara a crear
        turnos
        @param fecha_fin(opcional): Fecha en la que se termina de crear turnos
        @param dias(opcional): Cantidad de dias que se crearan turnos.
        Define el rango fecha_inicio y fecha_fin con la fecha actual y la fecha
        actual mas los dias indicados por este parametro.
        
        Retorna
        -----------
        @return: Lista de turnos creados
        '''
        # establecemos el rango de fechas de inicio y fecha de fin
        ahora = timezone.now()
        fecha_inicio = fecha_inicio if fecha_inicio is not None else ahora
        if fecha_fin is None:
            dias = dias if dias is not None else self.DIAS
            fecha_fin = ahora + timedelta(days=dias)
        # creamos la orden
        orden = commands.OrdenCrearTurnos(self.turno_manager,
                                          fecha_inicio,
                                          fecha_fin)
        # ejecutamos la orden
        self.__ejecutar(orden)
        # devolvemos la lista de turnos creados
        return orden.turnos_creados
    
    #===========================================================================
    # deshacer
    #===========================================================================
    def deshacer(self):
        '''Deshace la accion del ultimo comando ejecutado'''
        # verifico que haya un comando en el historial
        if 'last_command' in self.__dict__:
            # deshago el ultimo comando
            self.last_command.undo()
            
    #===========================================================================
    # crear_reserva
    #===========================================================================
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
        # creamos la orden
        orden = commands.OrdenReservar(self.reserva_manager,
                                            afiliado,
                                            telefono,
                                            turnos)
        # ejecutamos la orden
        self.__ejecutar(orden)
        # devolvemos la reserva
        return orden.reserva