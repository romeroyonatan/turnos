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
    
def verificarPresentismo(request, afiliado_id):
    # Contar cantidad de veces ausente en el plazo configurado
    # presentismo_ok si es menor a la cantidad tolerable
    return True