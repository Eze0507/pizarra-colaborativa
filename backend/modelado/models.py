import re
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError

# Expresión regular para cardinalidades / multiplicidades UML (ej. '1', '*', '0..1', '1..*', '0..*')
REGEX_CARDINALIDAD = r'^([0-9]+|\*|[0-9]+\.\.([0-9]+|\*))$'
validador_cardinalidad = RegexValidator(
    regex=REGEX_CARDINALIDAD,
    message="La cardinalidad debe tener un formato UML válido (ej. '1', '*', '0..1', '1..*', '0..*')."
)


class VisibilidadUML(models.TextChoices):
    PUBLIC = 'public', 'Public'
    PROTECTED = 'protected', 'Protected'
    PRIVATE = 'private', 'Private'
    PACKAGE = 'package', 'Package'


class DiagramHistoryOperation(models.Model):
    """Historia personal confirmada. Los estados UML nunca incluyen presencia o permisos."""
    class Status(models.TextChoices):
        APPLIED = 'aplicada', 'Aplicada'
        UNDONE = 'deshecha', 'Deshecha'
        INVALID = 'invalidada', 'Invalidada'

    id = models.BigAutoField(primary_key=True)  # orden lógico, independiente de la revisión del lote
    operation_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    project = models.ForeignKey('Proyecto', on_delete=models.CASCADE, related_name='history_operations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diagram_history')
    kind = models.CharField(max_length=40, default='edit')
    description = models.CharField(max_length=250)
    created_at = models.DateTimeField(auto_now_add=True)
    base_revision = models.PositiveBigIntegerField()
    confirmed_revision = models.PositiveBigIntegerField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.APPLIED)
    before = models.JSONField()
    after = models.JSONField()
    affected = models.JSONField(default=dict)
    request_id = models.CharField(max_length=100)
    batch_index = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['id']
        constraints = [models.UniqueConstraint(fields=['project', 'user', 'request_id', 'batch_index'], name='unique_history_batch_operation')]
        indexes = [models.Index(fields=['project', 'user', 'status', 'id'], name='history_owner_state_idx')]


class DiagramHistoryReceipt(models.Model):
    """Recibos durables independientes de la poda de las 50 operaciones restaurables."""
    project = models.ForeignKey('Proyecto', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request_id = models.CharField(max_length=100)
    fingerprint = models.CharField(max_length=64)
    result = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['project', 'user', 'request_id'], name='unique_history_request')]


class DiagramEditLock(models.Model):
    """Arrendamiento de edición vigente; jamás forma parte de un snapshot histórico."""
    project = models.ForeignKey('Proyecto', on_delete=models.CASCADE)
    entity_id = models.BigIntegerField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    connection = models.CharField(max_length=255)
    expires_at = models.DateTimeField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['project', 'entity_id'], name='unique_diagram_edit_lock')]


