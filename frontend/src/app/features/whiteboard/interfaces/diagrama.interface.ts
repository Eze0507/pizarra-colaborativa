// Contrato compartido por la carga REST, el snapshot y los eventos WebSocket.
export type TipoClasificador = 'clase' | 'entidad_persistente' | 'interfaz';
export type VisibilidadUML = 'public' | 'protected' | 'private' | 'package';
export type TipoRelacionDiagrama = 'asociacion' | 'agregacion' | 'composicion' | 'herencia' | 'implementacion';

export interface AtributoDiagrama {
  id: number; nombre: string; tipo: string; tipo_referencia_id?: number | null;
  visibilidad?: VisibilidadUML; es_estatico?: boolean; es_clave: boolean;
  es_nulo: boolean; valor_predeterminado?: string; orden: number;
}
export interface ParametroOperacionDiagrama {
  id: number; nombre: string; tipo: string; tipo_referencia_id?: number | null; orden: number;
}
export interface OperacionDiagrama {
  id: number; nombre: string; visibilidad: VisibilidadUML; tipo_retorno: string;
  retorno_referencia_id?: number | null; orden: number; es_estatico: boolean;
  es_abstracto: boolean; parametros: ParametroOperacionDiagrama[];
}
export interface EntidadDiagrama {
  id: number; nombre: string; estado: 'activo' | 'bloqueado' | 'papelera';
  coord_x: number; coord_y: number; ancho: number; es_intermedia?: boolean;
  tipo_clasificador?: TipoClasificador; abstracto?: boolean; pos_x?: number; pos_y?: number;
  atributos: AtributoDiagrama[]; operaciones?: OperacionDiagrama[];
}
export interface RelacionDiagrama {
  id: number; nombre_relacion: string; tipo: TipoRelacionDiagrama;
  entidad_origen_id: number; entidad_destino_id: number;
  cardinalidad_origen: string; cardinalidad_destino: string;
  clase_asociacion_id?: number | null; puerto_origen?: string; puerto_destino?: string;
  rol_origen?: string; rol_destino?: string; navegable_origen?: boolean; navegable_destino?: boolean;
  vertices?: { x: number; y: number }[]; origen_bloqueado?: boolean; destino_bloqueado?: boolean;
}
export interface ProyectoDiagrama {
  id: number; codigo: string; nombre: string; descripcion: string; paquete_base: string;
  datos_diagrama: Record<string, unknown> | null; propietario: string; es_propietario: boolean;
  rol_usuario: string; fecha_actualizacion: string; revision: number;
}
export interface DiagramaCargaInicial { proyecto: ProyectoDiagrama; entidades: EntidadDiagrama[]; relaciones: RelacionDiagrama[]; }
export interface UsuarioConectado { usuario_id: number; username: string; first_name?: string; email?: string; colorAvatar?: string; }
export interface MapasIdsSnapshot {
  id_map?: Record<string, number>; attr_id_map?: Record<string, number>;
  operation_id_map?: Record<string, number>; parameter_id_map?: Record<string, number>;
  rel_id_map?: Record<string, number>;
}
export type AccionWS =
  | 'mover_entidad' | 'entidad_movida' | 'cursor_posicion' | 'cursor_movido'
  | 'bloquear_entidad' | 'desbloquear_entidad' | 'guardar_snapshot'
  | 'usuarios_conectados' | 'colaborador_unido' | 'colaborador_salido'
  | 'entidad_bloqueada' | 'entidad_desbloqueada' | 'crear_entidad'
  | 'entidad_creada' | 'actualizar_entidad' | 'entidad_actualizada'
  | 'eliminar_entidad' | 'entidad_eliminada' | 'crear_relacion'
  | 'relacion_creada' | 'actualizar_relacion' | 'relacion_actualizada'
  | 'eliminar_relacion' | 'relacion_eliminada' | 'renombrar_proyecto'
  | 'proyecto_renombrado' | 'snapshot_guardado' | 'permiso_denegado'
  | 'comando_rechazado' | 'access.revoked' | 'diagram.updated'
  | 'agente_senior_mensaje_creado' | 'agente_senior_estado_actualizado'
  | 'agente_senior_respuesta' | 'agente_senior_error';
export interface MensajeWS extends MapasIdsSnapshot {
  accion?: AccionWS; evento?: AccionWS; entidad_id?: number; relacion_id?: number;
  proyecto_id?: number; nombre?: string; x?: number; y?: number; coord_x?: number; coord_y?: number;
  usuario_id?: number; usuario_nombre?: string; username?: string; first_name?: string; email?: string;
  usuarios?: UsuarioConectado[]; motivo?: string; entidad?: EntidadDiagrama; relacion?: RelacionDiagrama;
  data?: Record<string, unknown>; datos_diagrama?: Record<string, unknown>; exito?: boolean;
  revision?: number; expected_revision?: number; current_revision?: number;
  request_id?: string; codigo?: string; mensaje?: string;
  bloqueado_por?: { usuario_id: number; username: string };
}
export type EstadoConexion = 'conectando' | 'conectado' | 'desconectado' | 'error';
