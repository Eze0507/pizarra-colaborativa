import {
  Component,
  Input,
  OnInit,
  OnChanges,
  OnDestroy,
  SimpleChanges,
  ViewChild,
  ElementRef,
  ChangeDetectorRef,
  inject
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Subscription } from 'rxjs';

import {
  ContextoDiagramaIA,
  EstadoColaAgenteSenior,
  MensajeAgenteSenior
} from '../../interfaces/asistente-ia.interface';
import { AgenteSeniorService, ESTADO_COLA_INICIAL } from '../../services/agente-senior.service';
import { TokenStorageService } from '../../../../core/services/token-storage.service';
import { ToastNotificationService } from '../../../../core/services/toast-notification.service';

@Component({
  selector: 'app-chat-agente-senior',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-agente-senior.component.html',
  styleUrls: ['./chat-agente-senior.component.css']
})
export class ChatAgenteSeniorComponent implements OnInit, OnChanges, OnDestroy {
  private readonly agenteSeniorService = inject(AgenteSeniorService);
  private readonly tokenStorage = inject(TokenStorageService);
  private readonly toastService = inject(ToastNotificationService);
  private readonly cdr = inject(ChangeDetectorRef);

  @Input() public proyectoId = 0;
  @Input() public contextoDiagrama: ContextoDiagramaIA = { entidades: [], relaciones: [] };
  @Input() public modoOscuro = true;

  @ViewChild('seniorInput') public seniorInputRef?: ElementRef<HTMLTextAreaElement>;
  @ViewChild('seniorMessagesContainer') public seniorMessagesContainerRef?: ElementRef<HTMLDivElement>;

  public chatAbierto = false;
  public mensajes: MensajeAgenteSenior[] = [];
  public estadoCola: EstadoColaAgenteSenior = ESTADO_COLA_INICIAL;
  public cargandoHistorial = false;
  public enviandoConsulta = false;
  public maxCaracteres = 2000;
  public textoConsulta = '';
  public errorValidacionLocal: string | null = null;
  public mensajesSinLeer = 0;
  public miUsuarioId: number | null = null;

  private readonly subs = new Subscription();

  public ngOnInit(): void {
    this.miUsuarioId = this.tokenStorage.getUser()?.id ?? null;
    this.suscribirEstadoServicio();
    if (this.proyectoId > 0) {
      this.agenteSeniorService.inicializarProyecto(this.proyectoId);
    }
  }

  public ngOnChanges(changes: SimpleChanges): void {
    if (changes['proyectoId'] && !changes['proyectoId'].firstChange) {
      const nuevoId = Number(changes['proyectoId'].currentValue);
      if (nuevoId > 0) {
        this.agenteSeniorService.inicializarProyecto(nuevoId);
      }
    }
  }

  public ngOnDestroy(): void {
    this.subs.unsubscribe();
    this.agenteSeniorService.limpiarEstado();
  }

  public toggleChat(): void {
    this.chatAbierto = !this.chatAbierto;
    if (this.chatAbierto) {
      this.mensajesSinLeer = 0;
      if (this.proyectoId > 0 && this.mensajes.length === 0) {
        this.agenteSeniorService.cargarHistorial(this.proyectoId);
      }
      this.enfocarYDesplazar();
    }
  }

  public cerrarChat(): void {
    this.chatAbierto = false;
  }

  public recargarHistorial(): void {
    if (this.proyectoId > 0) {
      this.agenteSeniorService.cargarHistorial(this.proyectoId);
    }
  }

  public onInputCambio(): void {
    if (this.textoConsulta.length > this.maxCaracteres) {
      this.errorValidacionLocal = `La consulta supera el límite máximo de ${this.maxCaracteres} caracteres.`;
    } else {
      this.errorValidacionLocal = null;
    }
  }

  public onEnterInput(event: Event): void {
    const keyEvent = event as KeyboardEvent;
    if (!keyEvent.shiftKey) {
      event.preventDefault();
      this.enviarConsulta();
    }
  }

