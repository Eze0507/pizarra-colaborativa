// Interfaces para la carga inicial del diagrama (GET /api/modelado/proyectos/:id/diagrama/)

export interface AtributoDiagrama {
  id: number;
  nombre: string;
  tipo: 'string' | 'integer' | 'long' | 'double' | 'boolean' | 'date';
  es_clave: boolean;
  es_nulo: boolean;
  orden: number;
}

export interface EntidadDiagrama {
  id: number;
  nombre: string;
  estado: 'activo' | 'bloqueado' | 'papelera';
  coord_x: number;
  coord_y: number;
  ancho: number;
  es_intermedia?: boolean;
  atributos: AtributoDiagrama[];
}

export interface RelacionDiagrama {
  id: number;
  nombre_relacion: string;
  tipo: 'asociacion' | 'agregacion' | 'composicion' | 'herencia';
  entidad_origen_id: number;
  entidad_destino_id: number;
  cardinalidad_origen: string;
  cardinalidad_destino: string;
  clase_asociacion_id?: number | null;
  puerto_origen?: string;
  puerto_destino?: string;
  vertices?: { x: number; y: number }[];
  origen_bloqueado?: boolean;
}

export interface ProyectoDiagrama {
  id: number;
  codigo: string;
  nombre: string;
  descripcion: string;
  paquete_base: string;
  datos_diagrama: Record<string, unknown> | null;
  propietario: string;
  es_propietario: boolean;
  rol_usuario: string;
  fecha_actualizacion: string;
}

export interface DiagramaCargaInicial {
  proyecto: ProyectoDiagrama;
  entidades: EntidadDiagrama[];
  relaciones: RelacionDiagrama[];
}

export interface UsuarioConectado {
  usuario_id: number;
  username: string;
  first_name?: string;
  email?: string;
  colorAvatar?: string;
}

// ── Mensajes WebSocket ──────────────────────────────────────────────────────

export type AccionWS =
  | 'mover_entidad'
  | 'entidad_movida'
  | 'cursor_posicion'
  | 'cursor_movido'
  | 'bloquear_entidad'
  | 'desbloquear_entidad'
  | 'guardar_snapshot'
  | 'usuarios_conectados'
  | 'colaborador_unido'
  | 'colaborador_salido'
  | 'entidad_bloqueada'
  | 'entidad_desbloqueada'
  | 'crear_entidad'
  | 'entidad_creada'
  | 'actualizar_entidad'
  | 'entidad_actualizada'
  | 'eliminar_entidad'
  | 'entidad_eliminada'
  | 'crear_relacion'
  | 'relacion_creada'
  | 'actualizar_relacion'
  | 'relacion_actualizada'
  | 'eliminar_relacion'
  | 'relacion_eliminada'
  | 'renombrar_proyecto'
  | 'proyecto_renombrado'
  | 'snapshot_guardado';

export interface MensajeWS {
  accion?: AccionWS;
  evento?: AccionWS;
  entidad_id?: number;
  relacion_id?: number;
  proyecto_id?: number;
  nombre?: string;
  x?: number;
  y?: number;
  coord_x?: number;
  coord_y?: number;
  usuario_id?: number;
  usuario_nombre?: string;
  username?: string;
  first_name?: string;
  email?: string;
  usuarios?: UsuarioConectado[];
  motivo?: string;
  entidad?: EntidadDiagrama;
  relacion?: RelacionDiagrama;
  data?: Record<string, unknown>;
  datos_diagrama?: Record<string, unknown>;
  id_map?: Record<string, number>;
  rel_id_map?: Record<string, number>;
  exito?: boolean;
  bloqueado_por?: {
    usuario_id: number;
    username: string;
  };
}

// Estado de la conexion WebSocket
export type EstadoConexion = 'conectando' | 'conectado' | 'desconectado' | 'error';
