import { Component, OnInit, OnDestroy, Input, Output, EventEmitter, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { OpcionRelacion, TipoRelacionUML } from '../../interfaces/whiteboard-ui.interface';
import { WhiteboardCanvasService } from '../../services/whiteboard-canvas.service';

const OPCIONES_RELACIONES_DEFECTO: OpcionRelacion[] = [
  { tipo: 'asociacion', nombre: 'Asociación', subtitulo: 'Línea sólida continua entre tablas', svgIcon: 'asociacion' },
  { tipo: 'agregacion', nombre: 'Agregación', subtitulo: 'Contenedor débil (rombo hueco)', svgIcon: 'agregacion' },
  { tipo: 'composicion', nombre: 'Composición', subtitulo: 'Contenedor fuerte (rombo lleno)', svgIcon: 'composicion' },
  { tipo: 'herencia', nombre: 'Herencia (Generalización)', subtitulo: 'Especialización de tablas', svgIcon: 'herencia' },
  { tipo: 'clase_asociacion', nombre: 'Clase de Asociación (N:M)', subtitulo: 'Enlace principal sólido (0..* a 0..*) con clase flotante punteada', svgIcon: 'clase_asociacion' }
];

@Component({
  selector: 'app-menu-relacion',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './menu-relacion.component.html',
  styleUrls: ['./menu-relacion.component.css']
})
export class MenuRelacionComponent implements OnInit, OnDestroy {
  private readonly canvasService = inject(WhiteboardCanvasService, { optional: true });
  private readonly cdr           = inject(ChangeDetectorRef);
  private sub: Subscription | null = null;

  @Input() public visible = false;
  @Input() public posicion: { x: number; y: number } = { x: 0, y: 0 };
  @Input() public opciones: OpcionRelacion[] = OPCIONES_RELACIONES_DEFECTO;

  @Output() public readonly seleccionar = new EventEmitter<TipoRelacionUML>();
  @Output() public readonly cancelar = new EventEmitter<void>();

  public ngOnInit(): void {
    if (!this.canvasService) return;

    this.sub = new Subscription();
    this.sub.add(
      this.canvasService.solicitudRelacion$.subscribe(ev => {
        this.posicion = ev.pos;
        this.visible = true;
        this.cdr.detectChanges();
      })
    );
    this.sub.add(
      this.canvasService.cerrarModales$.subscribe(() => {
        if (this.visible) {
          this.visible = false;
          this.canvasService?.cancelarRelacionPendiente();
          this.cancelar.emit();
          this.cdr.detectChanges();
        }
      })
    );
  }

  public ngOnDestroy(): void {
    if (this.visible) {
      this.canvasService?.cancelarRelacionPendiente();
    }
    this.sub?.unsubscribe();
  }

  public onSeleccionar(tipo: TipoRelacionUML): void {
    this.visible = false;
    this.seleccionar.emit(tipo);
  }

  public onCancelar(): void {
    this.visible = false;
    this.canvasService?.cancelarRelacionPendiente();
    this.cancelar.emit();
  }
}
