import { AtributoDiagrama, RelacionDiagrama } from './diagrama.interface';

export interface TemaColores {
  lienzo: string;
  grid: string;
  entidadFondo: string;
  entidadBorde: string;
  headerFondo: string;
  headerBorde: string;
  headerTexto: string;
  bodyTexto: string;
  bloqueadoBorde: string;
}

export type TipoRelacionUML = RelacionDiagrama['tipo'] | 'clase_asociacion';

export interface OpcionRelacion {
  tipo: TipoRelacionUML;
  nombre: string;
  subtitulo: string;
  svgIcon: string;
}

export interface CardinalidadEditando {
  relacionId: number;
  extremo: 'origen' | 'destino';
  valorActual: string;
}

export interface CapsulaSeleccionada {
  relacionId: number;
  extremo: 'origen' | 'destino';
}

export interface PosicionEditor {
  x: number;
  y: number;
  w: number;
  h: number;
}

export type TipoEditor = 'nombre' | 'nuevo_atributo' | 'editar_atributo' | 'nombre_relacion';

export interface GuardarEditorPayload {
  valor: string;
  encadenar: boolean;
}
