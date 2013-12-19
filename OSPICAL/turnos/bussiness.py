import logging
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from turnos.models import *

# Get an instance of a logger
logger = logging.getLogger(__name__)

class Bussiness():
    def __init__(self):
        s = getattr(settings, 'TURNOS', {})
        self.AUSENTES_CANTIDAD = s.get('ausente_cantidad', 6)
        self.AUSENTES_MESES = s.get('ausente_meses', 6)
    
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
                                        fecha__gte=timezone.now()).datetimes('fecha', 'day')
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
    
    @transaction.atomic
    def reservarTurnos(self, afiliado, telefono, turnos, empleado=None):
        """ Reserva turnos a afiliado"""
        # TODO: Verificar excepciones
        logger.debug("Reservando turnos - afiliado:%s, telefono:%s, turnos:%s" % (afiliado, telefono, turnos))
        if turnos:
            reserva = self.__crearReserva(afiliado, telefono)
            logger.debug("Reserva id:%s" % reserva.id)
            for turno_id in turnos:
                turno = self.__reservarTurno(reserva, turno_id, empleado);
                lr = LineaDeReserva.objects.create(turno=turno,
                                                   reserva=reserva,
                                                   estado=Turno.RESERVADO)
                logger.debug("Linea de reserva id:%s" % lr.id)
            return reserva
        else:
            logger.warning("La lista de turnos a reservar esta vacia")
        return None
    
    def __crearReserva(self, afiliado, telefono):
        if not Afiliado.objects.filter(id=afiliado).exists():
            self.__lanzar(AfiliadoNotExistsException, "Afiliado ID '%s' inexistente" % afiliado)
        reserva = Reserva()
        reserva.afiliado = Afiliado.objects.get(id=afiliado)
        reserva.telefono = telefono
        reserva.fecha = timezone.now()
        reserva.save()
        return reserva
    
    def __reservarTurno(self, reserva, turno_id, empleado):
        logger.info("Reservando turno %s" % turno_id)
        if not Turno.objects.filter(id=turno_id).exists():
            self.__lanzar(TurnoNotExistsException, "Turno ID '%s' inexistente" % turno_id)
        turno = Turno.objects.get(id=turno_id)
        if turno.estado == Turno.RESERVADO:
            self.__lanzar(TurnoReservadoException, "Turno ID '%s' ya se encuentra reservado" % turno_id)
        historial = HistorialTurno.objects.create(fecha=timezone.now(),
                                   estadoAnterior=turno.estado,
                                   estadoNuevo=Turno.RESERVADO,
                                   turno=turno,
                                   empleado=empleado,
                                   descripcion="ID de reserva %s" % reserva.id)
        turno.estado = Turno.RESERVADO
        turno.save()
        logger.debug("Modificacion de turno: %s" % historial)
        return turno
        
    def verificarPresentismo(self, afiliado_id):
        """ Verifica si un afiliado se ausenta concurrentemente a los turnos"""
        fecha = timezone.now() + relativedelta(months=-1)
        queryset = LineaDeReserva.objects.filter(reserva__fecha__gte=fecha,
                                                 reserva__afiliado__id=afiliado_id,
                                                 estado=Turno.AUSENTE)
        return queryset.count() > self.AUSENTES_CANTIDAD
    
    def __lanzar(self, excepcion, mensaje):
        """Lanza una excepcion y loguea la misma"""
        e = excepcion(mensaje)
        logger.error(e)
        raise e
        
class TurnoNotExistsException(Exception):
    def __init__(self, mensaje=None):
        self.mensaje = mensaje
    def __str__(self):
        return self.mensaje

class AfiliadoNotExistsException(Exception):
    def __init__(self, mensaje=None):
        self.mensaje = mensaje
    def __str__(self):
        return self.mensaje

class TurnoReservadoException(Exception):
    def __init__(self, mensaje=None):
        self.mensaje = mensaje
    def __str__(self):
        return self.mensaje