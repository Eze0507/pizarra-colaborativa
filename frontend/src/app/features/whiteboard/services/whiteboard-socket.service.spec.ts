import { fakeAsync, TestBed, tick } from '@angular/core/testing';

import { WhiteboardSocketService } from './whiteboard-socket.service';

describe('WhiteboardSocketService - revisiones F06', () => {
  let service: WhiteboardSocketService;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [WhiteboardSocketService] });
    service = TestBed.inject(WhiteboardSocketService);
  });

  afterEach(() => service.desconectar());

  it('envia expected_revision y request_id en el guardado', () => {
    const send = spyOn<any>(service, 'enviarMensaje');
    service.establecerRevision(7);
    service.forzarGuardarSnapshot({ entidades: [] });
    expect(send).toHaveBeenCalledWith(jasmine.objectContaining({
      accion: 'guardar_snapshot', expected_revision: 7,
      request_id: jasmine.stringMatching(/^ws-/)
    }));
  });

  it('serializa guardados y conserva el snapshot mas reciente en cola', () => {
    const send = spyOn<any>(service, 'enviarMensaje');
    service.forzarGuardarSnapshot({ version: 1 });
    service.forzarGuardarSnapshot({ version: 2 });
    expect(send).toHaveBeenCalledTimes(1);
    expect((service as any).snapshotEnCola.datos).toEqual({ version: 2 });
  });

  it('liga el autosave a la revision conocida al editar', () => {
    const send = spyOn<any>(service, 'enviarMensaje');
    (service as any).snapshotSub = (service as any)._snapshotTrigger$
      .subscribe((pendiente: any) => (service as any).encolarOEnviarSnapshot(pendiente));
    service.establecerRevision(3);
    service.programarGuardarSnapshot({ local: true });
    service.establecerRevision(4);
    expect(send).toHaveBeenCalledWith(jasmine.objectContaining({ expected_revision: 3 }));
  });

  it('suspende escrituras y conserva cambios locales tras conflicto', () => {
    const send = spyOn<any>(service, 'enviarMensaje');
    service.registrarConflictoRevision(8);
    service.forzarGuardarSnapshot({ local: true });
    expect(send).not.toHaveBeenCalled();
    expect((service as any).snapshotEnCola.datos).toEqual({ local: true });
  });

  it('permite descartar explicitamente el borrador tras confirmacion del usuario', () => {
    service.registrarConflictoRevision(8);
    service.forzarGuardarSnapshot({ local: true });
    service.descartarCambiosLocalesEnConflicto();
    expect((service as any).snapshotEnCola).toBeNull();
  });

  it('confirma A aunque B siga en debounce y solo marca guardado al confirmar B', fakeAsync(() => {
    const send = spyOn<any>(service, 'enviarMensaje');
    const estados: string[] = [];
    service.estadoGuardado$.subscribe(estado => estados.push(estado));
    (service as any).proyectoActual = 41;
    (service as any).iniciarDebounceSnapshots();

    service.forzarGuardarSnapshot({ version: 'A' });
    const requestA = (send.calls.mostRecent().args[0] as any).request_id;
    service.programarGuardarSnapshot({ version: 'B' });

    expect((service as any).procesarConfirmacionSnapshot({
      accion: 'snapshot_guardado', exito: true, proyecto_id: 41,
      request_id: requestA, revision: 1
    })).toBeTrue();
    expect(service.revisionActual).toBe(1);
    expect(estados.at(-1)).toBe('guardando');

    tick(2_000);
    expect(send).toHaveBeenCalledTimes(2);
    expect(send.calls.mostRecent().args[0]).toEqual(jasmine.objectContaining({
      datos_diagrama: { version: 'B' }, expected_revision: 1
    }));

    const requestB = (send.calls.mostRecent().args[0] as any).request_id;
    expect((service as any).procesarConfirmacionSnapshot({
      accion: 'snapshot_guardado', exito: true, proyecto_id: 41,
      request_id: requestB, revision: 2
    })).toBeTrue();
    expect(service.revisionActual).toBe(2);
    expect(estados.at(-1)).toBe('guardado');
  }));

  it('ignora confirmaciones ajenas, antiguas, sin revision o de otro proyecto', () => {
    const send = spyOn<any>(service, 'enviarMensaje');
    (service as any).proyectoActual = 9;
    service.establecerRevision(4);
    service.forzarGuardarSnapshot({ version: 'local' });
    const request = (send.calls.mostRecent().args[0] as any).request_id;

    for (const mensaje of [
      { proyecto_id: 9, request_id: 'otro', revision: 5 },
      { proyecto_id: 8, request_id: request, revision: 5 },
      { proyecto_id: 9, request_id: request },
      { proyecto_id: 9, request_id: request, revision: 4 },
      { proyecto_id: 9, request_id: request, revision: 7 }
    ]) {
      expect((service as any).procesarConfirmacionSnapshot({
        accion: 'snapshot_guardado', exito: true, ...mensaje
      })).toBeFalse();
    }
    expect((service as any).guardadoPendiente).toBeTrue();
    expect(service.revisionActual).toBe(4);
  });

  it('acepta una confirmacion una sola vez y la duplicada es idempotente', () => {
    const send = spyOn<any>(service, 'enviarMensaje');
    (service as any).proyectoActual = 3;
    service.forzarGuardarSnapshot({ version: 1 });
    const mensaje = {
      accion: 'snapshot_guardado', exito: true, proyecto_id: 3,
      request_id: (send.calls.mostRecent().args[0] as any).request_id, revision: 1
    };
    expect((service as any).procesarConfirmacionSnapshot(mensaje)).toBeTrue();
    expect((service as any).procesarConfirmacionSnapshot(mensaje)).toBeFalse();
    expect(service.revisionActual).toBe(1);
  });

  it('un rechazo correlacionado conserva el ultimo snapshot para reintento', () => {
    const send = spyOn<any>(service, 'enviarMensaje');
    (service as any).proyectoActual = 6;
    service.forzarGuardarSnapshot({ version: 'A' });
    const request = (send.calls.mostRecent().args[0] as any).request_id;
    service.programarGuardarSnapshot({ version: 'B' });
    (service as any).procesarRechazoSnapshot({
      accion: 'comando_rechazado', exito: false, codigo: 'snapshot_rejected',
      proyecto_id: 6, request_id: request
    });
    expect((service as any).snapshotEnCola.datos).toEqual({ version: 'B' });
    expect((service as any)._estadoGuardado$.getValue()).toBe('error');
    expect((service as any).guardadoPendiente).toBeFalse();
  });

  it('un rechazo ajeno no libera el guardado local', () => {
    const send = spyOn<any>(service, 'enviarMensaje');
    (service as any).proyectoActual = 6;
    service.forzarGuardarSnapshot({ version: 'A' });
    (service as any).procesarRechazoSnapshot({
      accion: 'comando_rechazado', exito: false, codigo: 'snapshot_rejected',
      proyecto_id: 6, request_id: 'otro'
    });
    expect((service as any).guardadoPendiente).toBeTrue();
    expect((service as any)._estadoGuardado$.getValue()).toBe('guardando');
    expect(send).toHaveBeenCalledTimes(1);
  });

  it('el timeout conserva cambios y pasa a error sin confirmar ni reenviar', fakeAsync(() => {
    const send = spyOn<any>(service, 'enviarMensaje');
    service.forzarGuardarSnapshot({ version: 'incierta' });
    tick(15_000);
    expect((service as any)._estadoGuardado$.getValue()).toBe('error');
    expect((service as any).snapshotEnCola.datos).toEqual({ version: 'incierta' });
    expect((service as any).guardadoPendiente).toBeFalse();
    expect(send).toHaveBeenCalledTimes(1);
  }));

  it('forzar guardado invalida el debounce anterior y evita un duplicado tardio', () => {
    const send = spyOn<any>(service, 'enviarMensaje');
    service.programarGuardarSnapshot({ version: 'debounce' });
    const anterior = (service as any).snapshotEnDebounce;
    service.forzarGuardarSnapshot({ version: 'forzada' });
    expect(send).toHaveBeenCalledTimes(1);
    expect((service as any).snapshotEnDebounce).toBeNull();
    expect(anterior.datos).toEqual({ version: 'debounce' });
  });
});
