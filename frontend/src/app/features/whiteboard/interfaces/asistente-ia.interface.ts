import { EntidadDiagrama, RelacionDiagrama, AtributoDiagrama } from './diagrama.interface';

export interface AtributoIARespuesta {
  id?: number;
  nombre: string;
  tipo?: string;
  es_clave?: boolean;
  es_nulo?: boolean;
  orden?: number;
}

export interface EntidadIARespuesta {
  id: number;
  nombre: string;
  pos_x?: number;
  pos_y?: number;
  es_intermedia?: boolean;
  atributos?: AtributoIARespuesta[];
}

export interface RelacionIARespuesta {
  id?: number;
  nombre_relacion?: string;
  tipo?: string;
  entidad_origen_id: number;
  entidad_destino_id: number;
  cardinalidad_origen?: string;
  cardinalidad_destino?: string;
  clase_asociacion_id?: number | null;
}

export interface DiagramaIARespuesta {
  entidades: EntidadIARespuesta[];
  relaciones: RelacionIARespuesta[];
  total_entidades?: number;
  total_relaciones?: number;
  error?: string;
}

export interface DiagramaGeneradoPayload {
  entidades: EntidadDiagrama[];
  relaciones: RelacionDiagrama[];
}

export interface MensajeChatIA {
  id: string;
  remitente: 'usuario' | 'asistente';
  texto: string;
  fecha: Date;
  cargando?: boolean;
}

export interface ContextoAtributoMinimoIA {
  nombre: string;
  tipo: string;
  es_clave: boolean;
  es_nulo?: boolean;
}

export interface ContextoEntidadMinimoIA {
  id: number;
  nombre: string;
  estado?: string;
  atributos: ContextoAtributoMinimoIA[];
}

export interface ContextoRelacionMinimoIA {
  id: number;
  entidad_origen_id: number;
  entidad_destino_id: number;
  tipo: string;
  nombre_relacion?: string;
}

export interface ContextoDiagramaIA {
  entidades: ContextoEntidadMinimoIA[];
  relaciones: ContextoRelacionMinimoIA[];
}

export interface EntidadACrearIA {
  nombre: string;
  es_intermedia?: boolean;
  atributos?: AtributoIARespuesta[];
}

export interface AtributoAModificarIA {
  nombre_original?: string;
  nombre: string;
  tipo?: string;
  es_clave?: boolean;
  es_nulo?: boolean;
}

export interface EntidadAModificarIA {
  entidad_id: number | string;
  entidad_nombre?: string;
  nuevo_nombre?: string | null;
  atributos_nuevos?: AtributoIARespuesta[];
  atributos_a_modificar?: AtributoAModificarIA[];
  atributos_a_eliminar?: string[];
}

export interface RelacionACrearIA {
  nombre_relacion?: string;
  tipo?: 'asociacion' | 'agregacion' | 'composicion' | 'herencia' | 'clase_asociacion';
  entidad_origen_id?: number | string | null;
  entidad_destino_id?: number | string | null;
  entidad_origen_nombre?: string | null;
  entidad_destino_nombre?: string | null;
  cardinalidad_origen?: string;
  cardinalidad_destino?: string;
  clase_asociacion_nombre?: string | null;
  clase_asociacion_id?: number | null;
}

export interface DeltaInstruccionIARespuesta {
  mensaje: string;
  entidades_a_crear: EntidadACrearIA[];
  entidades_a_modificar: EntidadAModificarIA[];
  entidades_a_eliminar: number[];
  relaciones_a_crear: RelacionACrearIA[];
  relaciones_a_eliminar: number[];
}

// ── Interfaces para Agente Senior Colaborativo (CU Interactuar con Agente Senior) ──

export type EstadoMensajeAgenteSenior = 'respondido' | 'procesando' | 'en_cola' | 'error';

export type RolMensajeAgenteSenior = 'USER' | 'AGENT';

export interface UsuarioMensajeAgenteSenior {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  nombre_completo: string;
}

export interface MensajeAgenteSenior {
  id: number;
  conversacion_id: number;
  fecha_envio: string;
  estado: EstadoMensajeAgenteSenior;
  rol: RolMensajeAgenteSenior;
  contenido: string;
  pregunta_id: number | null;
  usuario: UsuarioMensajeAgenteSenior | null;
  posicion_cola: number | null;
}

export interface EstadoColaAgenteSenior {
  procesando: boolean;
  mensaje_procesando_id: number | null;
  usuario_procesando: string | null;
  en_cola_count: number;
  max_en_cola: number;
  cola_llena: boolean;
  posiciones_cola: Record<string, number>;
}

export interface HistorialAgenteSeniorRespuesta {
  proyecto_id: number;
  proyecto_nombre: string;
  rol_usuario_actual: string;
  conversacion_id: number | null;
  fecha_creacion: string | null;
  mensajes: MensajeAgenteSenior[];
  estado_cola: EstadoColaAgenteSenior;
  max_caracteres: number;
}

export interface EnviarConsultaAgenteSeniorRespuesta {
  conversacion_id: number;
  mensaje: MensajeAgenteSenior;
  estado_cola: EstadoColaAgenteSenior;
}

export interface EventoWSAgenteSenior {
  proyecto_id?: number;
  conversacion_id?: number;
  mensaje?: MensajeAgenteSenior;
  pregunta?: MensajeAgenteSenior;
  respuesta?: MensajeAgenteSenior;
  siguiente_procesando?: MensajeAgenteSenior | null;
  pregunta_descartada_id?: number;
  contenido_original?: string;
  usuario_id?: number;
  username?: string;
  estado?: EstadoMensajeAgenteSenior;
  mensaje_error?: string;
  estado_cola?: EstadoColaAgenteSenior;
}

