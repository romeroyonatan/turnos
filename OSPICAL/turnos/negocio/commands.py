# coding=utf-8
'''
Este modulo encapsula a todas las clases que representan acciones (comandos)
a ejecutarse en el sistema y que deben tener la capacidad de deshacerse y 
almacenarse para auditorias
Created on 30/07/2014

@author: romeroy
'''

#===============================================================================
# Command
#===============================================================================
class Command():
    '''
    Representa un comando a ejecutarse. Implementa patron command de GOF
    '''
    def execute(self):
        '''Ejecuta el comando'''
        raise NotImplementedError
    def undo(self):
        '''Deshace la ejecucion del comando'''
        raise NotImplementedError
    
#===============================================================================
# OrdenCrearTurno
#===============================================================================
class OrdenCrearTurno(Command):
    '''
    Representa una orden para crear un turno en el sistema
    '''
    #===========================================================================
    # __init__
    #===========================================================================
    def __init__(self, receiver, fecha=None, ee=None):
        '''Constructor.
        
        Parametros:
        * receiver: Objeto que recibira las peticiones de crear_turno()
        * fecha (opcional): Fecha que se realizara el turno
        * ee (opcional): instancia de models.EspecialidadEspecialista 
            que son responsables de cumplir el turno
            
        Los parametros opcionales en la construccion deben ser completados
        antes de ejectutar el comando
        '''
        self.receiver = receiver
        self.fecha = fecha
        self.ee = ee
    #===========================================================================
    # execute
    #===========================================================================
    def execute(self):
        '''Ejecuta la creacion del turno.
        
        ATENCION:
        Antes de ejecutar el comando debe estar definida la fecha y ee
        '''
        if self.fecha is None or self.ee is None:
            raise ValueError("You must define 'fecha' and 'ee' before \
                             execute this command")
        
        self.turno = self.receiver.crear_turno(self.fecha, self.ee)
    #===========================================================================
    # undo
    #===========================================================================
    def undo(self):
        'Deshace la creacion del turno'
        self.receiver.borrar_turno(self.turno)
