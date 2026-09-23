import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  ViewChild,
  ElementRef,
  inject
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Subscription } from 'rxjs';

import {
  MensajeChatIA,
  ContextoDiagramaIA,
  DeltaInstruccionIARespuesta
} from '../../interfaces/asistente-ia.interface';
import { AsistenteIaService } from '../../services/asistente-ia.service';
import { ToastNotificationService } from '../../../../core/services/toast-notification.service';

@Component({
  selector: 'app-chat-asistente-ia',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-asistente-ia.component.html',
  styleUrls: ['./chat-asistente-ia.component.css']
})
export class ChatAsistenteIaComponent implements OnInit, OnDestroy {
  private readonly asistenteIaService = inject(AsistenteIaService);
  private readonly toastService = inject(ToastNotificationService);

  @Input() public contextoDiagrama: ContextoDiagramaIA = { entidades: [], relaciones: [] };
  @Input() public modoOscuro = false;

  @Output() public readonly ejecutarDeltaIA = new EventEmitter<DeltaInstruccionIARespuesta>();

  @ViewChild('chatInput') public chatInputRef?: ElementRef<HTMLTextAreaElement>;
  @ViewChild('chatMessagesContainer') public chatMessagesContainerRef?: ElementRef<HTMLDivElement>;

  public chatAbierto = false;
  public mensajesChat: MensajeChatIA[] = [];
  public textoInstruccion = '';
  public cargandoInstruccion = false;
  public escuchandoMicrofono = false;

  private readonly subs = new Subscription();

  public ngOnInit(): void {
    this.suscribirEventosVoz();
  }

  public ngOnDestroy(): void {
    this.asistenteIaService.detenerReconocimientoVoz();
    this.subs.unsubscribe();
  }

  public toggleChat(): void {
    this.chatAbierto = !this.chatAbierto;
    if (this.chatAbierto) {
      setTimeout(() => {
        this.scrollChatAlFondo();
        this.chatInputRef?.nativeElement?.focus();
      }, 150);
    } else if (this.escuchandoMicrofono) {
      this.detenerMicrofono();
    }
  }

  public cerrarChat(): void {
    this.chatAbierto = false;
    if (this.escuchandoMicrofono) {
      this.detenerMicrofono();
    }
  }

  public alternarMicrofono(): void {
    if (this.escuchandoMicrofono) {
      this.detenerMicrofono();
    } else {
      this.iniciarMicrofono();
    }
  }

  public iniciarMicrofono(): void {
    this.asistenteIaService.iniciarReconocimientoVoz();
  }

  public detenerMicrofono(): void {
    this.asistenteIaService.detenerReconocimientoVoz();
    setTimeout(() => this.chatInputRef?.nativeElement?.focus(), 100);
  }

  public onEnterInput(event: Event): void {
    const keyEvent = event as KeyboardEvent;
    if (!keyEvent.shiftKey) {
      event.preventDefault();
      this.enviarInstruccion();
    }
  }

  public enviarInstruccion(): void {
    const texto = this.textoInstruccion.trim();
    if (!texto || this.cargandoInstruccion) return;

    if (this.escuchandoMicrofono) {
      this.detenerMicrofono();
    }

    const msgUsuario: MensajeChatIA = {
      id: `usr_${Date.now()}`,
      remitente: 'usuario',
      texto,
      fecha: new Date()
    };
    this.mensajesChat.push(msgUsuario);
    this.textoInstruccion = '';
    this.cargandoInstruccion = true;
    this.scrollChatAlFondo();

    this.procesarLlamadaBackend(texto);
  }

  public limpiarHistorial(): void {
    this.mensajesChat = [];
    this.toastService.info('Historial del chat reiniciado');
  }

  private procesarLlamadaBackend(texto: string): void {
    this.asistenteIaService
      .ejecutarInstruccion(texto, this.contextoDiagrama)
      .subscribe({
        next: (delta) => this.manejarExitoInstruccion(delta),
        error: (err: HttpErrorResponse) => this.manejarErrorInstruccion(err)
      });
  }

  private manejarExitoInstruccion(delta: DeltaInstruccionIARespuesta): void {
    this.cargandoInstruccion = false;
    const msgAsistente: MensajeChatIA = {
      id: `ia_${Date.now()}`,
      remitente: 'asistente',
      texto: delta.mensaje || 'Instrucción ejecutada con éxito.',
      fecha: new Date()
    };
    this.mensajesChat.push(msgAsistente);
    this.ejecutarDeltaIA.emit(delta);
    this.scrollChatAlFondo();
    setTimeout(() => this.chatInputRef?.nativeElement?.focus(), 100);
  }

  private manejarErrorInstruccion(err: HttpErrorResponse): void {
    this.cargandoInstruccion = false;
    const errorMsg = err.error?.error || 'Error al procesar la instrucción con la IA.';
    const msgError: MensajeChatIA = {
      id: `ia_err_${Date.now()}`,
      remitente: 'asistente',
      texto: `⚠️ ${errorMsg}`,
      fecha: new Date()
    };
    this.mensajesChat.push(msgError);
    this.toastService.error(errorMsg);
    this.scrollChatAlFondo();
    setTimeout(() => this.chatInputRef?.nativeElement?.focus(), 100);
  }

  private suscribirEventosVoz(): void {
    this.subs.add(
      this.asistenteIaService.escuchandoVoz$.subscribe(esc => {
        this.escuchandoMicrofono = esc;
      })
    );

    this.subs.add(
      this.asistenteIaService.textoVozProvisional$.subscribe(texto => {
        this.textoInstruccion = texto;
      })
    );

    this.subs.add(
      this.asistenteIaService.textoVozFinal$.subscribe(texto => {
        this.textoInstruccion = texto;
        this.asistenteIaService.detenerReconocimientoVoz();
        this.enviarInstruccion();
      })
    );

    this.subs.add(
      this.asistenteIaService.errorVoz$.subscribe(err => {
        this.escuchandoMicrofono = false;
        this.toastService.info(err);
        setTimeout(() => this.chatInputRef?.nativeElement?.focus(), 100);
      })
    );
  }

  private scrollChatAlFondo(): void {
    setTimeout(() => {
      const el = this.chatMessagesContainerRef?.nativeElement;
      if (el) {
        el.scrollTop = el.scrollHeight;
      }
    }, 50);
  }
}
