# coding=utf-8
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
import logging

# Definicion de señales
logger = logging.getLogger(__name__)

def log_login(sender, request, user, **kwargs):
    logger.info("<%s> ha iniciado sesion desde <%s>" % (user.username,request.get_host()))
def log_logout(sender, request, user, **kwargs):
    logger.info("<%s> ha cerrado sesion correctamente" % user.username)
def log_failed(sender, credentials, **kwargs):
    print sender, credentials, kwargs 
    logger.error("<%s> fallo al iniciar sesion" % (credentials['username']))   

user_logged_in.connect(log_login)
user_logged_out.connect(log_logout)
user_login_failed.connect(log_failed)