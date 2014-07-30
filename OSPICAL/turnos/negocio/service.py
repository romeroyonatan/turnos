'''
Este modulo agrupa los servicios ofrecidos por la aplicacion
Created on 30/07/2014

@author: romeroy
'''
import managers
import commands

class ReservaTurnosService(object):
    '''
    Muestra una interfaz para la manipulacion de turnos y reservas 
    '''

    def __init__(self):
        '''
        Constructor
        '''
        self.turno_manager = managers.TurnoManager()
    
    def crear_turno(self, fecha, ee):
        '''Permite crear un turno para un especialista y una especialidad.
        
        Parametros:
        * fecha: Fecha en la que se creara el turno
        * ee: Instancia de models.EspecialistaEspecialidad
        '''
        comando = commands.OrdenCrearTurno(self.turno_manager,
                                           fecha,
                                           ee)
        comando.execute()
        self.last_command = comando
        return comando.turno
    
    def deshacer(self):
        '''Deshace la accion del ultimo comando ejecutado'''
        self.last_command.undo()