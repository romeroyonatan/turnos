import logging
from django.utils import timezone
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
            # TODO: Buscar en la interfaz de consulta de afiliados
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
        filtro = self.__getFiltroFecha(especialista, fecha)
        queryset = Turno.objects.filter(**filtro)
        return [item for item in queryset.values()]
    
    def __haySobreturnos(self, especialista, fecha):
        """ Verifica si hay sobreturnos en un dia para un especialista """
        filtro = self.__getFiltroFecha(especialista, fecha)
        filtro['sobreturno'] = True
        query = Turno.objects.filter(**filtro).only("id")
        return query.exists()
    
    def crearSobreturnos(self, especialista, fecha):
        logger.info("Creando sobreturnos para el dia:%s" % fecha)
        # TODO: Crear sobreturnos
        return {}
    
    def getDiaTurnos(self, especialista):
        """Devuelve una lista de dias y el estado (Completo, Sobreturno)"""
        logger.debug("Obteniendo dias de turnos para el especialista_id:%s " % especialista)
        data = []
        queryset = Turno.objects.filter(ee__especialista__id=especialista,
                                        fecha__gte=timezone.now()).dates('fecha', 'day')
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
    
    def reservarTurnos(self, afiliado, telefono, turnos, empleado=None):
        """ Reserva turnos a afiliado"""
        # TODO: Verificar excepciones, historial de turnos
        # FIXME: Envolver todo en una Transaccion
        logger.info("Reservando turnos")
        logger.debug("afiliado:%s, telefono:%s, turnos:%s" % (afiliado, telefono, turnos))
        if turnos:
            reserva = self.__crearReserva(afiliado, telefono)
            logger.debug("Reserva id:%s" % reserva.id)
            for turno_id in turnos:
                turno = self.__reservarTurno(reserva, turno_id, empleado);
                lr = LineaDeReserva.objects.create(turno=turno,
                                                   reserva=reserva)
                logger.debug("Linea de reserva id:%s" % lr.id)
            return reserva.id
        return False
    
    def __crearReserva(self, afiliado, telefono):
        reserva = Reserva()
        reserva.afiliado = Afiliado.objects.get(id=afiliado)
        reserva.telefono = telefono
        reserva.fecha = timezone.now()
        reserva.save()
        return reserva
    
    def __reservarTurno(self, reserva, turno_id, empleado):
        turno = Turno.objects.get(id=turno_id)
        HistorialTurno.objects.create(fecha=timezone.now(),
                                   estadoAnterior=turno.estado,
                                   estadoNuevo=Turno.RESERVADO,
                                   turno=turno,
                                   empleado=empleado)
        turno.estado = Turno.RESERVADO
        turno.save()
        return turno
        
    def verificarPresentismo(self, afiliado_id):
        # TODO: Contar cantidad de veces ausente en el plazo configurado
        # TODO: presentismo_ok si es menor a la cantidad tolerable
        return True
