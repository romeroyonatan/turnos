# coding=utf-8
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta, datetime
from django.utils import timezone
from django.db import transaction
from django.db.models import Count

from turnos.models import *

import logging
from models import EspecialistaEspecialidad, HistorialTurno
logger = logging.getLogger(__name__)

class Bussiness():
    """Esta clase encapsula toda la logica de negocios"""
    def __init__(self):
        self.AUSENTES_CANTIDAD = int(self.__getSetting('ausente_meses', 3))
        self.AUSENTES_MESES = int(self.__getSetting('ausente_meses', 6))
        self.MINUTOS = int(self.__getSetting('minutos_entre_turnos', 15))
        self.DIAS = int(self.__getSetting('cantidad_dias_crear_turnos', 7))
    
    def __getSetting(self, key, default_value=None):
        setting = Settings.objects.filter(key=key)
        return setting[0].value if setting else default_value
    
    def getAfiliados(self, parametro, valor):
        # Buscar en la base de datos local
        logger.info("Buscando afiliado %s %s" % (parametro, valor))
        filtro = dict([(parametro, valor)])
        queryset = Afiliado.objects.filter(**filtro)
        data = [item for item in queryset.values()]
        if not data:
            logger.warn("Afiliado %s %s no encontrado. Buscando en interfaz de usuarios" % (parametro, valor))
            # TODO: Buscar en la interfaz de consulta de afiliados
            pass
        logger.info("Resultado de busqueda de afiliado %s %s: %s" % (parametro, valor, data))
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
                                        fecha__gte=timezone.now()).datetimes('fecha', 'day')[:self.DIAS]
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
        filtro = {'ee__especialista__id':especialista,
                  'fecha__day':fecha.day,
                  'fecha__month':fecha.month,
                  'fecha__year':fecha.year,
                  'estado':Turno.DISPONIBLE,
                  }
        return filtro
    
    @transaction.atomic
    def reservarTurnos(self, afiliado, telefono, turnos, empleado=None):
        """ Reserva turnos a afiliado"""
        # TODO: Verificar excepciones
        logger.info("Reservando turnos - afiliado:%s, telefono:%s, turnos:%s" % (afiliado, telefono, turnos))
        if turnos:
            reserva = self.__crearReserva(afiliado, telefono)
            logger.info("Reserva id:%s" % reserva.id)
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
        reserva.save()
        return reserva
    
    def __reservarTurno(self, reserva, turno_id, empleado):
        logger.info("Reservando turno %s" % turno_id)
        if not Turno.objects.filter(id=turno_id).exists():
            self.__lanzar(TurnoNotExistsException, "Turno ID '%s' inexistente" % turno_id)
        turno = Turno.objects.get(id=turno_id)
        if turno.estado == Turno.RESERVADO:
            self.__lanzar(TurnoReservadoException, "Turno ID '%s' ya se encuentra reservado" % turno_id)
        if turno.fecha < (timezone.now()-timedelta(minutes=self.MINUTOS)):
            self.__lanzar(ReservaTurnoException, "No se pueden reservar turnos anteriores a la fecha actual")
        historial = HistorialTurno.objects.create(estadoAnterior=turno.estado,
                                   estadoNuevo=Turno.RESERVADO,
                                   turno=turno,
                                   empleado=empleado,
                                   descripcion="ID de reserva %s" % reserva.id)
        turno.estado = Turno.RESERVADO
        turno.save()
        logger.debug("Modificacion de turno: %s" % historial)
        return turno
    
    def contarFaltas(self, afiliado_id):
        fecha = timezone.now() + relativedelta(months=-self.AUSENTES_MESES)
        queryset = LineaDeReserva.objects.filter(reserva__fecha__gte=fecha,
                                                 reserva__afiliado__id=afiliado_id,
                                                 estado=Turno.AUSENTE)
        return queryset.count()
    
    def presentismoOK(self, afiliado_id):
        """ Verifica si un afiliado se ausenta concurrentemente a los turnos"""
        faltas = self.contarFaltas(afiliado_id);
        logger.debug("Cantidad de faltas del afiliado %s: %s, Presentismo_ok %s" % (afiliado_id, faltas, faltas <= self.AUSENTES_CANTIDAD))
        return faltas <= self.AUSENTES_CANTIDAD
    def __lanzar(self, excepcion, mensaje):
        """Lanza una excepcion y loguea la misma"""
        e = excepcion(mensaje)
        logger.error("%s - %s" % (excepcion.__name__, mensaje))
        raise e
    def crear_turnos(self, dias):
        cantidad = 0
        for ee in EspecialistaEspecialidad.objects.all():
            creados = self.crear_turnos_del_especialista(ee, dias)
            cantidad += len(creados)
        return cantidad
    def crear_turnos_del_especialista(self, especialista_especialidad, 
                                      cantidad_dias=None, 
                                      a_partir_de = timezone.now()):
        """Crea turnos para un especialista y una especialidad a partir del dia especificado"""
        logger.debug("Creando turnos para el especialista %s" % especialista_especialidad)
        cantidad_dias = self.DIAS if cantidad_dias == None else cantidad_dias
        turnos = list()
        disponibilidades = Disponibilidad.objects.filter(ee=especialista_especialidad)
        base = a_partir_de = a_partir_de.date()
        aux = cantidad_dias
        today = date.today()
        while aux > 0:
            for disponibilidad in disponibilidades:
                dia = self.__proximoDia(int(disponibilidad.dia), base)
                diff = dia - today
                if diff.days <= cantidad_dias:
                    turnos += self.__crear_turnos_del_dia(disponibilidad, dia)
            # Avanzamos de semana
            aux -= 7
            base += timedelta(days=7)
        return self.__guardarTurnos(especialista_especialidad, turnos, a_partir_de) if turnos else []
    def __crear_turnos_del_dia(self, disponibilidad, dia):
        """Crea turnos para una disponibilidad de un especialista en un dia determinado"""
        logger.debug("Creando turnos para el dia <%s> para el especialista <%s>" % (dia, disponibilidad.ee))
        desde = datetime.combine(dia, disponibilidad.horaDesde)
        hasta = datetime.combine(dia, disponibilidad.horaHasta)
        turnos = []
        while desde < hasta:
            turnos.append(Turno(fecha=desde.replace(tzinfo=timezone.utc),
                                estado=Turno.DISPONIBLE,
                                sobreturno=False,
                                consultorio=disponibilidad.consultorio,
                                ee=disponibilidad.ee)
                          )
            desde += timedelta(minutes=self.MINUTOS)
        return turnos
    def __proximoDia(self, dia, desde = timezone.now().date()):
        """Obtiene el proximo dia de la semana a partir de otro dia"""
        days_ahead = dia - desde.weekday()
        if days_ahead < 0: # El dia ya paso en esta semana
            days_ahead += 7
        return desde + timedelta(days=days_ahead)
    @transaction.commit_manually
    def __guardarTurnos(self, ee, turnos, a_partir_de):
        """Guarda los turnos creados en la base de datos cuidando que no se guarden repetidos"""
        # Hago este lio para evitar el mensaje de warning por ser un datetime sin timezone
        fecha = datetime.combine(a_partir_de, datetime.min.time().replace(tzinfo=timezone.utc))
        existentes = Turno.objects.filter(ee=ee, fecha__gte = fecha)
        lista = filter(lambda turno: turno not in existentes, turnos)
        logger.debug("Guardando %s turnos del especialista <%s>"%(len(lista), ee))
        #XXX: Lo hago asi, para obtener los ID de turnos, es necesario para crear los historiales
        for turno in lista:
            turno.save()
        transaction.commit(); #Asi es mas rapido
        self.__crear_historial_turnos(lista)
        return lista
    
    def __crear_historial_turnos(self, turnos):
        """Crea los historiales de cada turno nuevo"""
        logger.debug("Creando historial de turnos")
        lista = list()
        for turno in turnos:
            #TODO tener en cuenta el empleado que hace la operacion
            lista.append(HistorialTurno(estadoNuevo=Turno.DISPONIBLE,
                                        descripcion="Creación de turno",
                                        turno=turno,
                                        empleado=None,))
        return HistorialTurno.objects.bulk_create(lista)
        
    def get_historial_creacion_turnos(self):
        """Obtiene el detalle de las ultimas creaciones de turnos"""
        logger.debug("Obteniendo historial de creacion de turnos")
        eventos = HistorialTurno.objects.extra(select={'fecha':'date( fecha )'})
        eventos = eventos.values('fecha','empleado').annotate(cantidad=Count('fecha'))
        lista = list()
        for evento in eventos:
            lista.append({'dia':evento['fecha'],
                          'responsable':evento['empleado'] if evento['empleado'] else 'Proceso automático',
                          'cantidad': evento['cantidad']})
        logger.debug("lista: %s" %lista)
        return lista
        
class ReservaTurnoException(Exception):
    def __init__(self, message=None):
        self.message = message
    def __str__(self):
        return self.message   
class TurnoNotExistsException(ReservaTurnoException):
    def __init__(self, message=None):
        self.message = message
class AfiliadoNotExistsException(ReservaTurnoException):
    def __init__(self, message=None):
        self.message = message
class TurnoReservadoException(ReservaTurnoException):
    def __init__(self, message=None):
        self.message = message