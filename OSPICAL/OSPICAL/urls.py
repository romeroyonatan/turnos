from django.conf.urls import patterns
from django.views.generic import RedirectView
from django.contrib.auth.views import login, logout

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('turnos.views',
    (r'^$', RedirectView.as_view(url='/reservar/')),
    (r'^reservar/$', 'reservar'),
    (r'^json/afiliado/(?P<parametro>(id|numero|dni))/(?P<valor>\w+)/$', 'getAfiliado'),
    (r'^json/afiliado/id/(?P<afiliado_id>\w+)/telefono/$', 'getTelefono'),
    (r'^json/presentismo/(?P<afiliado_id>\w+)/$', 'verificarPresentismo'),
    (r'^json/especialistas/especialidad/(?P<especialidad_id>\d+)/$', 'getEspecialistas'),
    (r'^json/turnos/(?P<especialista_id>\d+)/$', 'getDiaTurnos'),
    (r'^json/turnos/(?P<especialista_id>\d+)/(?P<year>\d{4})/(?P<month>\d{1,2})/(?P<day>\d{1,2})/$', 'getTurnosDisponibles'),
    (r'^accounts/login/$',  login),
    (r'^accounts/logout/$', logout),
    (r'^accounts/register/$', 'register'),
)
