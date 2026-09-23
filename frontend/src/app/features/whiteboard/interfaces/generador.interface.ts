export interface MetricasImportacionXML {
  entidades_creadas: number;
  atributos_creados: number;
  relaciones_creadas: number;
}

export interface RespuestaImportacionXML {
  detail: string;
  metricas: MetricasImportacionXML;
}

export interface SolicitudImportacionXML {
  archivo_xml?: File;
  contenido_xml?: string;
  reemplazar_existente?: boolean;
}
