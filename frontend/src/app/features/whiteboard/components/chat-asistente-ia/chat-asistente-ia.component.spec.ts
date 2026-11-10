import { TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';
import { ChatAsistenteIaComponent } from './chat-asistente-ia.component';
import { AsistenteIaService } from '../../services/asistente-ia.service';
import { DiagramHistoryService } from '../../services/diagram-history.service';
import { WhiteboardSocketService } from '../../services/whiteboard-socket.service';
import { ToastNotificationService } from '../../../../core/services/toast-notification.service';

describe('Barra del asistente: historial sin proveedores y respuestas tardías', () => {
  let ai: any;
  let history: any;
  let socket: any;
  let response: Subject<any>;
  let component: ChatAsistenteIaComponent;
  beforeEach(() => {
    response = new Subject();
    ai = { ejecutarInstruccion: jasmine.createSpy().and.returnValue(response),
      detenerReconocimientoVoz: jasmine.createSpy(), escuchandoVoz$: new Subject(), textoVozProvisional$: new Subject(), errorVoz$: new Subject() };
    history = { execute: jasmine.createSpy(), cancelAssistant$: new Subject(), busy$: new BehaviorSubject(false),
      state$: new BehaviorSubject(null), messages$: new Subject(), canUndo: true, canRedo: false };
    socket = { revisionActual: 4 };
    TestBed.configureTestingModule({ imports: [ChatAsistenteIaComponent], providers: [
      { provide: AsistenteIaService, useValue: ai }, { provide: DiagramHistoryService, useValue: history },
      { provide: WhiteboardSocketService, useValue: socket },
      { provide: ToastNotificationService, useValue: { error: jasmine.createSpy(), info: jasmine.createSpy() } }
    ] });
    const fixture = TestBed.createComponent(ChatAsistenteIaComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });
  for (const text of ['Deshacer', 'Rehacer', 'Restaura unidad', 'Recupera dirección', 'Restaura la última clase eliminada']) {
    it(`${text} no invoca IA`, () => {
      component.enviarInstruccion(text);
      expect(ai.ejecutarInstruccion).not.toHaveBeenCalled();
      expect(history.execute).toHaveBeenCalledTimes(1);
      history.messages$.next({ text: 'Sin historial', error: true });
      expect(ai.ejecutarInstruccion).not.toHaveBeenCalled();
      expect(component.mensajeHistorial).toBe('Sin historial');
    });
  }
  for (const text of ['Agrega dirección a unidad', 'Crea una clase llamada Restaurar']) {
    it(`${text} usa el contrato IA existente`, () => {
      const emit = spyOn(component.ejecutarDeltaIA, 'emit');
      component.enviarInstruccion(text);
      expect(ai.ejecutarInstruccion).toHaveBeenCalledWith(text, component.contextoDiagrama);
      response.next({ acciones: [] });
      expect(emit).toHaveBeenCalledTimes(1);
      expect(history.execute).not.toHaveBeenCalled();
    });
  }
  it('no ejecuta ninguna parte de una orden ambigua', () => {
    component.enviarInstruccion('Deshaz y luego crea cliente');
    expect(history.execute).not.toHaveBeenCalled();
    expect(ai.ejecutarInstruccion).not.toHaveBeenCalled();
  });
  for (const cancellation of ['undo', 'revision', 'context', 'destroy']) {
    it(`ignora respuesta tardía después de ${cancellation}`, () => {
      const emit = spyOn(component.ejecutarDeltaIA, 'emit');
      component.enviarInstruccion('Agrega dirección a unidad');
      if (cancellation === 'undo') history.cancelAssistant$.next();
      if (cancellation === 'revision') socket.revisionActual++;
      if (cancellation === 'context') component.contextoDiagrama = { entidades: [{ id: 7, nombre: 'cambio' } as any], relaciones: [] };
      if (cancellation === 'destroy') component.ngOnDestroy();
      response.next({ acciones: [] });
      expect(emit).not.toHaveBeenCalled();
    });
  }
});
