import { Component, OnInit, OnDestroy, Input, Output, EventEmitter, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { CardinalidadEditando, EventoSeleccionCardinalidad } from '../../interfaces/whiteboard-ui.interface';
import { WhiteboardCanvasService } from '../../services/whiteboard-canvas.service';

const OPCIONES_CARDINALIDAD_DEFECTO: string[] = ['1', '0..1', '1..*', '0..*', '*'];

@Component({
  selector: 'app-menu-cardinalidad',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './menu-cardinalidad.component.html',
  styleUrls: ['./menu-cardinalidad.component.css']
})
export class MenuCardinalidadComponent implements OnInit, OnDestroy {
  private readonly canvasService = inject(WhiteboardCanvasService, { optional: true });
  private readonly cdr           = inject(ChangeDetectorRef);
  private sub: Subscription | null = null;

  @Input() public visible = false;
  @Input() public posicion: { x: number; y: number } = { x: 0, y: 0 };
  @Input() public cardinalidadEditando: CardinalidadEditando | null = null;
  @Input() public opciones: string[] = OPCIONES_CARDINALIDAD_DEFECTO;

  @Output() public readonly seleccionar = new EventEmitter<EventoSeleccionCardinalidad>();
  @Output() public readonly cerrar = new EventEmitter<void>();

  public cardinalidadCustom = '';

  public ngOnInit(): void {
    if (!this.canvasService) return;

    this.sub = new Subscription();
    this.sub.add(
      this.canvasService.solicitudCardinalidad$.subscribe(ev => {
        this.posicion = ev.pos;
        this.cardinalidadEditando = {
          relacionId: ev.relacionId,
          extremo: ev.extremo,
          valorActual: ev.valorActual
        };
        this.cardinalidadCustom = '';
        this.visible = true;
        this.cdr.detectChanges();
      })
    );

    this.sub.add(
      this.canvasService.cerrarModales$.subscribe(() => {
        if (this.visible) {
          this.visible = false;
          this.cardinalidadEditando = null;
          this.cdr.detectChanges();
        }
      })
    );
  }

  public ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }

  public onSeleccionar(valor: string): void {
    if (this.cardinalidadEditando) {
      this.seleccionar.emit({
        relacionId: this.cardinalidadEditando.relacionId,
        extremo: this.cardinalidadEditando.extremo,
        valor
      });
    }
    this.onCerrar();
  }

  public onCerrar(): void {
    this.visible = false;
    this.cardinalidadEditando = null;
    this.canvasService?.deseleccionarCapsula();
    this.cerrar.emit();
  }

  public onInputCustom(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.cardinalidadCustom = input.value;
  }

  public onCustomSubmit(): void {
    const valor = this.cardinalidadCustom.trim();
    if (valor) {
      this.onSeleccionar(valor);
      this.cardinalidadCustom = '';
    }
  }
}
