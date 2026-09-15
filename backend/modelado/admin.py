from django.contrib import admin
from .models import Proyecto, Entidad, Atributo, Relacion


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'propietario', 'fecha_creacion', 'fecha_actualizacion')
    search_fields = ('codigo', 'nombre', 'propietario__username')


@admin.register(Entidad)
class EntidadAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'proyecto', 'estado', 'coord_x', 'coord_y', 'ancho')
    list_filter = ('estado', 'proyecto')
    search_fields = ('nombre', 'proyecto__nombre')


@admin.register(Atributo)
class AtributoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'entidad', 'tipo', 'es_clave', 'es_nulo', 'orden')
    list_filter = ('tipo', 'es_clave', 'es_nulo')
    search_fields = ('nombre', 'entidad__nombre')


@admin.register(Relacion)
class RelacionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'proyecto',
        'nombre_relacion',
        'tipo',
        'entidad_origen',
        'cardinalidad_origen',
        'entidad_destino',
        'cardinalidad_destino'
    )
    list_filter = ('tipo', 'proyecto')
    search_fields = ('nombre_relacion', 'entidad_origen__nombre', 'entidad_destino__nombre')

