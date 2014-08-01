'''
Este modulo contiene las excepciones generadas por la aplicacion
Created on 01/08/2014

@author: romeroy
'''

class TurnosAppException(Exception):
    '''
    Excepcion generica de la aplicacion de reserva de turnos. 
    ''' 
    def __init__(self, message=None, more_info=None, prev=None):
        self.message = message
        self.more_info = more_info
        self.prev = prev
    def __str__(self):
        return self.message   
class ReservaTurnoException(TurnosAppException):
    '''
    Excepcion generada al reservar un turno.
    '''
    pass
class TurnoNotExistsException(ReservaTurnoException):
    '''
    Excepcion generada cuando se quiere reservar un turno inexistente.
    '''
    pass
class AfiliadoNotExistsException(ReservaTurnoException):
    '''
    Excepcion generada cuando se quiere reservar un turno para un afiliado
    inexistente.
    '''
    pass
class TurnoReservadoException(ReservaTurnoException):
    '''
    Excepcion generada cuando se quiere reservar un turno que ya esta reservado.
    '''
    pass
class ConfirmarReservaException(TurnosAppException):
    '''
    Excepcion generada cuando se quiere confirmar una reserva
    '''
    pass
class CancelarReservaException(TurnosAppException):
    '''
    Excepcion generada al cancelar una reserva
    '''
    pass
class CancelarTurnoException(TurnosAppException):
    '''
    Excepcion generada cuando se quiere cancelar un turno
    '''
    pass        