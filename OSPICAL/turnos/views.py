# Create your views here.
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from turnos.forms import ReservarTurnoForm
import datetime


def current_datetime(request):
    now = datetime.datetime.now()
    return render_to_response('current_datetime.html', {'ahora': now})

def hours_ahead(request, offset):
    offset = int(offset)
    dt = datetime.datetime.now() + datetime.timedelta(hours=offset)
    return render_to_response('hours_ahead.html',locals())

def reservar(request):
    if request.method == 'POST':
        form = ReservarTurnoForm(request.POST)
        if form.is_valid():
            return HttpResponseRedirect('/horarios/dia/')
        return HttpResponseRedirect('/horarios/dia/')
    else:
        form = ReservarTurnoForm()
    error="Para reservar un turno debe llenar este formulario"
    return render_to_response('ReservarTurno.html', locals())