  public enviarConsulta(): void {
    const texto = this.textoConsulta.trim();
    if (!texto) {
      this.errorValidacionLocal = 'La consulta no puede estar vacía.';
      return;
    }
    if (texto.length > this.maxCaracteres) {
      this.errorValidacionLocal = `La consulta excede el límite de ${this.maxCaracteres} caracteres.`;
      return;
    }
    if (this.estadoCola.cola_llena || this.enviandoConsulta || !this.proyectoId) {
      return;
    }

    this.errorValidacionLocal = null;
    const respaldoTexto = this.textoConsulta;
    this.textoConsulta = '';

    this.agenteSeniorService
      .enviarConsulta(this.proyectoId, texto, this.contextoDiagrama)
      .subscribe({
        next: () => {
          this.scrollAlFondo();
          this.enfocarInput();
        },
        error: (err: HttpErrorResponse) => {
          this.textoConsulta = respaldoTexto;
          this.agenteSeniorService.actualizarColaDesdeError(err);
          const msg = this.agenteSeniorService.extraerMensajeError(
            err,
            'No se pudo enviar la consulta al Agente Senior.'
          );
          this.errorValidacionLocal = msg;
          this.toastService.error(msg);
          this.cdr.detectChanges();
        }
      });
  }

  public esMiMensaje(msg: MensajeAgenteSenior): boolean {
    return msg.rol === 'USER' && this.miUsuarioId !== null && msg.usuario?.id === this.miUsuarioId;
  }

  public obtenerNombreAutor(msg: MensajeAgenteSenior): string {
    if (msg.rol === 'AGENT') {
      return 'Agente Senior';
    }
    if (!msg.usuario) {
      return 'Colaborador';
    }
    if (this.esMiMensaje(msg)) {
      return `Tú (@${msg.usuario.username})`;
    }
    return msg.usuario.nombre_completo
      ? `${msg.usuario.nombre_completo} (@${msg.usuario.username})`
      : `@${msg.usuario.username}`;
  }

  public trackByMensajeId(_index: number, item: MensajeAgenteSenior): number {
    return item.id;
  }

  public obtenerContenidoHtml(msg: MensajeAgenteSenior): string {
    return this.agenteSeniorService.formatearMarkdown(msg.contenido);
  }

  private suscribirEstadoServicio(): void {
    this.subs.add(
      this.agenteSeniorService.mensajes$.subscribe(lista => {
        this.mensajes = lista;
        this.cdr.detectChanges();
        if (this.chatAbierto) {
          this.scrollAlFondo();
        }
      })
    );

    this.subs.add(
      this.agenteSeniorService.estadoCola$.subscribe(cola => {
        this.estadoCola = cola;
        this.cdr.detectChanges();
      })
    );

    this.subs.add(
      this.agenteSeniorService.cargandoHistorial$.subscribe(cargando => {
        this.cargandoHistorial = cargando;
        this.cdr.detectChanges();
      })
    );

    this.subs.add(
      this.agenteSeniorService.enviandoConsulta$.subscribe(enviando => {
        this.enviandoConsulta = enviando;
        this.cdr.detectChanges();
      })
    );

    this.subs.add(
      this.agenteSeniorService.maxCaracteres$.subscribe(max => {
        this.maxCaracteres = max;
      })
    );

    this.subs.add(
      this.agenteSeniorService.nuevoMensajeRecibido$.subscribe(msg => {
        if (!this.chatAbierto && !this.esMiMensaje(msg)) {
          this.mensajesSinLeer++;
          this.cdr.detectChanges();
        }
      })
    );

    this.subs.add(
      this.agenteSeniorService.consultaRevertida$.subscribe(textoOriginal => {
        if (!this.textoConsulta.trim()) {
          this.textoConsulta = textoOriginal;
          this.cdr.detectChanges();
        }
      })
    );

    this.subs.add(
      this.agenteSeniorService.eventoError$.subscribe(mensajeError => {
        this.toastService.error(mensajeError);
      })
    );
  }

  private enfocarYDesplazar(): void {
    setTimeout(() => {
      this.scrollAlFondo();
      this.enfocarInput();
    }, 120);
  }

  private enfocarInput(): void {
    setTimeout(() => this.seniorInputRef?.nativeElement?.focus(), 80);
  }

  private scrollAlFondo(): void {
    setTimeout(() => {
      const el = this.seniorMessagesContainerRef?.nativeElement;
      if (el) {
        el.scrollTop = el.scrollHeight;
      }
    }, 50);
  }
}

