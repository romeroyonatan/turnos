import datetime
import logging
from turnos.models import *


# Get an instance of a logger
logger = logging.getLogger(__name__)

class Bussiness():
    
    def getAfiliados(self, parametro, valor):
        # Buscar en la base de datos local
        logger.debug("Obteniendo afiliado %s %s" % (parametro, valor))
        filtro = dict([(parametro, valor)])
        queryset = Afiliado.objects.filter(**filtro)
        data = [item for item in queryset.values()]
        if not data:
            logger.debug("Afiliado %s %s no encontrado. Buscando en \
            interfaz de usuarios" % (parametro, valor))
            # TODO Buscar en la interfaz de consulta de afiliados
            pass
        return data
    
    def getTurnosDisponibles(self, especialista, fecha):
        disponibles = self.__buscarTurnosDisponibles(especialista, fecha)
        logger.debug("Turnos disponibles para el dia %s: %s" % (fecha, disponibles))
        if not disponibles and not self.__haySobreturnos(especialista, fecha):
            disponibles = self.crearSobreturnos(especialista, fecha)
        return disponibles
    
    def __buscarTurnosDisponibles(self, especialista, fecha):
        logger.debug("Obteniendo turnos disponibles especialista_id:%s fecha:%s" % (especialista, fecha))
        queryset = Turno.objects.filter(ee__especialista=especialista,
                                        fecha__year=fecha.year,
                                        fecha__month=fecha.month,
                                        fecha__day=fecha.day,
                                        estado=Turno.DISPONIBLE,
                                        )
        return [item for item in queryset.values()]
    
    def __haySobreturnos(self, especialista, fecha):
        """ Verifica si hay sobreturnos en un dia para un especialista """
        filtro = self.__getFiltroFecha(especialista, fecha)
        filtro['sobreturno'] = True
        query = Turno.objects.filter(**filtro).only("id")
        return query.exists()
    
    def crearSobreturnos(self, especialista, fecha):
        logger.info("Creando sobreturnos para el dia:%s" % fecha)
        # TODO Crear sobreturnos
        return {}
    
    def getDiaTurnos(self, especialista):
        """Devuelve una lista de dias y el estado (Completo, Sobreturno)"""
        logger.debug("Obteniendo dias de turnos para el especialista_id:%s " % especialista)
        data = []
        queryset = Turno.objects.filter(ee__especialista__id=especialista,
                                        fecha__gte=datetime.datetime.now()).dates('fecha', 'day')
        for fecha in queryset:
            estado = None
            if self.__isCompleto(especialista, fecha):
                estado = 'C'
            else:
                if self.__haySobreturnos(especialista, fecha):
                    estado = 'S'
            data.append({'fecha':fecha, 'estado':estado})
        return data
    
    def __isCompleto(self, especialista, fecha):
        """ Verifica si el dia esta completo para el especialista,
        es decir que no haya turnos disponibles para ese dia """
        filtro = self.__getFiltroFecha(especialista, fecha)
        query = Turno.objects.filter(**filtro).only("id")
        return not query.exists()
    
    def __getFiltroFecha(self, especialista, fecha):
        """Devuelve un filtro para buscar los turnos disponibles del especialista 
        en una fecha determinada"""
        filtro = {}
        filtro['ee__especialista__id'] = especialista
        filtro['fecha__day'] = fecha.day
        filtro['fecha__month'] = fecha.month
        filtro['fecha__year'] = fecha.year
        filtro['estado'] = Turno.DISPONIBLE
        return filtro
    
    def reservarTurnos(self, afiliado, telefono, turnos):
        """ Reserva turnos a afiliado"""
        # TODO Verificar excepciones, historial de turnos
        logger.info("Reservando turnos")
        logger.debug("afiliado:%s, telefono:%s, turnos:%s" % (afiliado, telefono, turnos))
        reserva = Reserva()
        reserva.afiliado = Afiliado.objects.get(id=afiliado)
        reserva.telefono = telefono
        reserva.fecha = datetime.datetime.now()
        reserva.save()
        logger.debug("Reserva id:%s" % reserva.id)
        for turno in turnos:
            lr = LineaDeReserva()
            t = Turno.objects.get(id=turno)
            lr.turno = t
            lr.reserva = reserva
            lr.estado = lr.turno.estado = Turno.RESERVADO
            lr.save()
            t.save()
            logger.debug("Linea de reserva id:%s" % lr.id)
        return True
    
    def verificarPresentismo(self, afiliado_id):
        # Contar cantidad de veces ausente en el plazo configurado
        # presentismo_ok si es menor a la cantidad tolerable
        return True
