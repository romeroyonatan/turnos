from django.conf.urls import patterns, include, url
from turnos.views import current_datetime, hours_ahead, reservar;

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^reservar/$', reservar),
    (r'^afiliado/dni/(\d{1,2})$', hours_ahead),
    (r'^afiliado/nro/(\d{1,2})$', hours_ahead),
    (r'^especialistas/especialidad$', hours_ahead),
    (r'^turnos/especialista/$', hours_ahead),
    (r'^horarios/dia/$', current_datetime),
)
