from django.contrib import admin
from turnos.models import Especialidad, Consultorio, Settings, Empleado
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin


admin.site.register(Especialidad)
admin.site.register(Consultorio)
admin.site.register(Settings)

admin.site.unregister(User)
 
class UserProfileInline(admin.StackedInline):
    model = Empleado
 
class UserProfileAdmin(UserAdmin):
    inlines = [UserProfileInline]
 
admin.site.register(User, UserProfileAdmin)