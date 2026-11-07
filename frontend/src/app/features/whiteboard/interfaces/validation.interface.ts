export type PerfilValidacion = 'uml' | 'java' | 'jpa';
export type SeveridadHallazgo = 'error' | 'warning' | 'info';

export interface ObjetivoHallazgo {
  tipo: 'proyecto' | 'clasificador' | 'atributo' | 'operacion' | 'parametro' | 'relacion';
  id: number;
  clasificador_id?: number;
  operacion_id?: number;
}

export interface HallazgoValidacion {
  codigo: string;
  severidad: SeveridadHallazgo;
  mensaje: string;
  objetivo: ObjetivoHallazgo;
  campo?: string;
}

export interface ResultadoValidacion {
  origen: 'orm';
  proyecto_id: number;
  fecha_actualizacion: string | null;
  perfil: PerfilValidacion;
  valido: boolean;
  resumen: {
    errores: number;
    advertencias: number;
    informativos: number;
  };
  hallazgos: HallazgoValidacion[];
}
