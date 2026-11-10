import { ComponentFixture, TestBed } from '@angular/core/testing';
import { BehaviorSubject, Subject } from 'rxjs';

import { TokenStorageService } from './core/services/token-storage.service';
import { ToastNotificationService } from './core/services/toast-notification.service';
import { ChatAgenteSeniorComponent } from './features/whiteboard/components/chat-agente-senior/chat-agente-senior.component';
import { MensajeAgenteSenior } from './features/whiteboard/interfaces/asistente-ia.interface';
import { AgenteSeniorService, ESTADO_COLA_INICIAL } from './features/whiteboard/services/agente-senior.service';


describe('ChatAgenteSeniorComponent', () => {
  let fixture: ComponentFixture<ChatAgenteSeniorComponent>;
  let component: ChatAgenteSeniorComponent;

  const mensajes$ = new BehaviorSubject<MensajeAgenteSenior[]>([]);
  const serviceMock = {
    mensajes$: mensajes$.asObservable(),
    estadoCola$: new BehaviorSubject(ESTADO_COLA_INICIAL).asObservable(),
    cargandoHistorial$: new BehaviorSubject(false).asObservable(),
    enviandoConsulta$: new BehaviorSubject(false).asObservable(),
    maxCaracteres$: new BehaviorSubject(2000).asObservable(),
    usarIaLocal$: new BehaviorSubject(false).asObservable(),
    nuevoMensajeRecibido$: new Subject<MensajeAgenteSenior>().asObservable(),
    consultaRevertida$: new Subject<string>().asObservable(),
    eventoError$: new Subject<string>().asObservable(),
    inicializarProyecto: jasmine.createSpy('inicializarProyecto'),
    limpiarEstado: jasmine.createSpy('limpiarEstado'),
    cargarHistorial: jasmine.createSpy('cargarHistorial'),
    setUsarIaLocal: jasmine.createSpy('setUsarIaLocal'),
    formatearMarkdown: (texto: string) => `<p>${texto}</p>`
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatAgenteSeniorComponent],
      providers: [
        { provide: AgenteSeniorService, useValue: serviceMock },
        { provide: TokenStorageService, useValue: { getUser: () => null } },
        { provide: ToastNotificationService, useValue: { error: jasmine.createSpy('error') } }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ChatAgenteSeniorComponent);
    component = fixture.componentInstance;
    component.chatAbierto = true;
    fixture.detectChanges();
  });

  afterEach(() => {
    mensajes$.next([]);
  });

  function mensajeAgente(overrides: Partial<MensajeAgenteSenior> = {}): MensajeAgenteSenior {
    return {
      id: 2,
      conversacion_id: 1,
      fecha_envio: '2026-11-09T12:00:00Z',
      estado: 'respondido',
      rol: 'AGENT',
      contenido: 'Respuesta del agente',
      pregunta_id: 1,
      usuario: null,
      posicion_cola: null,
      ...overrides
    };
  }

  it('muestra proveedor, modelo y respaldo separados del contenido', () => {
    mensajes$.next([
      mensajeAgente({
        provider: 'ollama',
        model: 'qwen-test',
        fallback_used: true
      })
    ]);
    fixture.detectChanges();

    const badge = fixture.nativeElement.querySelector('.badge-proveedor') as HTMLElement;
    const cuerpo = fixture.nativeElement.querySelector('.burbuja-cuerpo') as HTMLElement;
    expect(badge.textContent?.trim()).toBe('Ollama · qwen-test · Respaldo');
    expect(cuerpo.textContent).toContain('Respuesta del agente');
    expect(cuerpo.textContent).not.toContain('qwen-test');
  });

  it('muestra el modelo Gemini sin indicar respaldo', () => {
    mensajes$.next([
      mensajeAgente({
        provider: 'gemini',
        model: 'gemini-test',
        fallback_used: false
      })
    ]);
    fixture.detectChanges();

    const badge = fixture.nativeElement.querySelector('.badge-proveedor') as HTMLElement;
    expect(badge.textContent?.trim()).toBe('Gemini · gemini-test');
    expect(badge.textContent).not.toContain('Respaldo');
  });

  it('mantiene visible un mensaje histórico sin metadatos', () => {
    mensajes$.next([mensajeAgente()]);
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.badge-proveedor')).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('Respuesta del agente');
  });
});
