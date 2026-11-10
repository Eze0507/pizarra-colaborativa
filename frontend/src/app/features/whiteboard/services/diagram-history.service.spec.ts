import { TestBed, fakeAsync, flushMicrotasks } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { DiagramHistoryService } from './diagram-history.service';
import { WhiteboardSocketService } from './whiteboard-socket.service';

describe('DiagramHistoryService: autoridad, sesiones y operaciones pendientes', () => {
  let service: DiagramHistoryService;
  let http: HttpTestingController;
  let socket: any;
  const history = { proyecto_id: 3, revision: 5, canUndo: true, canRedo: false, limit: 50, operations: [] };
  beforeEach(() => {
    socket = { revisionActual: 5, esperarGuardadoConfirmado: jasmine.createSpy().and.resolveTo(), registrarConflictoRevision: jasmine.createSpy() };
    TestBed.configureTestingModule({ providers: [DiagramHistoryService, provideHttpClient(), provideHttpClientTesting(),
      { provide: WhiteboardSocketService, useValue: socket }] });
    service = TestBed.inject(DiagramHistoryService);
    http = TestBed.inject(HttpTestingController);
  });
  afterEach(() => { http.verify(); service.clearLocalState(); });
  function load(): void {
    void service.loadHistory(3);
    http.expectOne(req => req.url.endsWith('/3/historial/')).flush(history);
    flushMicrotasks();
  }
  it('cargar o volver a abrir consulta sin ejecutar acciones', fakeAsync(() => {
    load();
    expect(service.canUndo).toBeTrue();
    expect(socket.esperarGuardadoConfirmado).not.toHaveBeenCalled();
    service.clearLocalState();
    load();
    expect(service.canUndo).toBeTrue();
  }));
  it('espera guardado confirmado y publica éxito únicamente después del POST', fakeAsync(() => {
    load();
    let confirm!: () => void;
    socket.esperarGuardadoConfirmado.and.returnValue(new Promise<void>(resolve => { confirm = resolve; }));
    const results = jasmine.createSpy();
    service.confirmed$.subscribe(results);
    void service.execute({ action: 'undo' });
    flushMicrotasks();
    http.expectNone(req => req.method === 'POST');
    expect(service.busy$.value).toBeTrue();
    expect(results).not.toHaveBeenCalled();
    socket.revisionActual = 6;
    confirm(); flushMicrotasks();
    const post = http.expectOne(req => req.method === 'POST');
    expect(post.request.body.expected_revision).toBe(6);
    expect(results).not.toHaveBeenCalled();
    post.flush({ exito: true, proyecto_id: 3, revision: 7, mensaje: 'Deshecho', warnings: [], history: { ...history, revision: 7 } });
    flushMicrotasks();
    expect(results).toHaveBeenCalledTimes(1);
    expect(service.busy$.value).toBeFalse();
  }));
  it('guardado rechazado o desconectado no ejecuta el historial', fakeAsync(() => {
    load();
    socket.esperarGuardadoConfirmado.and.rejectWith(new Error('desconectado'));
    void service.execute({ action: 'undo' }); flushMicrotasks();
    http.expectNone(req => req.method === 'POST');
    http.expectOne(req => req.method === 'GET').flush(history); flushMicrotasks();
    expect(service.busy$.value).toBeFalse();
  }));
  it('reintenta confirmación perdida con mismo ID, revisión y comando', fakeAsync(() => {
    load();
    void service.execute({ action: 'undo' }); flushMicrotasks();
    const first = http.expectOne(req => req.method === 'POST');
    const body = first.request.body;
    first.error(new ProgressEvent('error')); flushMicrotasks();
    http.expectOne(req => req.method === 'GET').flush(history); flushMicrotasks();
    socket.revisionActual = 8;
    void service.execute({ action: 'redo' }); flushMicrotasks();
    const retry = http.expectOne(req => req.method === 'POST');
    expect(retry.request.body).toEqual(body);
    retry.flush({ exito: true, proyecto_id: 3, revision: 6, mensaje: 'Deshecho', warnings: [], history }); flushMicrotasks();
  }));
  it('cambiar de diagrama descarta respuestas locales tardías sin borrar historial del servidor', fakeAsync(() => {
    void service.loadHistory(3);
    const first = http.expectOne(req => req.url.endsWith('/3/historial/'));
    void service.loadHistory(4);
    const second = http.expectOne(req => req.url.endsWith('/4/historial/'));
    second.flush({ ...history, proyecto_id: 4 }); flushMicrotasks();
    first.flush(history); flushMicrotasks();
    expect(service.state$.value?.proyecto_id).toBe(4);
  }));
});
