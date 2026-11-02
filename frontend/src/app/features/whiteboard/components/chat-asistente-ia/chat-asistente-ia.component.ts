import {
  Component,
  Input,
  Output,
  EventEmitter,
  OnInit,
  OnDestroy,
  ViewChild,
  ElementRef,
  HostListener,
  inject,
  ChangeDetectorRef
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { Subscription } from 'rxjs';

import {
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
  private readonly cdr = inject(ChangeDetectorRef);

  @Input() public contextoDiagrama: ContextoDiagramaIA = { entidades: [], relaciones: [] };
  @Input() public modoOscuro = true;

  @Output() public readonly ejecutarDeltaIA = new EventEmitter<DeltaInstruccionIARespuesta>();

  @ViewChild('instruccionInput') public instruccionInputRef?: ElementRef<HTMLInputElement>;

  public textoInstruccion = '';
  public instruccionEnProceso = '';
  public cargandoInstruccion = false;
  public escuchandoMicrofono = false;
  public espacioPresionado = false;

  private timerDebounceEnvio: number | null = null;
  private readonly subs = new Subscription();

  public ngOnInit(): void {
    this.suscribirEventosVoz();
  }

  public ngOnDestroy(): void {
    if (this.timerDebounceEnvio !== null) {
      window.clearTimeout(this.timerDebounceEnvio);
      this.timerDebounceEnvio = null;
    }
    this.asistenteIaService.detenerReconocimientoVoz(false);
    this.subs.unsubscribe();
  }

  // ── Push-to-Talk con Barra Espaciadora (cuando no se está escribiendo en un input) ──

  @HostListener('window:keydown', ['$event'])
  public onKeyDownGlobal(evt: KeyboardEvent): void {
    if (evt.code !== 'Space' && evt.key !== ' ') return;
    if (this.cargandoInstruccion) return;
    if (evt.repeat) {
      if (this.espacioPresionado) {
        evt.preventDefault();
      }
      return;
    }
    if (this.esElementoEditable(evt.target)) {
      return;
    }

    evt.preventDefault();
    this.espacioPresionado = true;
    this.iniciarMicrofono();
  }

  @HostListener('window:keyup', ['$event'])
  public onKeyUpGlobal(evt: KeyboardEvent): void {
    if (evt.code !== 'Space' && evt.key !== ' ') return;
    if (!this.espacioPresionado) return;

    evt.preventDefault();
    this.espacioPresionado = false;
    this.detenerMicrofonoYEnviar();
  }

  private esElementoEditable(target: EventTarget | null): boolean {
    if (!target || !(target instanceof HTMLElement)) return false;
    const tag = target.tagName.toLowerCase();
    if (tag === 'input' || tag === 'textarea') return true;
    if (target.isContentEditable) return true;
    return false;
  }

  // ── Dictado y Reconocimiento de Voz ──

  public alternarMicrofono(): void {
    if (this.cargandoInstruccion) return;
    if (this.escuchandoMicrofono) {
      this.detenerMicrofonoYEnviar();
    } else {
      this.iniciarMicrofono();
    }
  }

  public iniciarMicrofono(): void {
    if (this.timerDebounceEnvio !== null) {
      window.clearTimeout(this.timerDebounceEnvio);
      this.timerDebounceEnvio = null;
    }
    this.textoInstruccion = '';
    this.asistenteIaService.iniciarReconocimientoVoz();
    this.cdr.markForCheck();
  }

  public detenerMicrofono(): void {
    this.asistenteIaService.detenerReconocimientoVoz(false);
    this.espacioPresionado = false;
    if (this.timerDebounceEnvio !== null) {
      window.clearTimeout(this.timerDebounceEnvio);
      this.timerDebounceEnvio = null;
    }
    this.cdr.markForCheck();
  }

  public detenerMicrofonoYEnviar(): void {
    const textoVoz = this.asistenteIaService.detenerReconocimientoVoz(false);
    const textoAEnviar = (textoVoz || this.textoInstruccion || this.asistenteIaService.ultimoTextoVoz).trim();
    this.textoInstruccion = '';
    if (this.timerDebounceEnvio !== null) {
      window.clearTimeout(this.timerDebounceEnvio);
    }
    this.timerDebounceEnvio = window.setTimeout(() => {
      this.timerDebounceEnvio = null;
      if (textoAEnviar) {
        this.enviarInstruccion(textoAEnviar);
      } else {
        this.toastService.info('No se detectó audio.');
      }
      this.cdr.markForCheck();
    }, 120);
  }

  // ── Envío de Instrucciones ──

  public onEnterInput(event: Event): void {
    event.preventDefault();
    if (this.escuchandoMicrofono) {
      this.detenerMicrofonoYEnviar();
    } else {
      this.enviarInstruccion();
    }
  }

  public enviarInstruccion(textoManual?: string): void {
    const texto = (textoManual ?? this.textoInstruccion).trim();
    this.textoInstruccion = '';
    if (!texto || this.cargandoInstruccion) return;

    if (this.escuchandoMicrofono) {
      this.detenerMicrofono();
    }

    this.instruccionInputRef?.nativeElement?.blur();
    this.instruccionEnProceso = texto;
    this.cargandoInstruccion = true;
    this.cdr.markForCheck();

    this.asistenteIaService
      .ejecutarInstruccion(texto, this.contextoDiagrama)
      .subscribe({
        next: (delta) => this.manejarExitoInstruccion(delta),
        error: (err: HttpErrorResponse) => this.manejarErrorInstruccion(err)
      });
  }

  private manejarExitoInstruccion(delta: DeltaInstruccionIARespuesta): void {
    this.cargandoInstruccion = false;
    this.instruccionEnProceso = '';
    this.ejecutarDeltaIA.emit(delta);
    this.cdr.markForCheck();
  }

  private manejarErrorInstruccion(err: HttpErrorResponse): void {
    this.cargandoInstruccion = false;
    this.instruccionEnProceso = '';
    const errorMsg = err.error?.detail || err.error?.error || 'Error al procesar la instrucción con la IA.';
    this.toastService.error(errorMsg);
    this.cdr.markForCheck();
  }

  private suscribirEventosVoz(): void {
    this.subs.add(
      this.asistenteIaService.escuchandoVoz$.subscribe(esc => {
        this.escuchandoMicrofono = esc;
        this.cdr.markForCheck();
      })
    );

    this.subs.add(
      this.asistenteIaService.textoVozProvisional$.subscribe(texto => {
        if (this.escuchandoMicrofono) {
          this.textoInstruccion = texto;
          this.cdr.markForCheck();
        }
      })
    );

    this.subs.add(
      this.asistenteIaService.errorVoz$.subscribe(err => {
        this.escuchandoMicrofono = false;
        this.espacioPresionado = false;
        this.toastService.info(err);
        this.cdr.markForCheck();
      })
    );
  }
}
