import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { OpcionRelacion, TipoRelacionUML } from '../../interfaces/whiteboard-ui.interface';

@Component({
  selector: 'app-menu-relacion',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './menu-relacion.component.html',
  styleUrls: ['./menu-relacion.component.css']
})
export class MenuRelacionComponent {
  @Input() public visible = false;
  @Input() public posicion: { x: number; y: number } = { x: 0, y: 0 };
  @Input() public opciones: OpcionRelacion[] = [];

  @Output() public readonly seleccionar = new EventEmitter<TipoRelacionUML>();
  @Output() public readonly cancelar = new EventEmitter<void>();

  public onSeleccionar(tipo: TipoRelacionUML): void {
    this.seleccionar.emit(tipo);
  }

  public onCancelar(): void {
    this.cancelar.emit();
  }
}
