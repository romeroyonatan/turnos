'''
Este modulo contiene las excepciones generadas por la aplicacion
Created on 01/08/2014

@author: romeroy
'''

class TurnosAppException(Exception):
    def __init__(self, message=None, more_info=None, prev=None):
        self.message = message
        self.more_info = more_info
        self.prev = prev
    def __str__(self):
        return self.message   
class ReservaTurnoException(TurnosAppException):
    pass
class TurnoNotExistsException(ReservaTurnoException):
    pass
class AfiliadoNotExistsException(ReservaTurnoException):
    pass
class TurnoReservadoException(ReservaTurnoException):
    pass
class ConfirmarReservaException(TurnosAppException):
    pass
class CancelarReservaException(TurnosAppException):
    pass
class CancelarTurnoException(TurnosAppException):
    pass        