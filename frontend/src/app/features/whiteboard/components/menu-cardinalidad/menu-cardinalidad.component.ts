import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CardinalidadEditando } from '../../interfaces/whiteboard-ui.interface';

@Component({
  selector: 'app-menu-cardinalidad',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './menu-cardinalidad.component.html',
  styleUrls: ['./menu-cardinalidad.component.css']
})
export class MenuCardinalidadComponent {
  @Input() public visible = false;
  @Input() public posicion: { x: number; y: number } = { x: 0, y: 0 };
  @Input() public cardinalidadEditando: CardinalidadEditando | null = null;
  @Input() public opciones: string[] = ['1', '0..1', '1..*', '0..*', '*'];

  @Output() public readonly seleccionar = new EventEmitter<string>();
  @Output() public readonly cerrar = new EventEmitter<void>();

  public cardinalidadCustom = '';

  public onSeleccionar(valor: string): void {
    this.seleccionar.emit(valor);
  }

  public onCerrar(): void {
    this.cerrar.emit();
  }

  public onInputCustom(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.cardinalidadCustom = input.value;
  }

  public onCustomSubmit(): void {
    const valor = this.cardinalidadCustom.trim();
    if (valor) {
      this.seleccionar.emit(valor);
      this.cardinalidadCustom = '';
    }
  }
}
