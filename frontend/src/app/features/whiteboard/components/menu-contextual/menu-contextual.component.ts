import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-menu-contextual',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './menu-contextual.component.html',
  styleUrls: ['./menu-contextual.component.css']
})
export class MenuContextualComponent implements OnChanges {
  @Input() public visible = false;
  @Input() public posicion: { x: number; y: number } = { x: 0, y: 0 };
  @Input() public tipo: 'entidad' | 'relacion' = 'entidad';
  @Input() public titulo = '';

  @Output() public readonly propiedades = new EventEmitter<void>();
  @Output() public readonly agregarEtiqueta = new EventEmitter<void>();
  @Output() public readonly eliminar = new EventEmitter<void>();
  @Output() public readonly cancelar = new EventEmitter<void>();

  public confirmandoEliminar = false;

  public ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible'] && !this.visible) {
      this.confirmandoEliminar = false;
    }
  }

  public onPropiedades(): void {
    this.confirmandoEliminar = false;
    this.propiedades.emit();
  }

  public onAgregarEtiqueta(): void {
    this.confirmandoEliminar = false;
    this.agregarEtiqueta.emit();
  }

  public onEliminar(): void {
    if (!this.confirmandoEliminar) {
      this.confirmandoEliminar = true;
      return;
    }
    this.confirmandoEliminar = false;
    this.eliminar.emit();
  }

  public onCancelar(): void {
    this.confirmandoEliminar = false;
    this.cancelar.emit();
  }
}