class Proyecto(models.Model):
    codigo = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Código identificador correlativo único (ej. PROJ-001)."
    )
    nombre = models.CharField(
        max_length=150,
        help_text="Nombre del proyecto de modelado."
    )
    descripcion = models.TextField(
        blank=True,
        default='',
        help_text="Descripción o propósito del proyecto."
    )
    paquete_base = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="Paquete base para la generación de código (ej. com.example.proyecto)."
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    datos_diagrama = models.JSONField(
        default=dict,
        blank=True,
        help_text="Snapshot del diagrama UML en formato JSON (posiciones, estado del lienzo y metadatos visuales)."
    )
    revision = models.PositiveBigIntegerField(
        default=0,
        help_text="Revisión monotónica del estado UML confirmado del proyecto.",
    )

    propietario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='proyectos_propios',
        help_text="Usuario creador y dueño del proyecto."
    )
    colaboradores = models.ManyToManyField(
        User,
        through='usuario.UserColaborador',
        related_name='proyectos_colaborando',
        blank=True,
        help_text="Colaboradores asignados al proyecto."
    )

    class Meta:
        db_table = 'proyecto'
        ordering = ['-fecha_creacion']
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'

    def save(self, *args, **kwargs):
        # 1. Generación automática del código correlativo PROJ-001, PROJ-002, etc.
        if not self.codigo:
            ultimo = Proyecto.objects.order_by('-id').first()
            if ultimo and ultimo.codigo and ultimo.codigo.startswith("PROJ-"):
                try:
                    num_parte = int(ultimo.codigo.replace("PROJ-", ""))
                    siguiente_num = num_parte + 1
                except ValueError:
                    siguiente_num = Proyecto.objects.count() + 1
            else:
                siguiente_num = 1

            candidato = f"PROJ-{siguiente_num:03d}"
            while Proyecto.objects.filter(codigo=candidato).exists():
                siguiente_num += 1
                candidato = f"PROJ-{siguiente_num:03d}"
            self.codigo = candidato

        # 2. Generación automática del paquete base si no fue provisto
        if not self.paquete_base:
            slug = re.sub(r'[^a-zA-Z0-9]+', '', self.nombre.lower()) or 'proyecto'
            self.paquete_base = f"com.example.{slug}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Entidad(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = 'activo', 'Activo'
        BLOQUEADO = 'bloqueado', 'Bloqueado'
        PAPELERA = 'papelera', 'Papelera'

    class TipoClasificador(models.TextChoices):
        CLASE = 'clase', 'Clase'
        ENTIDAD_PERSISTENTE = 'entidad_persistente', 'Entidad persistente'
        INTERFAZ = 'interfaz', 'Interfaz'

    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='entidades',
        help_text="Proyecto al que pertenece la entidad (agregación)."
    )
    nombre = models.CharField(
        max_length=150,
        help_text="Nombre conceptual de la entidad / clase."
    )
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.ACTIVO,
        help_text="Estado de la entidad (activo, bloqueado para exclusión mutua, papelera)."
    )
    coord_x = models.FloatField(
        default=0.0,
        help_text="Posición X en el lienzo virtual de la pizarra."
    )
    coord_y = models.FloatField(
        default=0.0,
        help_text="Posición Y en el lienzo virtual de la pizarra."
    )
    ancho = models.FloatField(
        default=200.0,
        help_text="Ancho de la entidad en el lienzo."
    )
    es_intermedia = models.BooleanField(
        default=False,
        help_text="Indica si la entidad es una tabla intermedia nacida a partir de una relación N:M (clase de asociación)."
    )
    tipo_clasificador = models.CharField(
        max_length=30,
        choices=TipoClasificador.choices,
        default=TipoClasificador.CLASE,
        help_text="Clasificación UML. Los registros históricos se interpretan como clases no persistentes."
    )
    abstracto = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'entidad'
        verbose_name = 'Entidad'
        verbose_name_plural = 'Entidades'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.proyecto.nombre})"


class Atributo(models.Model):
    class Tipo(models.TextChoices):
        STRING = 'string', 'String'
        INTEGER = 'integer', 'Integer'
        LONG = 'long', 'Long'
        DOUBLE = 'double', 'Double'
        BOOLEAN = 'boolean', 'Boolean'
        DATE = 'date', 'Date'

    entidad = models.ForeignKey(
        Entidad,
        on_delete=models.CASCADE,
        related_name='atributos',
        help_text="Entidad a la que pertenece el atributo (agregación)."
    )
    nombre = models.CharField(
        max_length=150,
        help_text="Nombre del atributo."
    )
    tipo = models.CharField(
        max_length=150,
        default=Tipo.STRING,
        help_text="Nombre de tipo simple conservado por compatibilidad."
    )
    tipo_referencia = models.ForeignKey(
        Entidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='atributos_que_referencian',
    )
    visibilidad = models.CharField(
        max_length=20,
        choices=VisibilidadUML.choices,
        default=VisibilidadUML.PRIVATE,
    )
    es_estatico = models.BooleanField(default=False)
    valor_predeterminado = models.CharField(max_length=255, blank=True, default='')
    es_clave = models.BooleanField(
        default=False,
        help_text="Indica si el atributo es clave primaria o identificador."
    )
    es_nulo = models.BooleanField(
        default=False,
        help_text="Indica si el atributo permite valores nulos."
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Posición u orden del atributo dentro de la entidad."
    )

    class Meta:
        db_table = 'atributo'
        ordering = ['orden', 'id']
        verbose_name = 'Atributo'
        verbose_name_plural = 'Atributos'

    def __str__(self):
        pk_indicator = " [PK]" if self.es_clave else ""
        return f"{self.nombre}: {self.tipo}{pk_indicator}"


class Operacion(models.Model):
    entidad = models.ForeignKey(Entidad, on_delete=models.CASCADE, related_name='operaciones')
    nombre = models.CharField(max_length=150)
    visibilidad = models.CharField(
        max_length=20,
        choices=VisibilidadUML.choices,
        default=VisibilidadUML.PUBLIC,
    )
    tipo_retorno = models.CharField(max_length=150, default='void')
    retorno_referencia = models.ForeignKey(
        Entidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operaciones_que_retornan',
    )
    orden = models.PositiveIntegerField(default=0)
    es_estatico = models.BooleanField(default=False)
    es_abstracto = models.BooleanField(default=False)

    class Meta:
        db_table = 'operacion'
        ordering = ['orden', 'id']
        verbose_name = 'Operación UML'
        verbose_name_plural = 'Operaciones UML'

    def __str__(self):
        return f"{self.nombre}(): {self.tipo_retorno}"


