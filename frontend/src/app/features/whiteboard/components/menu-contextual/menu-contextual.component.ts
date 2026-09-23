import { Component, OnInit, OnDestroy, Input, Output, EventEmitter, OnChanges, SimpleChanges, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';
import { EventoContextualAccion } from '../../interfaces/whiteboard-ui.interface';
import { WhiteboardCanvasService } from '../../services/whiteboard-canvas.service';

@Component({
  selector: 'app-menu-contextual',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './menu-contextual.component.html',
  styleUrls: ['./menu-contextual.component.css']
})
export class MenuContextualComponent implements OnInit, OnDestroy, OnChanges {
  private readonly canvasService = inject(WhiteboardCanvasService, { optional: true });
  private readonly cdr           = inject(ChangeDetectorRef);
  private sub: Subscription | null = null;

  @Input() public visible = false;
  @Input() public posicion: { x: number; y: number } = { x: 0, y: 0 };
  @Input() public tipo: 'entidad' | 'relacion' = 'entidad';
  @Input() public titulo = '';

  public id: number | null = null;
  public confirmandoEliminar = false;

  @Output() public readonly propiedades = new EventEmitter<EventoContextualAccion>();
  @Output() public readonly agregarEtiqueta = new EventEmitter<EventoContextualAccion>();
  @Output() public readonly eliminar = new EventEmitter<EventoContextualAccion>();
  @Output() public readonly cancelar = new EventEmitter<void>();

  public ngOnInit(): void {
    if (!this.canvasService) return;

    this.sub = new Subscription();
    this.sub.add(
      this.canvasService.solicitudMenuContextual$.subscribe(ev => {
        this.posicion = ev.pos;
        this.tipo = ev.tipo;
        this.id = ev.id;
        this.titulo = ev.titulo;
        this.confirmandoEliminar = false;
        this.visible = true;
        this.cdr.detectChanges();
      })
    );

    this.sub.add(
      this.canvasService.cerrarModales$.subscribe(() => {
        if (this.visible) {
          this.visible = false;
          this.confirmandoEliminar = false;
          this.cdr.detectChanges();
        }
      })
    );
  }

  public ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }

  public ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && !this.visible) {
      this.confirmandoEliminar = false;
    }
  }

  public onPropiedades(): void {
    this.confirmandoEliminar = false;
    this.visible = false;
    if (this.id !== null) {
      this.propiedades.emit({ tipo: this.tipo, id: this.id });
    }
  }

  public onAgregarEtiqueta(): void {
    this.confirmandoEliminar = false;
    this.visible = false;
    if (this.id !== null) {
      this.agregarEtiqueta.emit({ tipo: this.tipo, id: this.id });
    }
  }

  public onEliminar(): void {
    if (!this.confirmandoEliminar) {
      this.confirmandoEliminar = true;
      return;
    }
    this.confirmandoEliminar = false;
    this.visible = false;
    if (this.id !== null) {
      this.eliminar.emit({ tipo: this.tipo, id: this.id });
    }
  }

  public onCancelar(): void {
    this.confirmandoEliminar = false;
    this.visible = false;
    this.cancelar.emit();
  }
}
