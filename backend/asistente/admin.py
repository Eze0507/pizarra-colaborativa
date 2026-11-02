from django.contrib import admin
from .models import Conversacion, Mensaje


@admin.register(Conversacion)
class ConversacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'proyecto', 'fecha_creacion')
    search_fields = ('proyecto__nombre', 'proyecto__codigo')


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversacion', 'rol', 'estado', 'usuario', 'pregunta_id', 'fecha_envio')
    list_filter = ('rol', 'estado', 'fecha_envio')
    search_fields = ('contenido', 'usuario__username')
