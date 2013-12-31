# coding=utf-8
# Create your views here.
import datetime
import json
from time import mktime

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.forms.models import model_to_dict
from django.contrib import messages
from django.template import RequestContext

from turnos.forms import ReservarTurnoForm
from turnos.models import *
from turnos.bussiness import Bussiness
import logging

logger = logging.getLogger(__name__)

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(mktime(obj.timetuple()))
        return json.JSONEncoder.default(self, obj)

def JSONResponse(response):
    return HttpResponse(json.dumps(response, cls=MyEncoder), content_type="application/json")

def reservar(request):
    if request.method == 'POST':
        form = ReservarTurnoForm(request.POST)
        if form.is_valid():
            p = __getParametrosReserva(form)
            bussiness = Bussiness()
            if not p['turnos']:
                messages.error(request, 'Debe ingresar al menos un turno a reservar')
            else:
                try:
                    reserva = bussiness.reservarTurnos(p['afiliado'], p['telefono'], p['turnos'])
                except Exception, e:
                    messages.error(request, __getExceptionMessage(e))
                else:
                    messages.success(request, u'Turno reservado con éxito')
                    return HttpResponseRedirect('/reservar/')
    else:
        form = ReservarTurnoForm()
    return render_to_response('ReservarTurno.html', locals(), context_instance=RequestContext(request))

def __getTurnos(form):
    turnos = form.cleaned_data['turnos']
    lista = []
    if turnos:
        lista = json.loads(turnos)
    if not lista:
        hora = form.cleaned_data['hora']
        lista = [hora] if hora else None
    return lista
    
def __getParametrosReserva(form):
    turnos = __getTurnos(form)
    afiliado = form.cleaned_data['afiliado']
    telefono = form.cleaned_data['telefono']
    return {'turnos':turnos, 'afiliado':afiliado, 'telefono':telefono}
    
def __getExceptionMessage(exception):
    return exception.message

def get(request, model, parametro, valor):
    filtro = dict([(parametro, valor)])
    queryset = model.objects.filter(**filtro)
    data = [item for item in queryset.values()]
    return JSONResponse(data)

def getAfiliado(request, parametro, valor):
    bussiness = Bussiness()
    data = bussiness.getAfiliados(parametro,valor)
    return JSONResponse(data)

def getDiaTurnos(request, especialista_id):
    bussiness = Bussiness()
    data = bussiness.getDiaTurnos(especialista_id)
    return JSONResponse(data)    

def getEspecialistas(request, especialidad_id):
    queryset = EspecialistaEspecialidad.objects.filter(especialidad__id=especialidad_id)
    data = [model_to_dict(item.especialista) for item in queryset]
    return JSONResponse(data)

def getTurnosDisponibles(request, especialista_id, year, month, day):
    bussiness = Bussiness()
    fecha = datetime.datetime(int(year), int(month), int(day))
    data = bussiness.getTurnosDisponibles(especialista_id, fecha)
    return JSONResponse(data)

def verificarPresentismo(request, afiliado_id):
    bussiness = Bussiness()
    data = {'presentismo_ok': bussiness.presentismoOK(afiliado_id)}
    return JSONResponse(data)

def getTelefono(request, afiliado_id):
    queryset = Reserva.objects.filter(afiliado__id=afiliado_id).order_by('-fecha')[:1]
    data = [item["telefono"] for item in queryset.values('telefono')]
    return JSONResponse(data)