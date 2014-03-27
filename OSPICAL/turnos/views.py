# coding=utf-8
import datetime
import json
import inspect
from time import mktime

from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.forms.models import model_to_dict
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from turnos.forms import *
from turnos.models import *
from turnos.bussiness import Bussiness
import logging

logger = logging.getLogger(__name__)

class MyEncoder(json.JSONEncoder):
    """Uso este encoder para codficar la fecha a JSON """
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            tz = timezone.get_default_timezone()
            fecha = obj.astimezone(tz)
            return int(mktime(fecha.timetuple()))
        return json.JSONEncoder.default(self, obj)

def JSONResponse(response):
    return HttpResponse(json.dumps(response, cls=MyEncoder), content_type="application/json; charset=utf-8")

@login_required
@permission_required('turnos.reservar_turnos', raise_exception=True)
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
                    reserva = bussiness.reservarTurnos(p['afiliado'], 
                                                       p['telefono'],
                                                       p['turnos'],
                                                       empleado=request.user.get_profile())
                except Exception, e:
                    messages.error(request, __getExceptionMessage(e))
                else:
                    messages.success(request, u'Turno reservado con éxito')
                    return HttpResponseRedirect(request.path)
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
    fecha = datetime.date(int(year), int(month), int(day))
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
@permission_required('auth.add_user')
def register(request):
    if request.method == 'POST':
        form = RegistrarUsuarioForm(request.POST)
        if form.is_valid():
            logger.info("Creando cuenta del usuario %s" % form.cleaned_data['username'])
            user = form.save()
            messages.success(request, 
                             u'La cuenta para el usuario <%s> ha sido creada con éxito' % user.username)
            return HttpResponseRedirect(request.path)
    else:
        form = RegistrarUsuarioForm()
    return render(request, "registration/register.html", {'form': form})

@login_required
@permission_required('turnos.crear_turnos', raise_exception=True)
def crear_turnos(request):
    b = Bussiness()
    if request.method == 'POST':
        form = CrearTurnoForm(request.POST)
        if form.is_valid():
            logger.info("<%s> esta creando turnos" % request.user.username)
            creados = b.crear_turnos(form.cleaned_data['dias'])
            if creados:
                messages.success(request, 
                                 u'%s Turnos creados con éxito' % creados)
            else:
                messages.warning(request, 
                                 u'No se creó ningún turno, puede que ya se \
                                 crearon con anterioridad')
            return HttpResponseRedirect(request.path)
    else:
        hasta = (timezone.now() + datetime.timedelta(days=b.DIAS-1)).strftime("%d-%m-%Y")
        last = Turno.objects.order_by('fecha').last()
        frecuencia = b.MINUTOS
        form = CrearTurnoForm(initial={'dias':b.DIAS})
        historial = b.get_historial_creacion_turnos()
    return render(request, "turno/creacion.html", locals())

@login_required
@permission_required('turnos.reservar_turnos', raise_exception=True)
def confirmar_reserva(request):
    b = Bussiness()
    if request.method == 'POST':
        form = ConfirmarTurnoForm(request.POST)
        if form.is_valid():
            reservas = form.cleaned_data["turnos"]
            if b.confirmar_reserva(reservas, request.user.get_profile()):
                messages.success(request, u'Reserva confirmada con éxito')
            return HttpResponseRedirect(request.path)
    else:
        form = ConfirmarTurnoForm()
    return render(request, "turno/confirmar.html", locals())

@login_required
def get_turnos_afiliado(request,afiliado_id,today=False):
    b = Bussiness()
    day = timezone.now() if today else None
    data = b.get_turnos_reservados(afiliado_id, day)
    return JSONResponse(data)

@login_required
@permission_required('turnos.reservar_turnos', raise_exception=True)
def cancelar_reserva(request):
    b = Bussiness()
    if request.method == 'POST':
        form = CancelarReservaForm(request.POST)
        if form.is_valid():
            reserva = form.cleaned_data["turnos"]
            motivo = form.cleaned_data["motivo"]
            if b.cancelar_reserva(reserva, motivo, request.user.get_profile()):
                messages.success(request, u'Reserva cancelada con éxito')
            return HttpResponseRedirect(request.path)
    else:
        form = CancelarReservaForm()
    return render(request, "turno/cancelar_reserva.html", locals())

@login_required
@permission_required('turnos.cancelar_turnos', raise_exception=True)
def cancelar_turnos(request):
    if request.method == 'POST':
        form = CancelarTurnoForm(request.POST)
        if form.is_valid():
            ee = EspecialistaEspecialidad.objects.filter(especialidad=form.cleaned_data["especialidad"],
                                                         especialista=form.cleaned_data["especialista"])
            if ee:
                ee = ee[0]
                b = Bussiness()
                fecha = datetime.date.fromtimestamp(form.cleaned_data["fecha"]/1000)
                cancelados = b.cancelar_turnos(ee.especialista.id, fecha)
                messages.success(request, u'%s turnos cancelados' % len(cancelados))
                return HttpResponseRedirect(request.path)
            else:
                messages.error(request, u'La combinacion de especialidad y especialista no coincide')
    else:
        form = CancelarTurnoForm()
    return render(request, "turno/cancelar_turnos.html", locals())

@login_required
def get_reservas_especialista(request, especialidad, especialista, year, month, day):
    b = Bussiness()
    ee = EspecialistaEspecialidad.objects.filter(especialidad=especialidad,
                                                 especialista=especialista)
    fecha = datetime.date(int(year), int(month), int(day))
    lineas = b.get_reserva_especialista(ee, fecha)
    data = [{"fecha_reserva": lr.reserva.fecha,
             "fecha_turno": lr.turno.fecha,
             "afiliado":lr.reserva.afiliado.full_name(),
             "numero": lr.reserva.afiliado.numero,
             "telefono": lr.reserva.telefono,
             } for lr in lineas]
    return JSONResponse(data)

@login_required
# @permission_required('turnos.registrar_especialista', raise_exception=True)
def registrar_especialista(request):
    b=Bussiness()
    if request.method == 'POST':
        form = RegistarEspecialistaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, u'La operación se realizó con éxito')
            return HttpResponseRedirect(request.path)
    else:
        form = RegistarEspecialistaForm(initial={'frecuencia':b.MINUTOS})
    return render(request, "especialista/registrar.html", locals())

@permission_required('turnos.consultar_reservas', raise_exception=True)
def consultar_reservas(request):
    b=Bussiness()
    if request.method == 'POST':
        form = ConsultarReservaForm(request.POST)
        if form.is_valid():
            mostrar_resultados=True
            resultado = b.consultar_reservas(especialidad=form.cleaned_data['especialidad'], 
                                             especialista=form.cleaned_data['especialista'], 
                                             afiliado=form.cleaned_data['afiliado'], 
                                             fecha=form.cleaned_data['fecha'])
    else:
        form = ConsultarReservaForm()
    return render(request, "turno/buscar.html", locals())