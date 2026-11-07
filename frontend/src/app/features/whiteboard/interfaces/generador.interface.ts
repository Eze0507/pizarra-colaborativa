export interface MetricasImportacionXML {
  entidades_creadas: number;
  atributos_creados: number;
  relaciones_creadas: number;
  entidades_persistentes?: number;
  claves_explicitamente_importadas?: number;
  claves_preservadas?: number;
  claves_id_inferidas?: number;
  entidades_no_elegibles_persistencia?: number;
  clasificadores_duplicados_omitidos?: number;
}

export interface RespuestaImportacionXML {
  detail: string;
  metricas: MetricasImportacionXML;
  revision: number;
}

export interface SolicitudImportacionXML {
  archivo_xml?: File;
  contenido_xml?: string;
  reemplazar_existente?: boolean;
  expected_revision: number;
}

export interface OpcionesGeneracionSpring {
  modelo: boolean;
  repositorio: boolean;
  servicio: boolean;
  controlador: boolean;
}

export interface SolicitudGeneracionSpring {
  expected_revision: number;
  nombre_proyecto: string;
  paquete_base: string;
  opciones: OpcionesGeneracionSpring;
}

export interface ErrorGeneracionSpring {
  code: string;
  message: string;
  details?: unknown;
  status?: number;
  current_revision?: number;
}

export interface DescargaSpringPreparada {
  blob: Blob;
  filename: string;
}
