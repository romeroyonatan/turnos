# coding=utf-8
import datetime
import json
import inspect
from time import mktime

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.forms.models import model_to_dict
from django.contrib import messages
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render
from django.utils import timezone

from turnos.forms import ReservarTurnoForm, CrearTurnoForm
from turnos.models import *
from turnos.bussiness import Bussiness
import logging

logger = logging.getLogger(__name__)

class MyEncoder(json.JSONEncoder):
    ### Uso este encoder para codficar la fecha a JSON ###
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return int(mktime(obj.timetuple()))
        return json.JSONEncoder.default(self, obj)

def JSONResponse(response):
    return HttpResponse(json.dumps(response, cls=MyEncoder), content_type="application/json")

@login_required
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
    return render_to_response('turno/reserva.html',
                              locals(),
                              context_instance=RequestContext(request))

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
    logger.error("Ocurrio una excepcion en la vista '%s': %s - %s" % (inspect.stack()[1][3],
                                                                    exception.__class__.__name__,
                                                                    exception.message))
    return exception.message

@login_required
def get(request, model, parametro, valor):
    filtro = dict([(parametro, valor)])
    queryset = model.objects.filter(**filtro)
    data = [item for item in queryset.values()]
    return JSONResponse(data)

@login_required
def getAfiliado(request, parametro, valor):
    bussiness = Bussiness()
    data = bussiness.getAfiliados(parametro, valor)
    return JSONResponse(data)

@login_required
def getDiaTurnos(request, especialista_id):
    bussiness = Bussiness()
    data = bussiness.getDiaTurnos(especialista_id)
    return JSONResponse(data)    

@login_required
def getEspecialistas(request, especialidad_id):
    queryset = EspecialistaEspecialidad.objects.filter(especialidad__id=especialidad_id)
    data = [model_to_dict(item.especialista) for item in queryset]
    return JSONResponse(data)

@login_required
def getTurnosDisponibles(request, especialista_id, year, month, day):
    bussiness = Bussiness()
    fecha = datetime.datetime(int(year), int(month), int(day))
    data = bussiness.getTurnosDisponibles(especialista_id, fecha)
    return JSONResponse(data)

@login_required
def verificarPresentismo(request, afiliado_id):
    bussiness = Bussiness()
    data = {'presentismo_ok': bussiness.presentismoOK(afiliado_id)}
    return JSONResponse(data)

@login_required
def getTelefono(request, afiliado_id):
    queryset = Reserva.objects.filter(afiliado__id=afiliado_id).order_by('-fecha')[:1]
    data = [item["telefono"] for item in queryset.values('telefono')]
    return JSONResponse(data)

@login_required
def register(request):
    # TODO: Verificar permisos de crear usuarios
    # TODO: Falta agregar el dni, nombre, apellido, email, etc
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            logger.info("Creando cuenta del usuario %s" % form.cleaned_data['username'])
            form.save()
            return HttpResponseRedirect("/")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {'form': form})

@login_required
def crear_turnos(request):
    # TODO: Verificar permisos de crear turnos
    # TODO: Mostrar el ultimo turno creado y el historial de creaciones de turno
    b = Bussiness()
    if request.method == 'POST':
        form = CrearTurnoForm(request.POST)
        if form.is_valid():
            logger.info("<%s> esta creando turnos" % request.user.username)
            creados = b.crear_turnos(form.cleaned_data['dias'])
            if creados:
                messages.success(request, u'Turnos creados con éxito: %s' % creados)
            else:
                messages.warning(request, u'No se creó ningún turno, puede que ya se crearon con anterioridad')
            return HttpResponseRedirect("/crear/")
    else:
        form = CrearTurnoForm(initial={'dias':b.DIAS,
                                       'hasta':(timezone.now()+datetime.timedelta(days=b.DIAS)).strftime("%d-%m-%Y"),
                                       'frecuencia':b.MINUTOS,})
        last = Turno.objects.order_by('fecha').last()
        historial = b.get_historial_creacion_turnos()
    return render(request, "turno/creacion.html", locals())