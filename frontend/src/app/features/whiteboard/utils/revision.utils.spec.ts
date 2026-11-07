import { confirmacionCorresponde, esConflictoRevision, requestCorresponde } from './revision.utils';

describe('contrato de revision F06', () => {
  it('acepta la confirmacion de la solicitud pendiente', () => {
    expect(confirmacionCorresponde('req-1', { request_id: 'req-1', exito: true })).toBeTrue();
  });

  it('rechaza una confirmacion obsoleta o fallida', () => {
    expect(confirmacionCorresponde('req-2', { request_id: 'req-1', exito: true })).toBeFalse();
    expect(confirmacionCorresponde('req-2', { request_id: 'req-2', exito: false })).toBeFalse();
  });

  it('rechaza eventos confirmados cuando no hay solicitud local pendiente', () => {
    expect(confirmacionCorresponde(null, { request_id: 'remota', exito: true })).toBeFalse();
    expect(confirmacionCorresponde('req-1', { request_id: undefined, exito: true })).toBeFalse();
  });

  it('correlaciona rechazos sin convertirlos artificialmente en exitos', () => {
    expect(requestCorresponde('req-1', { request_id: 'req-1' })).toBeTrue();
    expect(requestCorresponde('req-1', { request_id: 'req-2' })).toBeFalse();
    expect(requestCorresponde(null, { request_id: 'req-1' })).toBeFalse();
  });

  it('identifica exclusivamente stale_revision como conflicto de concurrencia', () => {
    expect(esConflictoRevision({ accion: 'comando_rechazado', codigo: 'stale_revision', exito: false })).toBeTrue();
    expect(esConflictoRevision({ accion: 'comando_rechazado', codigo: 'permission_denied', exito: false })).toBeFalse();
  });
});
