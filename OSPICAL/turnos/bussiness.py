import datetime
from turnos.models import Turno, Afiliado, Especialista

class Bussiness():
    
    def getAfiliados(self, parametro, valor):
        # Buscar en la base de datos local
        filtro = dict([(parametro, valor)])
        queryset = Afiliado.objects.filter(**filtro)
        data = [item for item in queryset.values()]
        if not data:
            # TODO Buscar en la interfaz de consulta de afiliados
            pass
        return data
    
    def getTurnosDisponibles(self, especialista, fecha):
        disponibles = self.buscarTurnosDisponibles(especialista, fecha)
        if not disponibles and not self.haySobreturnos(especialista, fecha):
            disponibles=self.crearSobreturnos()
        return disponibles
    
    def buscarTurnosDisponibles(self, especialista, fecha):
        queryset = Turno.objects.filter(ee__especialista=especialista, 
                                        fecha__year=fecha.year,
                                        fecha__month=fecha.month,
                                        fecha__day=fecha.day,
                                        estado=Turno.DISPONIBLE,
                                        )
        return [item for item in queryset.values()]
    
    def haySobreturnos(self, especialista, fecha):
        queryset = Turno.objects.filter(ee__especialista=especialista, 
                                        fecha__year=fecha.year,
                                        fecha__month=fecha.month,
                                        fecha__day=fecha.day,
                                        sobreturno=True,
                                        )
        return queryset.count() > 0
    
    def crearSobreturnos(self):
        # TODO Crear sobreturnos
        return {}
    
    def getDiaTurnos(self, especialista):
        """Devuelve una lista de dias y el estado (Completo, Sobreturno)"""
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
    
    def verificarPresentismo(request, afiliado_id):
        # Contar cantidad de veces ausente en el plazo configurado
        # presentismo_ok si es menor a la cantidad tolerable
        return True
