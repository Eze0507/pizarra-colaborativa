import { MensajeWS } from '../interfaces/diagrama.interface';

export function confirmacionCorresponde(
  requestPendiente: string | null,
  mensaje: Pick<MensajeWS, 'request_id' | 'exito'>
): boolean {
  return mensaje.exito !== false && requestCorresponde(requestPendiente, mensaje);
}

export function requestCorresponde(
  requestPendiente: string | null,
  mensaje: Pick<MensajeWS, 'request_id'>
): boolean {
  return typeof requestPendiente === 'string' && requestPendiente.length > 0 &&
    typeof mensaje.request_id === 'string' && mensaje.request_id === requestPendiente;
}

export function esConflictoRevision(
  mensaje: Pick<MensajeWS, 'accion' | 'codigo' | 'exito'>
): boolean {
  return mensaje.accion === 'comando_rechazado' &&
    mensaje.exito === false && mensaje.codigo === 'stale_revision';
}
