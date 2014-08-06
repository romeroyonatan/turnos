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
    
    Atributos
    -----------------
    receiver -- Es el manejador que recibe la orden. Debe implementar el
                metodo 'crear_turno' y 'borrar_turno'
    fecha -- Instancia de datetime en el que se creara el turno
    ee -- Especialista para el cual se creara el turno
    turno -- Instancia del turno creado despues de ejecutar el comando
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
        # verifico que la fecha y el ee esten seteados antes de ejecutar el
        # comando
        if self.fecha and self.ee:
            # mando a crear el turno
            self.turno = self.receiver.crear_turno(self.fecha, self.ee)
        else:
            # lanzo excepcion
            raise ValueError("You must define 'fecha' and 'ee' before \
                             execute this command")
        return self.turno
    #===========================================================================
    # undo
    #===========================================================================
    def undo(self):
        'Deshace la creacion del turno'
        # valido que haya un turno creado
        if 'turno' in self.__dict__ and self.turno:
            # borro el turno
            self.receiver.borrar_turno(self.turno)
            del self.turno

#===============================================================================
# OrdenCrearTurnos
#===============================================================================
class OrdenCrearTurnos(Command):
    '''
    Representa una orden para crear turnos de todas las especialidades en un
    rango de fechas
    
    Atributos
    -----------------
    receiver -- Es el manejador que recibe la orden. Debe implementar el
                metodo 'crear_turnos' y 'borrar_turno'
    fecha_inicio -- Fecha en la que se empezara a crear turnos
    fecha_fin -- Fecha en la que se termina de crear turnos
    turnos_creados -- Lista de turnos creados despues de ejecutar el comando
    '''
    #===========================================================================
    # __init__
    #===========================================================================
    def __init__(self, receiver, fecha_inicio=None, fecha_fin=None):
        '''Constructor.
        
        Parametros
        ------------------
        @param fecha_inicio(opcional): Fecha en la que se empezara a crear
        turnos
        @param fecha_fin(opcional): Fecha en la que se termina de crear turnos
            
        Los parametros opcionales en la construccion deben ser completados
        antes de ejectutar el comando
        '''
        self.receiver = receiver
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        
    #===========================================================================
    # execute
    #===========================================================================
    def execute(self):
        '''Ejecuta la creacion del turno.
        
        ATENCION:
        Antes de ejecutar el comando debe estar definida la fecha_incio y
        fecha_fin
        '''
        # verifico que esten seteados la fecha de inicio y la fecha de fin
        if self.fecha_inicio and self.fecha_fin:
            self.turnos_creados = self.receiver.crear_turnos(self.fecha_inicio,
                                                             self.fecha_fin)
        else:
            raise ValueError("You must define 'fecha_inicio' and 'fecha_fin' \
                              before execute this command")
        # ordeno crear los turnos
        return self.turnos_creados

    #===========================================================================
    # undo
    #===========================================================================
    def undo(self):
        'Deshace la creacion de los turnos'
        # valido que haya turnos creados
        if 'turnos_creados' in self.__dict__ and self.turnos_creados:
            # borro los turnos
            for turno in self.turnos_creados:
                self.receiver.borrar_turno(turno)
            del self.turnos_creados

#===============================================================================
# OrdenReservar
#===============================================================================
class OrdenReservar(Command):
    '''
    Representa una orden para reservar turnos.
    
    Atributos
    -----------------
    receiver -- Es el manejador que recibe la orden. Debe implementar el
                metodo 'crear_reserva' y 'borrar_reserva'
    afiliado -- Instancia de models.Afiliado quien reserva los turnos
    telefono -- Telefono de contacto del afiliado
    turnos -- Iterable de turnos (models.Turno) a reservar (lista o tupla)
    '''
    #===========================================================================
    # __init__
    #===========================================================================
    def __init__(self, receiver, afiliado=None, telefono=None, turnos=None):
        '''
        Contructor.
        '''
        self.receiver = receiver
        self.afiliado = afiliado
        self.telefono = telefono
        self.turnos = turnos
    
    #===========================================================================
    # execute
    #===========================================================================
    def execute(self):
        '''
        Ejecuta la reserva de los turnos.
        
        ATENCION:
        Antes de ejecutar el comando debe estar definida la afiliado, telefono 
        y turnos
        '''
        # valido los parametros
        if self.afiliado and self.telefono and self.turnos:
            # reservo los turnos
            self.reserva = self.receiver.crear_reserva(self.afiliado,
                                                       self.telefono,
                                                       self.turnos)
        else:
            # lanzo excepcion en caso que falte algun parametro
            raise ValueError("You must define 'afiliado' and 'telefono' \
                              'turnos' before execute this command")
        # devuelvo la instancia de la reserva
        return self.reserva

    #===========================================================================
    # undo
    #===========================================================================
    def undo(self):
        '''
        Borra la reserva del turno.
        '''
        # verifico que haya reservado un turno
        if 'reserva' in self.__dict__ and self.reserva:
            # borro la reserva
            self.receiver.borrar_reserva(self.reserva)
            del self.reserva
        