import {
  Component,
  OnInit,
  OnDestroy,
  ElementRef,
  ViewChild,
  Input,
  inject,
  HostListener
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { AyudaService, MensajeAyudaChat } from '../../../core/services/ayuda.service';

@Component({
  selector: 'app-asistente-ayuda',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './asistente-ayuda.component.html',
  styleUrls: ['./asistente-ayuda.component.css']
})
export class AsistenteAyudaComponent implements OnInit, OnDestroy {
  public readonly ayudaService = inject(AyudaService);

  @ViewChild('mensajesContainer') private mensajesContainerRef?: ElementRef<HTMLDivElement>;
  @ViewChild('inputPregunta') private inputPreguntaRef?: ElementRef<HTMLTextAreaElement>;
  @ViewChild('panelRef') private panelRef?: ElementRef<HTMLDivElement>;

  @Input() public interfaz: 'dashboard' | 'pizarra' = 'dashboard';

  public visible = false;
  public minimizado = false;
  public cargando = false;
  public mensajes: MensajeAyudaChat[] = [];
  public textoConsulta = '';

  // Posicionamiento dinámico para arrastre libre (FA-03)
  public panelLeft = 0;
  public panelTop = 0;
  public isDragging = false;
  private dragStartX = 0;
  private dragStartY = 0;
  private posicionadaInicialmente = false;

  private readonly subs = new Subscription();

  public sugerenciasRapidasDashboard: string[] = [
    '¿Cómo creo un nuevo proyecto?',
    '¿Cómo abro un proyecto para diseñar?',
    '¿Cómo busco un proyecto en la lista?',
    '¿Cómo acepto o rechazo invitaciones?',
    '¿Cómo elimino un proyecto propio?'
  ];

  public sugerenciasRapidasPizarra: string[] = [
    '¿Cómo creo una nueva entidad en el diagrama?',
    '¿Cómo elimino una entidad del lienzo?',
    '¿Cómo genero el código backend Spring Boot?',
    '¿Cómo importo un diagrama desde una foto o boceto?',
    '¿Cómo invito a colaboradores a la pizarra?',
    '¿Cómo ejecuto la validación del modelo?'
  ];

  public get sugerenciasRapidas(): string[] {
    return this.interfaz === 'pizarra' ? this.sugerenciasRapidasPizarra : this.sugerenciasRapidasDashboard;
  }

  public ngOnInit(): void {
    this.subs.add(
      this.ayudaService.panelVisible$.subscribe(vis => {
        this.visible = vis;
        if (vis) {
          if (!this.posicionadaInicialmente) {
            this.inicializarPosicion();
          }
          this.scrollAlFondo();
          setTimeout(() => this.inputPreguntaRef?.nativeElement?.focus(), 150);
        }
      })
    );

    this.subs.add(
      this.ayudaService.minimizado$.subscribe(min => {
        this.minimizado = min;
      })
    );

    this.subs.add(
      this.ayudaService.cargando$.subscribe(carg => {
        this.cargando = carg;
      })
    );

    this.subs.add(
      this.ayudaService.mensajes$.subscribe(lista => {
        this.mensajes = lista;
        this.scrollAlFondo();
      })
    );
  }

  public ngOnDestroy(): void {
    this.subs.unsubscribe();
    this.ayudaService.limpiarResaltado();
  }

  @HostListener('window:resize')
  public onWindowResize(): void {
    if (!this.visible) return;
    const panelWidth = this.panelRef?.nativeElement?.offsetWidth || 380;
    const panelHeight = this.panelRef?.nativeElement?.offsetHeight || 500;
    const maxLeft = Math.max(10, window.innerWidth - panelWidth - 20);
    const maxTop = Math.max(10, window.innerHeight - panelHeight - 20);

    if (this.panelLeft > maxLeft) this.panelLeft = maxLeft;
    if (this.panelTop > maxTop) this.panelTop = maxTop;
  }

  private inicializarPosicion(): void {
    const width = 420;
    this.panelLeft = Math.max(20, window.innerWidth - width - 30);
    this.panelTop = 75;
    this.posicionadaInicialmente = true;
  }

  public iniciarArrastre(event: MouseEvent): void {
    // Requisito especial: El arrastre solo se inicia desde el icono de agarre
    event.preventDefault();
    event.stopPropagation();
    this.isDragging = true;
    this.dragStartX = event.clientX - this.panelLeft;
    this.dragStartY = event.clientY - this.panelTop;

    const onMouseMove = (e: MouseEvent) => {
      if (!this.isDragging) return;
      const panelWidth = this.panelRef?.nativeElement?.offsetWidth || 390;
      const panelHeight = this.panelRef?.nativeElement?.offsetHeight || 500;

      const maxLeft = Math.max(0, window.innerWidth - panelWidth - 10);
      const maxTop = Math.max(0, window.innerHeight - panelHeight - 10);

      this.panelLeft = Math.min(Math.max(10, e.clientX - this.dragStartX), maxLeft);
      this.panelTop = Math.min(Math.max(10, e.clientY - this.dragStartY), maxTop);
    };

    const onMouseUp = () => {
      this.isDragging = false;
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  }

  public enviarPregunta(): void {
    const texto = this.textoConsulta.trim();
    if (!texto || this.cargando) return;
    this.textoConsulta = '';
    this.ayudaService.consultar(texto, this.interfaz);
    setTimeout(() => {
      this.ajustarAlturaInput();
      this.scrollAlFondo();
    });
  }

  public usarSugerencia(sug: string): void {
    if (this.cargando) return;
    this.ayudaService.consultar(sug, this.interfaz);
    this.scrollAlFondo();
  }

  public onKeydownInput(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.enviarPregunta();
    }
  }

  public ajustarAlturaInput(): void {
    const el = this.inputPreguntaRef?.nativeElement;
    if (!el) return;
    el.style.height = 'auto';
    const maxAlto = 116;
    const scrollH = el.scrollHeight;
    el.style.height = `${Math.min(Math.max(24, scrollH), maxAlto)}px`;
    el.style.overflowY = scrollH > maxAlto ? 'auto' : 'hidden';
  }

  public cerrar(): void {
    this.ayudaService.cerrarPanel();
  }

  public toggleMinimizar(): void {
    this.ayudaService.toggleMinimizar();
  }

  public limpiarHistorial(): void {
    this.ayudaService.limpiarHistorial();
  }

  public volverAResaltar(componenteId: string): void {
    this.ayudaService.resaltarComponente(componenteId);
  }

  public limpiarTextoPaso(paso: string): string {
    if (!paso) return '';
    return paso.replace(/^(\s*(\*{1,2})?(paso\s*)?\d+[\.\)\-:]+(\*{1,2})?\s*)+/i, '').trim();
  }

  private scrollAlFondo(): void {
    setTimeout(() => {
      const el = this.mensajesContainerRef?.nativeElement;
      if (el) {
        el.scrollTop = el.scrollHeight;
      }
    }, 60);
  }
}

