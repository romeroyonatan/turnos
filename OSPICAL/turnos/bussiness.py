import datetime
import logging
from turnos.models import *

# Get an instance of a logger
logger = logging.getLogger(__name__)

class Bussiness():
    
    def getAfiliados(self, parametro, valor):
        # Buscar en la base de datos local
        logger.debug("Obteniendo afiliado %s %s" %(parametro, valor))
        filtro = dict([(parametro, valor)])
        queryset = Afiliado.objects.filter(**filtro)
        data = [item for item in queryset.values()]
        if not data:
            logger.debug("Afiliado %s %s no encontrado. Buscando en \
            interfaz de usuarios" %(parametro, valor))
            # TODO Buscar en la interfaz de consulta de afiliados
            pass
        return data
    
    def getTurnosDisponibles(self, especialista, fecha):
        logger.debug("Obteniendo turnos disponibles especialista:%s fecha:%s" %(especialista, fecha))
        disponibles = self.__buscarTurnosDisponibles(especialista, fecha)
        logger.debug("Turnos disponibles para el dia %s: %s" % (fecha, disponibles))
        if not disponibles and not self.__haySobreturnos(especialista, fecha):
            disponibles=self.crearSobreturnos()
        return disponibles
    
    def __buscarTurnosDisponibles(self, especialista, fecha):
        queryset = Turno.objects.filter(ee__especialista=especialista, 
                                        fecha__year=fecha.year,
                                        fecha__month=fecha.month,
                                        fecha__day=fecha.day,
                                        estado=Turno.DISPONIBLE,
                                        )
        return [item for item in queryset.values()]
    
    def __haySobreturnos(self, especialista, fecha):
        queryset = Turno.objects.filter(ee__especialista=especialista, 
                                        fecha__year=fecha.year,
                                        fecha__month=fecha.month,
                                        fecha__day=fecha.day,
                                        sobreturno=True,
                                        )
        return queryset.count() > 0
    
    def crearSobreturnos(self):
        logger.debug("Creando sobreturnos para el dia%s" % fecha)
        # TODO Crear sobreturnos
        return {}
    
    def getDiaTurnos(self, especialista):
        """Devuelve una lista de dias y el estado (Completo, Sobreturno)"""
        logger.debug("Obteniendo dias de turnos %s " % especialista)
        data=[]
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
        filter = self.__getFiltroFecha(especialista, fecha)
        query = Turno.objects.filter(**filter).only("id")
        return not query.exists()
    
    def __haySobreturnos(self, especialista, fecha):
        """ Verifica si hay sobreturnos en un dia para un especialista """
        filter = self.__getFiltroFecha(especialista, fecha)
        filter['sobreturno'] = True
        query = Turno.objects.filter(**filter).only("id")
        return query.exists()
    
    def __getFiltroFecha(self,especialista,fecha):
        """Devuelve un filtro para buscar los turnos disponibles del especialista 
        en una fecha determinada"""
        filter = {}
        filter['ee__especialista__id'] = especialista
        filter['fecha__day'] = fecha.day
        filter['fecha__month'] = fecha.month
        filter['fecha__year'] = fecha.year
        filter['estado'] = Turno.DISPONIBLE
        return filter
    
    def reservarTurnos(self, afiliado, telefono, turnos):
        """ Reserva turnos a afiliado"""
        #TODO Verificar excepciones
        logger.info("Reservando turnos")
        logger.debug("afiliado:%s, telefono:%s, turnos:%s" % (afiliado,telefono,turnos))
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
    
    def verificarPresentismo(request, afiliado_id):
        # Contar cantidad de veces ausente en el plazo configurado
        # presentismo_ok si es menor a la cantidad tolerable
        return True
