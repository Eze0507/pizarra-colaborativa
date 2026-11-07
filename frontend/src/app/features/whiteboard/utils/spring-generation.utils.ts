import { EstadoConexion } from '../interfaces/diagrama.interface';


export interface EstadoGeneracionSpring {
  proyectoId: number | null;
  proyectoActivoId: number;
  rol: string;
  conexion: EstadoConexion;
  guardado: 'guardado' | 'guardando' | 'error';
  conflicto: boolean;
  generando: boolean;
}

export function puedeExportarSpring(rol: string): boolean {
  return ['propietario', 'editor', 'visualizador'].includes(rol);
}

export function normalizarNombreProyectoSpring(nombre: string): string {
  return (nombre || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
}

export function motivoBloqueoSpring(estado: EstadoGeneracionSpring): string {
  if (!estado.proyectoId || estado.proyectoId !== estado.proyectoActivoId) {
    return 'No existe un proyecto activo confirmado.';
  }
  if (!puedeExportarSpring(estado.rol)) return 'No tienes permiso para exportar este proyecto.';
  if (estado.conflicto) return 'Resuelve el conflicto de revisión antes de generar.';
  if (estado.guardado === 'guardando') return 'Esperando la confirmación del autoguardado.';
  if (estado.guardado === 'error') return 'El último guardado no fue confirmado por el servidor.';
  if (estado.conexion !== 'conectado') return 'La conexión no permite certificar la revisión confirmada.';
  if (estado.generando) return 'Ya existe una generación en curso.';
  return '';
}

export function puedeGenerarSpring(estado: EstadoGeneracionSpring): boolean {
  return motivoBloqueoSpring(estado) === '';
}
