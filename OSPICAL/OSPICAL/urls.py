from django.conf.urls import patterns, include, url
from turnos.models import Afiliado, Especialista

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('turnos.views',
    (r'^reservar/$', 'reservar'),
    (r'^json/afiliado/(?P<parametro>(id|numero|dni))/(?P<valor>\w+)$', 'get', {'model':Afiliado}),
    (r'^json/afiliado/id/(?P<afiliado_id>\w+)/telefono$', 'getTelefono'),
    (r'^json/presentismo/(?P<afiliado_id>\w+)$', 'verificarPresentismo'),
    (r'^json/especialistas/(?P<parametro>\w+)/(?P<valor>\w+)$', 'get', {'model':Especialista}),
    (r'^json/turnos/(?P<especialista_id>\d+)$', 'getDiaTurnos'),
    (r'^json/turnos/(?P<especialista_id>\d+)/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/$', 'getTurnosDisponibles'),
)
