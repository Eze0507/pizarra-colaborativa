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
