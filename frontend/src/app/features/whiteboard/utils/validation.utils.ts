import { HallazgoValidacion } from '../interfaces/validation.interface';
import { EstadoConexion } from '../interfaces/diagrama.interface';

export function puedeValidarModelo(
  proyectoId: number | undefined,
  conexion: EstadoConexion,
  guardado: 'guardado' | 'guardando' | 'error',
  validando: boolean
): boolean {
  return !!proyectoId && conexion === 'conectado' && guardado === 'guardado' && !validando;
}

export function objetivoVisible(hallazgo: HallazgoValidacion): { tipo: 'clasificador' | 'relacion'; id: number } | null {
  if (hallazgo.objetivo.tipo === 'relacion') {
    return { tipo: 'relacion', id: hallazgo.objetivo.id };
  }
  if (hallazgo.objetivo.tipo === 'clasificador') {
    return { tipo: 'clasificador', id: hallazgo.objetivo.id };
  }
  if (hallazgo.objetivo.clasificador_id) {
    return { tipo: 'clasificador', id: hallazgo.objetivo.clasificador_id };
  }
  return null;
}