class ParametroOperacion(models.Model):
    operacion = models.ForeignKey(Operacion, on_delete=models.CASCADE, related_name='parametros')
    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=150, default='string')
    tipo_referencia = models.ForeignKey(
        Entidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='parametros_que_referencian',
    )
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'parametro_operacion'
        ordering = ['orden', 'id']
        verbose_name = 'Parámetro de operación'
        verbose_name_plural = 'Parámetros de operación'

    def __str__(self):
        return f"{self.nombre}: {self.tipo}"


class Relacion(models.Model):
    class Tipo(models.TextChoices):
        ASOCIACION = 'asociacion', 'Asociación'
        AGREGACION = 'agregacion', 'Agregación'
        COMPOSICION = 'composicion', 'Composición'
        HERENCIA = 'herencia', 'Herencia (Generalización)'
        IMPLEMENTACION = 'implementacion', 'Implementación de interfaz'

    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='relaciones',
        help_text="Proyecto al que pertenece la relación (agregación)."
    )
    entidad_origen = models.ForeignKey(
        Entidad,
        on_delete=models.CASCADE,
        related_name='relaciones_origen',
        help_text="Entidad origen de la relación."
    )
    entidad_destino = models.ForeignKey(
        Entidad,
        on_delete=models.CASCADE,
        related_name='relaciones_destino',
        help_text="Entidad destino de la relación."
    )
    clase_asociacion = models.ForeignKey(
        Entidad,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='relaciones_asociadas',
        help_text="Entidad intermedia vinculada si la relación es N:M o clase de asociación."
    )
    nombre_relacion = models.CharField(
        max_length=150,
        blank=True,
        default='',
        help_text="Nombre opcional de la relación o verbo de conexión."
    )
    tipo = models.CharField(
        max_length=30,
        choices=Tipo.choices,
        default=Tipo.ASOCIACION,
        help_text="Tipo de relación UML (asociacion, agregacion, composicion, herencia, implementacion)."
    )
    cardinalidad_origen = models.CharField(
        max_length=20,
        default='',
        blank=True,
        validators=[validador_cardinalidad],
        help_text="Multiplicidad o cardinalidad en la entidad de origen (ej. '1', '*', '0..1', '1..*')."
    )
    cardinalidad_destino = models.CharField(
        max_length=20,
        default='',
        blank=True,
        validators=[validador_cardinalidad],
        help_text="Multiplicidad o cardinalidad en la entidad de destino (ej. '1', '*', '0..1', '1..*')."
    )
    puerto_origen = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Identificador del puerto en la entidad de origen (ej. 'top-0', 'right-1')."
    )
    puerto_destino = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Identificador del puerto en la entidad de destino (ej. 'bottom-0', 'left-2')."
    )

    rol_origen = models.CharField(max_length=150, blank=True, default='')
    rol_destino = models.CharField(max_length=150, blank=True, default='')
    navegable_origen = models.BooleanField(default=False)
    navegable_destino = models.BooleanField(default=False)

    class Meta:
        db_table = 'relacion'
        verbose_name = 'Relación'
        verbose_name_plural = 'Relaciones'

    def clean(self):
        super().clean()
        if self.cardinalidad_origen and not re.match(REGEX_CARDINALIDAD, str(self.cardinalidad_origen).strip()):
            raise ValidationError({
                'cardinalidad_origen': f"Formato inválido para cardinalidad_origen: '{self.cardinalidad_origen}'. Debe cumplir con el formato: ^([0-9]+|\\*|[0-9]+\\.\\.([0-9]+|\\*))$"
            })
        if self.cardinalidad_destino and not re.match(REGEX_CARDINALIDAD, str(self.cardinalidad_destino).strip()):
            raise ValidationError({
                'cardinalidad_destino': f"Formato inválido para cardinalidad_destino: '{self.cardinalidad_destino}'. Debe cumplir con el formato: ^([0-9]+|\\*|[0-9]+\\.\\.([0-9]+|\\*))$"
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        desc = self.nombre_relacion or self.tipo
        return f"{self.entidad_origen.nombre} ({self.cardinalidad_origen}) -> {self.entidad_destino.nombre} ({self.cardinalidad_destino}) [{desc}]"
